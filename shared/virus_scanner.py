"""Virus Scanner Module for File Security.

Provides comprehensive virus scanning for uploaded files using multiple
scanning engines and fallback mechanisms with retry logic.
"""

from __future__ import annotations

import hashlib
import subprocess
import tempfile

from shared.logging_config import get_logger
from shared.retry_utils import RetryConfigs, retry_sync

logger = get_logger("sorce.virus_scanner")


class VirusScanResult:
    """Result of virus scan."""

    def __init__(self, clean: bool, threats: list[str] = None, engine: str = "unknown"):
        self.clean = clean
        self.threats = threats or []
        self.engine = engine
        self.scan_time = None


class ClamAVScanner:
    """ClamAV virus scanner implementation."""

    def __init__(self):
        self.available = self._check_clamav_available()

    @retry_sync(RetryConfigs.FILE_OPERATIONS, "ClamAV scan")
    def _check_clamav_available(self) -> bool:
        """Check if ClamAV is available with retry logic."""
        try:
            result = subprocess.run(
                ["clamscan", "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @retry_sync(RetryConfigs.FILE_OPERATIONS, "ClamAV scan")
    def _run_clamav_scan(self, file_path: str) -> subprocess.CompletedProcess:
        """Run ClamAV scan with retry logic."""
        return subprocess.run(
            ["clamscan", "--no-summary", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

    async def scan_file(self, file_path: str) -> VirusScanResult:
        """Scan file using ClamAV."""
        if not self.available:
            logger.warning("ClamAV not available, skipping scan")
            return VirusScanResult(clean=True, engine="clamav-unavailable")

        try:
            result = self._run_clamav_scan(file_path)

            if result.returncode == 0:
                return VirusScanResult(clean=True, engine="clamav")
            else:
                # Parse ClamAV output for threats
                threats = []
                output_lines = result.stdout.split("\n")
                for line in output_lines:
                    if "FOUND" in line:
                        threat = line.split("FOUND")[0].strip()
                        threats.append(threat)

                return VirusScanResult(clean=False, threats=threats, engine="clamav")

        except subprocess.TimeoutExpired:
            logger.error("ClamAV scan timed out")
            return VirusScanResult(
                clean=False, threats=["scan_timeout"], engine="clamav"
            )
        except Exception as e:
            logger.error(f"ClamAV scan failed: {e}")
            return VirusScanResult(clean=False, threats=["scan_error"], engine="clamav")


class HeuristicScanner:
    """Heuristic scanner for common malware patterns."""

    def __init__(self):
        self.malicious_patterns = [
            b"eval(",
            b"javascript:",
            b"vbscript:",
            b"<script",
            b"powershell",
            b"cmd.exe",
            b"shell_exec",
            b"base64_decode",
            b"exec(",
            b"system(",
            b"passthru(",
            b"shell_exec(",
        ]

        self.suspicious_extensions = [
            ".exe",
            ".bat",
            ".cmd",
            ".com",
            ".scr",
            ".pif",
            ".vbs",
            ".js",
            ".jar",
            ".app",
            ".deb",
            ".rpm",
            ".dmg",
            ".pkg",
            ".msi",
            ".torrent",
        ]

    async def scan_file(self, file_path: str, filename: str) -> VirusScanResult:
        """Scan file using heuristic analysis."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()

            threats = []

            # Check for malicious patterns
            for pattern in self.malicious_patterns:
                if pattern in content.lower():
                    threats.append(
                        f"malicious_pattern_{pattern.decode('ascii', errors='ignore')}"
                    )

            # Check filename
            filename_lower = filename.lower()
            for ext in self.suspicious_extensions:
                if filename_lower.endswith(ext):
                    threats.append(f"suspicious_extension_{ext}")

            # Check for embedded executables
            if content.startswith(b"MZ"):  # PE header
                threats.append("embedded_executable")

            # Check for common malware signatures
            malware_signatures = [
                b"X5O!P%@AP[4",
                b"JFIF",  # JPEG header in non-image files
                b"\x89PNG",  # PNG header in non-image files
            ]

            for signature in malware_signatures:
                if signature in content[:100]:  # Check first 100 bytes
                    threats.append("malware_signature_detected")

            is_clean = len(threats) == 0
            return VirusScanResult(clean=is_clean, threats=threats, engine="heuristic")

        except Exception as e:
            logger.error(f"Heuristic scan failed: {e}")
            return VirusScanResult(
                clean=False, threats=["scan_error"], engine="heuristic"
            )


class VirusScanner:
    """Main virus scanner that coordinates multiple scanning engines."""

    def __init__(self):
        self.clamav = ClamAVScanner()
        self.heuristic = HeuristicScanner()

    async def scan_bytes(self, file_bytes: bytes, filename: str) -> VirusScanResult:
        """Scan file bytes using multiple engines."""
        # Create temporary file for scanning
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_bytes)
            temp_file.flush()

            # Run scans in parallel
            import asyncio

            clamav_result, heuristic_result = await asyncio.gather(
                self.clamav.scan_file(temp_file.name),
                self.heuristic.scan_file(temp_file.name, filename),
                return_exceptions=True,
            )

            # Clean up temporary file
            import os

            try:
                os.unlink(temp_file.name)
            except OSError:
                pass

            # Combine results
            all_threats = []
            is_clean = True
            engines_used = []

            for result in [clamav_result, heuristic_result]:
                if result is None:
                    continue

                engines_used.append(result.engine)
                if not result.clean:
                    is_clean = False
                    all_threats.extend(result.threats)

            # Remove duplicate threats
            unique_threats = list(set(all_threats))

            return VirusScanResult(
                clean=is_clean, threats=unique_threats, engine="+".join(engines_used)
            )

    async def scan_file_path(self, file_path: str) -> VirusScanResult:
        """Scan file at given path using multiple engines."""
        filename = file_path.split("/")[-1]  # Extract filename

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        return await self.scan_bytes(file_bytes, filename)


# Global scanner instance
_virus_scanner = None


def get_virus_scanner() -> VirusScanner:
    """Get or create global virus scanner instance."""
    global _virus_scanner
    if _virus_scanner is None:
        _virus_scanner = VirusScanner()
    return _virus_scanner


async def scan_uploaded_file(file_bytes: bytes, filename: str) -> VirusScanResult:
    """Convenience function to scan uploaded file."""
    scanner = get_virus_scanner()
    result = await scanner.scan_bytes(file_bytes, filename)

    # Log scan results
    if result.clean:
        logger.info(f"File scan passed: {filename}")
    else:
        logger.warning(
            f"File scan failed: {filename}, threats: {result.threats}, engine: {result.engine}"
        )

    return result


def generate_file_hash(file_bytes: bytes) -> str:
    """Generate SHA-256 hash of file for tracking."""
    return hashlib.sha256(file_bytes).hexdigest()


def is_file_type_allowed(filename: str, content_type: str) -> bool:
    """Check if file type is allowed for scanning."""
    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/csv",
    ]

    # Check content type
    if content_type not in allowed_types:
        return False

    # Check filename extension
    filename_lower = filename.lower()
    allowed_extensions = [".pdf", ".doc", ".docx", ".txt", ".csv"]
    if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
        return False

    return True
