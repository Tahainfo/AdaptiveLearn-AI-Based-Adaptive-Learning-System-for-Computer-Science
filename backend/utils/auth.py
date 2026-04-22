"""
Authentication utilities
"""
import bcrypt
import secrets
import time


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def generate_token() -> str:
    """Generate a random auth token"""
    return secrets.token_urlsafe(32)


class TokenStore:
    """Simple in-memory token store"""
    _tokens = {}

    @classmethod
    def create_token(cls, student_id: int) -> str:
        """Create a new token for a student"""
        token = generate_token()
        cls._tokens[token] = {
            'student_id': student_id,
            'created_at': time.time(),
            'expires_at': time.time() + (24 * 60 * 60)  # 24 hours
        }
        return token

    @classmethod
    def verify_token(cls, token: str) -> int:
        """Verify token and return student_id, or None if invalid"""
        if token not in cls._tokens:
            return None

        token_data = cls._tokens[token]

        if time.time() > token_data['expires_at']:
            del cls._tokens[token]
            return None

        return token_data['student_id']

    @classmethod
    def invalidate_token(cls, token: str):
        """Invalidate a token"""
        if token in cls._tokens:
            del cls._tokens[token]
