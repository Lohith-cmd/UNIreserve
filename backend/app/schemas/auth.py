from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=150)
    password: str


class StudentRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6)
    phone: Optional[str] = Field(None, max_length=20)
    bits_id: str = Field(..., min_length=12, max_length=13)
    department: Optional[str] = None
    year: int = Field(..., ge=2020, le=2024)


class FacultyRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6)
    phone: Optional[str] = Field(None, max_length=20)
    employee_id: str = Field(..., min_length=3, max_length=20)
    department: Optional[str] = None
    designation: Optional[str] = None


class UserProfileResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    bits_id: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    admin_level: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse
