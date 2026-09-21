import base64
import os
import time
import unittest
from unittest.mock import patch

from jose import jwt

from services import auth


def _base64url(value: int) -> str:
    byte_length = (value.bit_length() + 7) // 8
    encoded = value.to_bytes(byte_length, "big")
    return base64.urlsafe_b64encode(encoded).rstrip(b"=").decode("ascii")


class CognitoAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.private_pem = cls.private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        public_numbers = cls.private_key.public_key().public_numbers()
        cls.jwks = {
            "keys": [{
                "kty": "RSA",
                "n": _base64url(public_numbers.n),
                "e": _base64url(public_numbers.e),
                "alg": "RS256",
                "use": "sig",
                "kid": "test-key",
            }]
        }

    def setUp(self) -> None:
        self.environment = patch.dict(
            os.environ,
            {
                "AWS_REGION": "ap-south-1",
                "COGNITO_USER_POOL_ID": "pool-id",
                "COGNITO_CLIENT_ID": "client-id",
            },
            clear=False,
        )
        self.environment.start()
        auth._jwks.cache_clear()

    def tearDown(self) -> None:
        self.environment.stop()

    def token(self, **claims: object) -> str:
        now = int(time.time())
        payload = {
            "iss": "https://cognito-idp.ap-south-1.amazonaws.com/pool-id",
            "iat": now,
            "exp": now + 300,
            "sub": "user-id",
            "token_use": "access",
            "client_id": "client-id",
            **claims,
        }
        return jwt.encode(payload, self.private_pem, algorithm="RS256", headers={"kid": "test-key"})

    def assert_valid(self, token: str) -> None:
        with patch.object(auth, "_jwks", return_value=self.jwks):
            claims = auth.require_authenticated_user(f"Bearer {token}")
        self.assertEqual(claims["sub"], "user-id")

    def test_valid_access_token_uses_client_id(self) -> None:
        self.assert_valid(self.token())

    def test_valid_id_token_uses_audience(self) -> None:
        self.assert_valid(self.token(token_use="id", aud="client-id"))

    def test_wrong_access_client_id_is_rejected(self) -> None:
        with self.assertRaises(auth.HTTPException):
            self.assert_valid(self.token(client_id="other-client"))

    def test_wrong_id_audience_is_rejected(self) -> None:
        with self.assertRaises(auth.HTTPException):
            self.assert_valid(self.token(token_use="id", aud="other-client"))

    def test_wrong_issuer_is_rejected(self) -> None:
        with self.assertRaises(auth.HTTPException):
            self.assert_valid(self.token(iss="https://example.invalid/pool-id"))

    def test_wrong_token_use_is_rejected(self) -> None:
        with self.assertRaises(auth.HTTPException):
            self.assert_valid(self.token(token_use="refresh"))

    def test_expired_token_is_rejected(self) -> None:
        with self.assertRaises(auth.HTTPException):
            self.assert_valid(self.token(exp=int(time.time()) - 1))


if __name__ == "__main__":
    unittest.main()