"""Test helpers: build real RS256 bearer headers without going through /auth/login."""
from app.auth_utils import create_access_token


def auth(user_id) -> dict:
    """Authorization header carrying a genuine signed JWT for the given user ID."""
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}
