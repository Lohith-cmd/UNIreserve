from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2 import errors

from app.auth_utils import create_access_token, hash_password, verify_password
from app.database import get_db_cursor
from app.dependencies import get_current_user
from app.schemas.auth import (
    FacultyRegister,
    LoginRequest,
    StudentRegister,
    TokenResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """
    Authenticates a user via email and password.
    Returns an RS256 JWT access token and user profile metadata.
    """
    with get_db_cursor(commit=False) as cur:
        query = """
            SELECT u.UserID, u.Name, u.Email, u.PasswordHash, u.Role, u.Phone,
                   s.BITS_ID, s.Department AS StudentDepartment, s.Year,
                   f.EmployeeID, f.Department AS FacultyDepartment, f.Designation,
                   a.AdminLevel
            FROM Users u
            LEFT JOIN Student s ON s.UserID = u.UserID
            LEFT JOIN Faculty f ON f.UserID = u.UserID
            LEFT JOIN Admin a ON a.UserID = u.UserID
            WHERE LOWER(u.Email) = LOWER(%s);
        """
        cur.execute(query, (payload.email,))
        row = cur.fetchone()

        if not row or not verify_password(payload.password, row["passwordhash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_profile = UserProfileResponse(
            user_id=row["userid"],
            name=row["name"],
            email=row["email"],
            role=row["role"],
            phone=row["phone"],
            bits_id=row["bits_id"],
            department=row["studentdepartment"] or row["facultydepartment"],
            year=row["year"],
            employee_id=row["employeeid"],
            designation=row["designation"],
            admin_level=row["adminlevel"],
        )

        token = create_access_token(
            data={"sub": str(row["userid"]), "role": row["role"]}
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=user_profile,
        )


@router.get("/me", response_model=UserProfileResponse)
def get_me(user: dict = Depends(get_current_user)):
    """
    Returns the authenticated user's profile metadata.
    """
    return UserProfileResponse(**user)


@router.post("/register/student", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: StudentRegister):
    """
    Registers a new student, hashes password with bcrypt, and creates role row.
    """
    pwd_hash = hash_password(payload.password)

    with get_db_cursor(commit=True) as cur:
        # Check duplicate email
        cur.execute("SELECT UserID FROM Users WHERE LOWER(Email) = LOWER(%s);", (payload.email,))
        if cur.fetchone():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        # Check duplicate BITS_ID
        cur.execute("SELECT UserID FROM Student WHERE BITS_ID = %s;", (payload.bits_id,))
        if cur.fetchone():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="BITS ID already registered")

        # Insert user
        cur.execute(
            """
            INSERT INTO Users (Name, Email, PasswordHash, Phone, Role)
            VALUES (%s, %s, %s, %s, 'Student')
            RETURNING UserID;
            """,
            (payload.name, payload.email, pwd_hash, payload.phone),
        )
        user_id = cur.fetchone()["userid"]

        # Insert student
        cur.execute(
            """
            INSERT INTO Student (UserID, BITS_ID, Department, Year)
            VALUES (%s, %s, %s, %s);
            """,
            (user_id, payload.bits_id, payload.department, payload.year),
        )

        user_profile = UserProfileResponse(
            user_id=user_id,
            name=payload.name,
            email=payload.email,
            role="Student",
            phone=payload.phone,
            bits_id=payload.bits_id,
            department=payload.department,
            year=payload.year,
        )

        token = create_access_token(data={"sub": str(user_id), "role": "Student"})
        return TokenResponse(access_token=token, token_type="bearer", user=user_profile)


@router.post("/register/faculty", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_faculty(payload: FacultyRegister):
    """
    Registers a new faculty member, hashes password with bcrypt, and creates role row.
    """
    pwd_hash = hash_password(payload.password)

    with get_db_cursor(commit=True) as cur:
        # Check duplicate email
        cur.execute("SELECT UserID FROM Users WHERE LOWER(Email) = LOWER(%s);", (payload.email,))
        if cur.fetchone():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        # Check duplicate EmployeeID
        cur.execute("SELECT UserID FROM Faculty WHERE EmployeeID = %s;", (payload.employee_id,))
        if cur.fetchone():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee ID already registered")

        # Insert user
        cur.execute(
            """
            INSERT INTO Users (Name, Email, PasswordHash, Phone, Role)
            VALUES (%s, %s, %s, %s, 'Faculty')
            RETURNING UserID;
            """,
            (payload.name, payload.email, pwd_hash, payload.phone),
        )
        user_id = cur.fetchone()["userid"]

        # Insert faculty
        cur.execute(
            """
            INSERT INTO Faculty (UserID, EmployeeID, Department, Designation)
            VALUES (%s, %s, %s, %s);
            """,
            (user_id, payload.employee_id, payload.department, payload.designation),
        )

        user_profile = UserProfileResponse(
            user_id=user_id,
            name=payload.name,
            email=payload.email,
            role="Faculty",
            phone=payload.phone,
            employee_id=payload.employee_id,
            department=payload.department,
            designation=payload.designation,
        )

        token = create_access_token(data={"sub": str(user_id), "role": "Faculty"})
        return TokenResponse(access_token=token, token_type="bearer", user=user_profile)


@router.get("/status")
def auth_status():
    """
    Returns auth subsystem status.
    """
    return {"status": "ok", "algorithm": "RS256"}
