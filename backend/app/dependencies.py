from typing import Optional
from fastapi import Header, HTTPException, status
from app.database import get_db_cursor


def get_current_user_id(x_user_id: Optional[int] = Header(None, alias="X-User-ID")) -> int:
    """
    Retrieves the current user ID. Accepts X-User-ID header for straightforward development
    and testing until JWT middleware is integrated.
    """
    if x_user_id is None:
        # Default to student test user (UserID 4) if not supplied in dev mode
        return 4
    return x_user_id


def require_admin_user(x_user_id: Optional[int] = Header(None, alias="X-User-ID")) -> int:
    """
    Ensures the user has the 'Admin' role in the Users table.
    """
    user_id = x_user_id if x_user_id is not None else 1  # UserID 1 is Admin in seed data
    with get_db_cursor(commit=False) as cur:
        cur.execute("SELECT Role FROM Users WHERE UserID = %s;", (user_id,))
        row = cur.fetchone()
        if not row or row["role"] != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
    return user_id

