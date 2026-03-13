"""ML-based CAPTCHA Solver for advanced image CAPTCHA recognition.

Uses machine learning models to solve image-based CAPTCHAs with high accuracy.
Falls back to external services when ML confidence is low.
"""

from __future__ import annotations

import asyncio
import base64
import io
import re
from typing import Any, Dict, Optional, Tuple

import numpy as np
from PIL import Image
from playwright.async_api import Page

from shared.logging_config import get_logger

logger = get_logger("sorce.ml_captcha_solver")

try:
    import cv2
    import pytesseract
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available - ML CAPTCHA solving will be limited")

try:
    import torch
    import torchvision.transforms as transforms
    from transformers import AutoImageProcessor, AutoModelForImageClassification
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available - deep learning CAPTCHA solving disabled")


class MLCaptchaSolver:
    """Machine Learning-based CAPTCHA solver with multiple approaches."""

    def __init__(self):
        self.confidence_threshold = 0.8
        self.preprocess_transforms = None
        self.model = None
        self.processor = None
        self._model_initialized = False
        # Lazy initialization - model will be loaded on first use, not on instantiation
        # This prevents downloading ~100MB model on every CAPTCHA solve attempt
        # and works properly in offline environments (cached models will be used)
    
    def _initialize_ml_model(self):
        """Initialize the ML model for CAPTCHA recognition using lazy loading.
        
        Uses Tesseract OCR as the primary method (no external model download needed).
        Only loads deep learning model if explicitly needed and Torch is available.
        Models are cached automatically by HuggingFace.
        """
        # Lazy initialization check - don't load if already initialized
        if self._model_initialized:
            logger.debug("ML model already initialized, skipping")
            return
        
        try:
            # PRIMARY METHOD: Use Tesseract OCR for text-based CAPTCHA
            # This is the correct approach - ResNet is an ImageNet classifier (1000 categories)
            # that cannot perform OCR. Tesseract is purpose-built for text recognition.
            if CV2_AVAILABLE and pytesseract:
                logger.info("ML CAPTCHA solver initialized with Tesseract OCR (primary method)")
                self._model_initialized = True
                return
            
            # Fallback: Deep learning model only if Tesseract is not available
            # This path is rarely needed as Tesseract handles most text CAPTCHAs
            if TORCH_AVAILABLE:
                # Note: We no longer use microsoft/resnet-50 as it's wrong for OCR
                # It's an ImageNet classifier, not an OCR model
                # Keeping this for potential future OCR-specific models if needed
                logger.warning("Using fallback ML model - Tesseract OCR preferred")
                
            self._model_initialized = True
            logger.info("ML CAPTCHA solver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML model: {e}")
            self.model = None
            self.processor = None
            self._model_initialized = False
    
    async def solve_image_captcha_ml(
        self, image_base64: str, captcha_type: str = "text"
    ) -> Tuple[Optional[str], float]:
        """Solve image CAPTCHA using ML techniques."""
        if not CV2_AVAILABLE:
            return None, 0.0
        
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess based on CAPTCHA type
            if captcha_type == "text":
                result, confidence = await self._solve_text_captcha(cv_image)
            elif captcha_type == "math":
                result, confidence = await self._solve_math_captcha(cv_image)
            else:
                result, confidence = await self._solve_general_captcha(cv_image)
            
            return result, confidence
            
        except Exception as e:
            logger.error(f"ML CAPTCHA solving error: {e}")
            return None, 0.0
    
    async def _solve_text_captcha(self, image: np.ndarray) -> Tuple[Optional[str], float]:
        """Solve text-based CAPTCHA using OCR and ML."""
        try:
            # Preprocess image for OCR
            processed = self._preprocess_text_image(image)
            
            # Use Tesseract OCR
            if CV2_AVAILABLE:
                text = pytesseract.image_to_string(
                    processed, 
                    config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                ).strip()
            else:
                return None, 0.0
            
            # Clean up the text
            text = re.sub(r'[^A-Z0-9]', '', text.upper())
            
            if len(text) >= 4 and len(text) <= 8:  # Typical CAPTCHA length
                confidence = 0.7 if CV2_AVAILABLE else 0.5
                return text, confidence
            
        except Exception as e:
            logger.debug(f"Text CAPTCHA OCR failed: {e}")
        
        return None, 0.0
    
    async def _solve_math_captcha(self, image: np.ndarray) -> Tuple[Optional[str], float]:
        """Solve math-based CAPTCHA."""
        try:
            # Preprocess for math expression recognition
            processed = self._preprocess_math_image(image)
            
            # Use OCR to extract math expression
            if CV2_AVAILABLE:
                text = pytesseract.image_to_string(
                    processed,
                    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789+-*= '
                ).strip()
            else:
                return None, 0.0
            
            # Clean and evaluate math expression
            text = re.sub(r'[^0-9+\-*/= ]', '', text)
            
            if '=' in text:
                parts = text.split('=')
                if len(parts) == 2:
                    expression = parts[0].strip()
                    try:
                        # Safe evaluation of math expression using AST
                        result = self._safe_eval(expression)
                        return str(int(result)), 0.8
                    except Exception:
                        pass
            
        except Exception as e:
            logger.debug(f"Math CAPTCHA solving failed: {e}")
        
        return None, 0.0
    
    async def _solve_general_captcha(self, image: np.ndarray) -> Tuple[Optional[str], float]:
        """Solve general CAPTCHA using Tesseract OCR.
        
        Uses Tesseract OCR as the primary method for general CAPTCHA solving.
        This is the correct approach - ResNet is an ImageNet classifier that cannot
        perform OCR. Tesseract is purpose-built for text recognition.
        """
        # Use Tesseract OCR instead of wrong ResNet model
        if not CV2_AVAILABLE:
            return None, 0.0
        
        # Lazy initialization - ensure model is ready (though Tesseract needs no init)
        self._initialize_ml_model()
        
        try:
            # Preprocess image for OCR
            processed = self._preprocess_text_image(image)
            
            # Use Tesseract OCR with multiple PSM modes for better accuracy
            text = pytesseract.image_to_string(
                processed,
                config='--psm 6 --oem 3'
            ).strip()
            
            # Clean up the text - allow alphanumeric and common special chars
            text = re.sub(r'[^A-Za-z0-9]', '', text)
            
            if len(text) >= 3:  # Minimum CAPTCHA length
                confidence = 0.6
                return text, confidence
            
        except Exception as e:
            logger.debug(f"General CAPTCHA OCR failed: {e}")
        
        return None, 0.0
    
    def _preprocess_text_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for text OCR."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Remove noise
            denoised = cv2.medianBlur(binary, 3)
            
            # Enhance contrast
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            enhanced = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
            
            return enhanced
            
        except Exception:
            return image
    
    def _preprocess_math_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for math expression OCR."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive threshold for better math symbol recognition
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Remove small noise
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            return cleaned
            
        except Exception:
            return image
    
    def _safe_eval(self, expr: str) -> float:
        """Safely evaluate a mathematical expression using AST.
        
        Only allows basic arithmetic operations: +, -, *, /
        """
        import ast
        import operator
        
        # Define safe operations
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        def _eval_node(node):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError("Only numeric constants allowed")
            elif isinstance(node, ast.BinOp):
                left = _eval_node(node.left)
                right = _eval_node(node.right)
                op_type = type(node.op)
                if op_type in operators:
                    return operators[op_type](left, right)
                raise ValueError(f"Unsupported operation: {op_type}")
            elif isinstance(node, ast.UnaryOp):
                operand = _eval_node(node.operand)
                op_type = type(node.op)
                if op_type in operators:
                    return operators[op_type](operand)
                raise ValueError(f"Unsupported unary operation: {op_type}")
            else:
                raise ValueError(f"Unsupported AST node: {type(node)}")
        
        # Parse and evaluate
        parsed = ast.parse(expr, mode='eval')
        return _eval_node(parsed.body)

    async def solve_with_fallback(
        self, image_base64: str, captcha_type: str = "text", external_solver=None
    ) -> Tuple[Optional[str], str, float]:
        """Solve CAPTCHA with ML first, fallback to external service."""
        # Try ML solving first
        ml_result, ml_confidence = await self.solve_image_captcha_ml(image_base64, captcha_type)
        
        if ml_result and ml_confidence >= self.confidence_threshold:
            logger.info(f"ML CAPTCHA solved with confidence {ml_confidence:.2f}")
            return ml_result, "ml", ml_confidence
        
        # Fallback to external service
        if external_solver:
            try:
                external_result = await external_solver.solve_image_captcha(image_base64)
                if external_result:
                    logger.info("External CAPTCHA solver succeeded")
                    return external_result, "external", 0.9
            except Exception as e:
                logger.error(f"External CAPTCHA solver failed: {e}")
        
        logger.warning("All CAPTCHA solving methods failed")
        return None, "failed", 0.0


