"""JWT token handling and validation"""

import jwt
from functools import wraps
from typing import Optional, Dict, Tuple
from flask import request, jsonify
from leaf_api.auth.roles import DEFAULT_ROLE, ROLES


class JWTHandler:
    """Handles JWT validation and decoding"""

    def __init__(self, public_key_path: str = None, private_key_path: str = None):
        self.public_key_path = public_key_path
        self.private_key_path = private_key_path
        self._public_key = None
        self._private_key = None

    @property
    def public_key(self) -> str:
        """Load and cache public key"""
        if not self._public_key and self.public_key_path:
            try:
                with open(self.public_key_path, "r") as f:
                    self._public_key = f.read()
            except FileNotFoundError:
                raise RuntimeError(f"Public key not found at {self.public_key_path}")
        return self._public_key

    @property
    def private_key(self) -> str:
        """Load and cache private key"""
        if not self._private_key and self.private_key_path:
            try:
                with open(self.private_key_path, "r") as f:
                    self._private_key = f.read()
            except FileNotFoundError:
                raise RuntimeError(f"Private key not found at {self.private_key_path}")
        return self._private_key

    def validate_jwt(self, token: str) -> Optional[Dict]:
        """
        Validates Ed25519 JWT token and returns claims
        Returns None if invalid
        """
        if not token:
            return None

        try:
            claims = jwt.decode(
                token,
                self.public_key,
                algorithms=["EdDSA"],
            )
            return claims
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def extract_jwt_from_header(self, headers: Dict) -> Optional[str]:
        """Extract JWT token from Authorization header"""
        auth_header = headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        return auth_header[7:]

    def get_user_role(self, claims: Dict) -> str:
        """Extract role from JWT claims"""
        role = claims.get("role", DEFAULT_ROLE)
        if role not in ROLES:
            return DEFAULT_ROLE
        return role

    def get_user_context(self, token: Optional[str] = None) -> Dict:
        """
        Returns user context including role and permissions
        If no token provided, returns public context
        """
        if not token:
            return {
                "role": DEFAULT_ROLE,
                "permissions": ROLES[DEFAULT_ROLE]["permissions"],
                "user_id": None,
                "authenticated": False,
            }

        claims = self.validate_jwt(token)
        if not claims:
            return {
                "role": DEFAULT_ROLE,
                "permissions": ROLES[DEFAULT_ROLE]["permissions"],
                "user_id": None,
                "authenticated": False,
            }

        role = self.get_user_role(claims)
        return {
            "role": role,
            "permissions": ROLES[role]["permissions"],
            "user_id": claims.get("sub"),
            "authenticated": True,
            "claims": claims,
        }

    def create_token(self, user_id: str, role: str = DEFAULT_ROLE, exp: int = None) -> str:
        """Create a JWT token (for testing/demo purposes)"""
        import time

        payload = {
            "sub": user_id,
            "role": role,
            "iat": int(time.time()),
        }
        if exp:
            payload["exp"] = int(time.time()) + exp

        return jwt.encode(
            payload,
            self.private_key,
            algorithm="EdDSA",
        )


def require_auth(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        handler = current_app.jwt_handler
        token = handler.extract_jwt_from_header(request.headers)
        if not token:
            return jsonify({"error": "Missing authorization token"}), 401

        claims = handler.validate_jwt(token)
        if not claims:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated_function
