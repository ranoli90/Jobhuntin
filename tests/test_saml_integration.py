"""Integration tests for SAML 2.0 signature verification.

Tests the full parse_saml_response flow with:
- A self-signed certificate and properly signed SAML XML
- Rejection of unsigned/tampered responses in prod mode
- Rejection of responses signed with the wrong key
- Successful claim extraction from a valid signed response
"""

from __future__ import annotations

import base64
import datetime
import unittest
from unittest.mock import patch

import pytest

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    from lxml import etree as ET
    from signxml import XMLSigner
    from signxml.algorithms import SignatureConstructionMethod

    SIGNXML_AVAILABLE = True
except ImportError:
    SIGNXML_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not SIGNXML_AVAILABLE,
    reason="signxml not available or incompatible OpenSSL version",
)

# ---------------------------------------------------------------------------
# Test helpers: generate a self-signed cert + sign SAML XML
# ---------------------------------------------------------------------------


def _generate_self_signed_cert() -> tuple[bytes, bytes]:
    """Return (private_key_pem, certificate_pem) for a self-signed test cert."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "test-idp.example.com"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test IdP"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)
        )
        .sign(key, hashes.SHA256())
    )
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    return key_pem, cert_pem


def _build_saml_response_xml(email: str = "alice@example.com") -> str:
    """Build a minimal SAML 2.0 Response XML string (unsigned)."""
    return f"""<saml2p:Response xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol"
        xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion"
        ID="_resp_001" Version="2.0" IssueInstant="2025-01-01T00:00:00Z"
        Destination="https://api.sorce.app/sso/saml/acs">
  <saml2:Assertion ID="_assert_001" Version="2.0" IssueInstant="2025-01-01T00:00:00Z">
    <saml2:Issuer>https://idp.example.com</saml2:Issuer>
    <saml2:Subject>
      <saml2:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">{email}</saml2:NameID>
    </saml2:Subject>
    <saml2:AuthnStatement SessionIndex="_session_001">
      <saml2:AuthnContext>
        <saml2:AuthnContextClassRef>urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport</saml2:AuthnContex
tClassRef>
      </saml2:AuthnContext>
    </saml2:AuthnStatement>
    <saml2:AttributeStatement>
      <saml2:Attribute Name="firstName">
        <saml2:AttributeValue>Alice</saml2:AttributeValue>
      </saml2:Attribute>
      <saml2:Attribute Name="lastName">
        <saml2:AttributeValue>Smith</saml2:AttributeValue>
      </saml2:Attribute>
    </saml2:AttributeStatement>
  </saml2:Assertion>
