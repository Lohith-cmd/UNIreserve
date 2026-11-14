from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from app.auth_utils import decode_access_token
from app.database import get_db_cursor


def get_current_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> int:
    """
    Returns the authenticated user's ID from a valid 'Authorization: Bearer <token>'
    RS256 JWT. A missing, malformed, expired or tampered token is rejected with 401;
    there is no header or default-user fallback.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(authorization[7:].strip())
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return int(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(user_id: int = Depends(get_current_user_id)) -> dict:
    """
    Fetches full user profile details joined across role subtypes.
    """
    with get_db_cursor(commit=False) as cur:
        query = """
            SELECT u.UserID, u.Name, u.Email, u.Role, u.Phone,
                   s.BITS_ID, s.Department AS StudentDepartment, s.Year,
                   f.EmployeeID, f.Department AS FacultyDepartment, f.Designation,
                   a.AdminLevel
            FROM Users u
            LEFT JOIN Student s ON s.UserID = u.UserID
            LEFT JOIN Faculty f ON f.UserID = u.UserID
            LEFT JOIN Admin a ON a.UserID = u.UserID
            WHERE u.UserID = %s;
        """
        cur.execute(query, (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return {
            "user_id": row["userid"],
            "name": row["name"],
            "email": row["email"],
            "role": row["role"],
            "phone": row["phone"],
            "bits_id": row["bits_id"],
            "department": row["studentdepartment"] or row["facultydepartment"],
            "year": row["year"],
            "employee_id": row["employeeid"],
            "designation": row["designation"],
            "admin_level": row["adminlevel"],
        }


def require_admin_user(user_id: int = Depends(get_current_user_id)) -> int:
    """
    Ensures the user has the 'Admin' role in the Users table.
    The user comes from the verified JWT; the role is always re-read from the database.
    """
    with get_db_cursor(commit=False) as cur:
        cur.execute("SELECT Role FROM Users WHERE UserID = %s;", (user_id,))
        row = cur.fetchone()
        if not row or row["role"] != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )
    return user_id
