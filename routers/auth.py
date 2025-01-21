from fastapi import APIRouter

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.get("/get-user")
async def get_user():
    return {"user": "admin"}