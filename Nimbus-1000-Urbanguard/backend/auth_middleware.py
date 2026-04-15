"""
UrbanGuard AI System - Authentication Middleware
Handles user auth with JWT tokens.
Uses DynamoDB for storage when DYNAMODB_TABLE_USERS env var is set (AWS),
falls back to in-memory dict for local development.
"""
import hashlib
import json
import os
import time
import hmac
import base64
import logging
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "urbanguard-dev-secret-key-change-in-production")
TOKEN_EXPIRY_HOURS = 24

# Local file-based storage for dev (persists across restarts)
_USERS_FILE = os.path.join(os.path.dirname(__file__), "users_local.json")
_users_store: Dict[str, dict] = {}


def _load_users_from_file():
    global _users_store
    if os.path.exists(_USERS_FILE):
        try:
            with open(_USERS_FILE, "r") as f:
                _users_store = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load users file: {e}")
            _users_store = {}


def _save_users_to_file():
    try:
        with open(_USERS_FILE, "w") as f:
            json.dump(_users_store, f)
    except Exception as e:
        logger.warning(f"Could not save users file: {e}")


_load_users_from_file()

# DynamoDB setup (only when table name is provided)
_dynamodb_table = None

def _get_dynamo_table():
    global _dynamodb_table
    table_name = os.getenv("DYNAMODB_TABLE_USERS")
    if not table_name:
        return None
    if _dynamodb_table is None:
        import boto3
        region = os.getenv("AWS_REGION", "ap-south-2")
        dynamodb = boto3.resource("dynamodb", region_name=region)
        _dynamodb_table = dynamodb.Table(table_name)
    return _dynamodb_table


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _create_token(user_data: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload_data = {
        "email": user_data["email"],
        "role": user_data["role"],
        "exp": int(time.time()) + (TOKEN_EXPIRY_HOURS * 3600),
        "iat": int(time.time())
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
    signature = hmac.new(
        JWT_SECRET.encode(),
        f"{header}.{payload}".encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{header}.{payload}.{signature}"


def _decode_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, signature = parts
        expected_sig = hmac.new(
            JWT_SECRET.encode(),
            f"{header}.{payload}".encode(),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        payload_data = json.loads(base64.urlsafe_b64decode(payload))
        if payload_data.get("exp", 0) < time.time():
            return None
        return payload_data
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        return None


def _get_user(email: str) -> Optional[dict]:
    table = _get_dynamo_table()
    if table:
        resp = table.get_item(Key={"email": email})
        return resp.get("Item")
    return _users_store.get(email)


def _put_user(email: str, user_data: dict):
    table = _get_dynamo_table()
    if table:
        table.put_item(Item=user_data)
    else:
        _users_store[email] = user_data
        _save_users_to_file()


def signup_user(email: str, password: str, role: str = "citizen") -> dict:
    """Register a new user. Stores in DynamoDB (AWS) or in-memory (local)."""
    if _get_user(email):
        raise ValueError("Email already registered")

    if role not in ("citizen", "admin"):
        raise ValueError("Role must be 'citizen' or 'admin'")

    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")

    user_data = {
        "email": email,
        "password_hash": _hash_password(password),
        "role": role,
        "created_at": datetime.now().isoformat()
    }
    _put_user(email, user_data)

    token = _create_token(user_data)
    logger.info(f"User registered: {email} (role: {role})")
    return {"token": token, "user": {"email": email, "role": role}}


def login_user(email: str, password: str) -> dict:
    """Authenticate a user."""
    user = _get_user(email)
    if not user or user["password_hash"] != _hash_password(password):
        raise ValueError("Invalid email or password")

    token = _create_token(user)
    logger.info(f"User logged in: {email}")
    return {"token": token, "user": {"email": email, "role": user["role"]}}


def verify_token(token: str) -> Optional[dict]:
    return _decode_token(token)


def get_user_from_request(authorization: str = None) -> Optional[dict]:
    if not authorization:
        return None
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return verify_token(parts[1])


def _seed_demo_users():
    """Create demo accounts for local testing (skipped when DynamoDB is active)."""
    if _get_dynamo_table():
        return  # Don't seed in AWS
    try:
        signup_user("admin@urbanguard.ai", "admin123", "admin")
        signup_user("citizen@urbanguard.ai", "citizen123", "citizen")
        logger.info("Demo users seeded: admin@urbanguard.ai / citizen@urbanguard.ai")
    except ValueError:
        pass


_seed_demo_users()