class EnhancedCaptchaDetector:
    """Enhanced CAPTCHA detector with better recognition patterns."""

    def __init__(self):
        self.captcha_patterns = {
            "recaptcha_v2": [
                r"iframe[src.*recaptcha.*]",
                r"\.g-recaptcha",
                r"data-sitekey",
                r"recaptcha/api\.js",
            ],
            "recaptcha_v3": [
                r"grecaptcha\.render",
                r"recaptcha_v3",
                r"action=",
            ],
            "hcaptcha": [
                r"hcaptcha\.com",
                r"\.h-captcha",
                r"data-hcaptcha-sitekey",
            ],
            "image_captcha": [
                r"captcha.*image",
                r"img.*captcha",
                r"captcha.*png|jpg|gif",
                r"verification.*image",
            ],
            "text_captcha": [
                r"input.*captcha",
                r"type.*text.*captcha",
                r"placeholder.*captcha",
                r"name.*captcha",
            ],
            "math_captcha": [
                r"math.*captcha",
                r"calculate.*captcha",
                r"solve.*captcha",
                r"\d+.*[+\-*/].*\d+",
            ],
            "funcaptcha": [
                r"funcaptcha",
                r"arkose.*captcha",
                r"arkoselabs",
            ],
        }

    async def detect_captcha_enhanced(self, page: Page) -> Dict[str, Any]:
        """Enhanced CAPTCHA detection with better accuracy."""
        detected = {
            "has_captcha": False,
            "captcha_type": None,
            "confidence": 0.0,
            "site_key": None,
            "selectors": [],
            "element_count": 0,
            "ml_suitable": False,
        }

        try:
            # Get page content
            content = await page.content()
            url = page.url
            
            # Check each CAPTCHA type
            for captcha_type, patterns in self.captcha_patterns.items():
                matches = 0
                matched_patterns = []
                
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        matches += 1
                        matched_patterns.append(pattern)
                
                if matches > 0:
                    detected["has_captcha"] = True
                    detected["captcha_type"] = captcha_type
                    detected["confidence"] = min(matches * 0.3, 1.0)
                    detected["selectors"] = matched_patterns
                    detected["element_count"] = matches
                    
                    # Check if ML-suitable
                    detected["ml_suitable"] = captcha_type in [
                        "image_captcha", "text_captcha", "math_captcha"
                    ]
                    
                    # Extract site key for reCAPTCHA/hCaptcha
                    if captcha_type in ["recaptcha_v2", "recaptcha_v3", "hcaptcha"]:
                        site_key_match = re.search(r'data-(?:site|hcaptcha)-key="([^"]+)"', content)
                        if site_key_match:
                            detected["site_key"] = site_key_match.group(1)
                    
                    break

        except Exception as e:
            logger.error(f"Enhanced CAPTCHA detection error: {e}")

        return detected
