import pytest

from app.core.encryption import decrypt_value, encrypt_value
from app.core.exceptions import (
    AuthenticationException,
    NotFoundException,
    RateLimitException,
    ValidationException,
)
from app.core.rate_limiter import InMemoryRateLimiter
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestSecurity:
    def test_hash_password(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_verify_wrong_password(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_create_and_decode_token(self):
        token = create_access_token({"sub": "test_user", "role": "admin"})
        payload = decode_access_token(token)
        assert payload["sub"] == "test_user"
        assert payload["role"] == "admin"

    def test_decode_invalid_token(self):
        with pytest.raises(AuthenticationException):
            decode_access_token("invalid.token.here")


class TestEncryption:
    def test_encrypt_decrypt(self):
        plaintext = "super_secret_api_key_12345"
        encrypted = encrypt_value(plaintext)
        assert encrypted != plaintext
        decrypted = decrypt_value(encrypted)
        assert decrypted == plaintext

    def test_encrypt_different_each_time(self):
        text = "same_text"
        enc1 = encrypt_value(text)
        enc2 = encrypt_value(text)
        assert enc1 != enc2
        assert decrypt_value(enc1) == text
        assert decrypt_value(enc2) == text


class TestRateLimiter:
    def test_allows_requests(self):
        limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            limiter.check("test_key")

    def test_blocks_over_limit(self):
        limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)
        limiter.check("test_key")
        limiter.check("test_key")
        limiter.check("test_key")
        with pytest.raises(RateLimitException):
            limiter.check("test_key")

    def test_get_remaining(self):
        limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60)
        limiter.check("test_key")
        remaining = limiter.get_remaining("test_key")
        assert remaining == 4


class TestExceptions:
    def test_not_found_exception(self):
        exc = NotFoundException("User", "123")
        assert "123" in exc.message
        assert exc.code == "NOT_FOUND"

    def test_validation_exception(self):
        exc = ValidationException("Invalid input")
        assert exc.code == "VALIDATION_ERROR"
