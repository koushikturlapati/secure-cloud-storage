import os
from datetime import datetime, timedelta, timezone
from unittest import TestCase

import bcrypt
import jwt
from fastapi.testclient import TestClient

# The database engine is configured during the API import.  These values only
# allow that configuration to be constructed; all endpoint tests use FakeDB.
os.environ.setdefault("SECRET_KEY", "test-signing-key-that-is-at-least-32-bytes")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "test")

from api import main as auth  # noqa: E402


class TestUser:
    id = 1
    username = "alice"
    password_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode("utf-8")


class FakeQuery:
    def __init__(self, user):
        self.user = user

    def filter(self, *_args):
        return self

    def first(self):
        return self.user


class FakeDB:
    def __init__(self):
        self.user = TestUser()

    def query(self, _model):
        return FakeQuery(self.user)


def override_get_db():
    yield FakeDB()


class AuthenticationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        auth.app.dependency_overrides[auth.get_db] = override_get_db
        cls.client = TestClient(auth.app)

    @classmethod
    def tearDownClass(cls):
        auth.app.dependency_overrides.clear()

    def test_json_login_returns_a_signed_bearer_token(self):
        response = self.client.post(
            "/login", json={"username": "alice", "password": "correct-password"}
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["token_type"], "bearer")
        self.assertEqual(
            jwt.decode(body["access_token"], auth.SECRET_KEY, algorithms=[auth.ALGORITHM])["sub"],
            "alice",
        )

    def test_root_serves_the_login_page(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("<h3 style=\"text-align: center;\">Login</h3>", response.text)

    def test_oauth_token_and_protected_endpoint(self):
        token_response = self.client.post(
            "/token", data={"username": "alice", "password": "correct-password"}
        )

        self.assertEqual(token_response.status_code, 200)
        token = token_response.json()["access_token"]
        response = self.client.get("/me", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": 1, "username": "alice"})

    def test_invalid_and_expired_tokens_are_rejected(self):
        invalid_login = self.client.post(
            "/login", json={"username": "alice", "password": "wrong-password"}
        )
        self.assertEqual(invalid_login.status_code, 401)

        expired_token = jwt.encode(
            {"sub": "alice", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            auth.SECRET_KEY,
            algorithm=auth.ALGORITHM,
        )
        expired_response = self.client.get(
            "/me", headers={"Authorization": f"Bearer {expired_token}"}
        )
        self.assertEqual(expired_response.status_code, 401)
        self.assertEqual(expired_response.json()["detail"], "Token has expired")
