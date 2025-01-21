from typing import Annotated
from fastapi import APIRouter, Depends
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

bcrypt_context_hashed = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

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

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        user_id = payload.get('id')
        role = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username or ID is invalid")
        return {"username": username, "id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid")


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


@router.post("/token", response_model = Token)
async def create_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],db: db_dependency = db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = create_access_token(username=user.username, user_id=user.id, role=user.role, expires_delta=timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}
