from typing import Annotated
from fastapi import APIRouter, Depends
from jose.constants import ALGORITHMS
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from starlette.exceptions import HTTPException
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

SECRET_KEY =  "57fw34yu2fd26c82g4f4j958j3fc48bdx28370gtr67"
ALGORITHM = "HS256"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
db_dependency = Annotated[Session, Depends(get_db)]



class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    payload = {'sub': username, 'id': user_id, 'role': role}
    expire = datetime.now(timezone.utc) + expires_delta
    payload['exp'] = expire
    return jwt.encode(payload, SECRET_KEY, ALGORITHM)




def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context_hashed.verify(password, user.hashed_password):
        return False
    return user


bcrypt_context_hashed = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, request: CreateUserRequest):
    user = User(
        username=request.username,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        is_active=True,
        hashed_password=bcrypt_context_hashed.hash(request.password)
    )
    db.add(user)
    db.commit()


@router.post("/token")
async def create_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],db: db_dependency = db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = ""
    return {"access_token": token, "token_type": "bearer"}