</saml2p:Response>"""


def _sign_xml(xml_str: str, key_pem: bytes, cert_pem: bytes) -> bytes:
    """Sign XML with enveloped signature using signxml."""
    root = ET.fromstring(xml_str)
    signer = XMLSigner(method=SignatureConstructionMethod.enveloped)
    signed_root = signer.sign(root, key=key_pem, cert=cert_pem)
    return ET.tostring(signed_root, encoding="utf-8", xml_declaration=True)


# ---------------------------------------------------------------------------
# Mock settings for different environments
# ---------------------------------------------------------------------------

from shared.config import Environment


class _MockSettings:
    """Minimal settings mock for SAML tests.

    Uses real Environment enum members so that identity comparisons
    like ``s.env in (Environment.PROD, Environment.STAGING)`` work
    correctly in the code under test.
    """

    def __init__(self, env: Environment = Environment.LOCAL):
        self.env = env
        self.sso_session_secret = "test-secret-for-hmac"
        self.sso_sp_entity_id = "https://api.sorce.app/sso"
        self.sso_sp_acs_url = "https://api.sorce.app/sso/saml/acs"


class _MockProdSettings(_MockSettings):
    def __init__(self):
        super().__init__(Environment.PROD)


class _MockLocalSettings(_MockSettings):
    def __init__(self):
        super().__init__(Environment.LOCAL)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSAMLSignatureVerification(unittest.TestCase):
    """End-to-end tests for parse_saml_response with real XML signatures."""

    @classmethod
    def setUpClass(cls):
        cls.key_pem, cls.cert_pem = _generate_self_signed_cert()
        cls.cert_str = cls.cert_pem.decode("utf-8")
        # Also generate a second keypair (wrong key)
        cls.wrong_key_pem, cls.wrong_cert_pem = _generate_self_signed_cert()
        cls.wrong_cert_str = cls.wrong_cert_pem.decode("utf-8")

    def _signed_b64(self, email: str = "alice@example.com") -> str:
        """Return a base64-encoded signed SAML response."""
        xml_str = _build_saml_response_xml(email)
        signed_bytes = _sign_xml(xml_str, self.key_pem, self.cert_pem)
        return base64.b64encode(signed_bytes).decode("utf-8")

    def _unsigned_b64(self, email: str = "alice@example.com") -> str:
        """Return a base64-encoded unsigned SAML response."""
        xml_str = _build_saml_response_xml(email)
        return base64.b64encode(xml_str.encode("utf-8")).decode("utf-8")

    @patch("backend.sso.saml.get_settings", return_value=_MockLocalSettings())
    def test_valid_signed_response_extracts_claims(self, _mock):
        """A properly signed SAML response should return extracted claims."""
        from backend.sso.saml import parse_saml_response

        result = parse_saml_response(self._signed_b64(), self.cert_str)

        self.assertIsNotNone(result)
        self.assertEqual(result["email"], "alice@example.com")
        self.assertEqual(result["name_id"], "alice@example.com")
        self.assertEqual(result["first_name"], "Alice")
        self.assertEqual(result["last_name"], "Smith")
        self.assertEqual(result["session_index"], "_session_001")

    @patch("backend.sso.saml.get_settings", return_value=_MockLocalSettings())
    def test_wrong_cert_rejects_response(self, _mock):
        """A response verified against the wrong certificate should be rejected."""
        from backend.sso.saml import parse_saml_response

        result = parse_saml_response(self._signed_b64(), self.wrong_cert_str)

        self.assertIsNone(
            result, "Should reject when certificate doesn't match signing key"
        )

    @patch("backend.sso.saml.get_settings", return_value=_MockProdSettings())
    def test_no_cert_in_prod_rejects(self, _mock):
        """In prod, missing certificate should reject the response (fail-closed)."""
        from backend.sso.saml import parse_saml_response

        result = parse_saml_response(self._unsigned_b64(), "")

        self.assertIsNone(
            result, "Should reject unsigned response in prod when no cert configured"
        )

    @patch("backend.sso.saml.get_settings", return_value=_MockLocalSettings())
    def test_no_cert_in_local_allows_unsigned(self, _mock):
        """In local dev, missing certificate should allow unsigned responses (for development)."""
        from backend.sso.saml import parse_saml_response

        result = parse_saml_response(self._unsigned_b64(), "")

        self.assertIsNotNone(result, "Should allow unsigned response in local dev")
        self.assertEqual(result["email"], "alice@example.com")

    @patch("backend.sso.saml.get_settings", return_value=_MockLocalSettings())
    def test_tampered_response_rejected(self, _mock):
        """A signed response with tampered content should be rejected."""
        from backend.sso.saml import parse_saml_response

        # Sign with alice, then tamper the base64 to change the email
        signed_b64 = self._signed_b64("alice@example.com")
        signed_bytes = base64.b64decode(signed_b64)
        tampered = signed_bytes.replace(b"alice@example.com", b"evil@attacker.com")
        tampered_b64 = base64.b64encode(tampered).decode("utf-8")

        result = parse_saml_response(tampered_b64, self.cert_str)

        self.assertIsNone(result, "Should reject tampered signed response")

    @patch("backend.sso.saml.get_settings", return_value=_MockLocalSettings())
    def test_invalid_base64_returns_none(self, _mock):
        """Invalid base64 input should return None gracefully."""
        from backend.sso.saml import parse_saml_response

        result = parse_saml_response("not-valid-base64!!!", self.cert_str)

        self.assertIsNone(result)

    @patch("backend.sso.saml.get_settings", return_value=_MockLocalSettings())
    def test_missing_nameid_returns_none(self, _mock):
        """A response with no NameID element should return None."""
        from backend.sso.saml import parse_saml_response

        xml_no_nameid = """<saml2p:Response xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol"
            xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion"
            ID="_resp_002" Version="2.0" IssueInstant="2025-01-01T00:00:00Z">
          <saml2:Assertion ID="_assert_002" Version="2.0" IssueInstant="2025-01-01T00:00:00Z">
            <saml2:Issuer>https://idp.example.com</saml2:Issuer>
            <saml2:Subject></saml2:Subject>
          </saml2:Assertion>
        </saml2p:Response>"""
        b64 = base64.b64encode(xml_no_nameid.encode()).decode()

        result = parse_saml_response(b64, "")

        self.assertIsNone(result)


class TestSSOSessionToken(unittest.TestCase):
    """Tests for SSO session token creation and verification."""

    @patch("backend.sso.saml.get_settings", return_value=_MockLocalSettings())
    def test_create_and_verify_roundtrip(self, _mock):
        """A freshly created token should verify successfully."""
        from backend.sso.saml import create_sso_session_token, verify_sso_session_token

        token = create_sso_session_token("tenant-1", "alice@example.com", "user-1")
        result = verify_sso_session_token(token)

        self.assertIsNotNone(result)
        self.assertEqual(result["tenant_id"], "tenant-1")
        self.assertEqual(result["email"], "alice@example.com")
        self.assertEqual(result["user_id"], "user-1")

    @patch("backend.sso.saml.get_settings", return_value=_MockLocalSettings())
    def test_tampered_token_rejected(self, _mock):
        """A tampered token should fail verification."""
        from backend.sso.saml import create_sso_session_token, verify_sso_session_token

        token = create_sso_session_token("tenant-1", "alice@example.com", "user-1")
        # Tamper with the payload portion
        parts = token.split(".")
        parts[0] = parts[0][:5] + "TAMPERED" + parts[0][5:]
        tampered = ".".join(parts)

        result = verify_sso_session_token(tampered)

        self.assertIsNone(result, "Tampered token should be rejected")

    @patch("backend.sso.saml.get_settings", return_value=_MockProdSettings())
    def test_empty_secret_in_prod_raises(self, _mock):
        """Creating a token with empty secret in prod should raise RuntimeError."""
        # Override the mock to have empty secret
        _mock.return_value.sso_session_secret = ""
        from backend.sso.saml import create_sso_session_token

        with self.assertRaises(RuntimeError):
            create_sso_session_token("tenant-1", "alice@example.com", "user-1")


if __name__ == "__main__":
    unittest.main()
