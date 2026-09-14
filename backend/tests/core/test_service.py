"""
Unit-тесты бизнес-логики auth.
Нет БД, нет HTTP — только чистые функции из app.core.auth.service.
"""
import uuid
from datetime import timedelta

import pytest

from app.core.auth.service import (
    create_access_token,
    create_refresh_token_raw,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_returns_bcrypt_string(self):
        hashed = hash_password("mysecret")
        assert hashed.startswith("$2b$")

    def test_bcrypt_cost_is_12(self):
        hashed = hash_password("mysecret")
        # bcrypt format: $2b$<cost>$...
        cost = int(hashed.split("$")[2])
        assert cost == 12

    def test_verify_password_correct_returns_true(self):
        hashed = hash_password("mysecret")
        assert verify_password("mysecret", hashed) is True

    def test_verify_password_wrong_returns_false(self):
        hashed = hash_password("mysecret")
        assert verify_password("wrongpassword", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        # bcrypt использует случайную соль
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


class TestAccessToken:
    def test_create_access_token_is_string(self):
        token = create_access_token(uuid.uuid4())
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_returns_correct_user_id(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)

    def test_decode_raises_on_expired_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
        with pytest.raises(Exception):
            decode_access_token(token)

    def test_decode_raises_on_garbage_token(self):
        with pytest.raises(Exception):
            decode_access_token("not.a.valid.jwt")

    def test_decode_raises_on_tampered_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(Exception):
            decode_access_token(tampered)


class TestRefreshToken:
    def test_create_refresh_token_raw_returns_string(self):
        raw = create_refresh_token_raw()
        assert isinstance(raw, str)

    def test_create_refresh_token_raw_is_long_enough(self):
        raw = create_refresh_token_raw()
        assert len(raw) >= 32

    def test_two_raw_tokens_differ(self):
        assert create_refresh_token_raw() != create_refresh_token_raw()

    def test_hash_refresh_token_is_deterministic(self):
        raw = "some_fixed_raw_token"
        assert hash_refresh_token(raw) == hash_refresh_token(raw)

    def test_hash_refresh_token_differs_from_raw(self):
        raw = create_refresh_token_raw()
        assert hash_refresh_token(raw) != raw
