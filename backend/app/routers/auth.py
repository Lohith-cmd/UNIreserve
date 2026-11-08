from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/status")
def auth_status():
    """
    Reserved for P3 (JWT Auth router).
    """
    return {"message": "Auth router placeholder for P3"}

