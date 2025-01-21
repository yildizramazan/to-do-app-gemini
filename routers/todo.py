from typing import Annotated
from fastapi import APIRouter, Depends, status, Path, HTTPException
from pydantic import BaseModel, Field
from models import Base, ToDo
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from routers.auth import get_current_user

router = APIRouter(
    prefix="/todo",
    tags=["ToDo"]
)

class ToDoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=1000)
    priority: int = Field(ge=1, le=5)
    done: bool = Field(default=False)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]




@router.get("/read-all")
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(ToDo).all()

@router.get("/get-by-id/{todo_id}", status_code=status.HTTP_200_OK)
async def read_by_id(db: db_dependency, todo_id: int = Path(ge=1)):
    todo = db.query(ToDo).filter(ToDo.id == todo_id).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ToDo not found.")

@router.post("/create-todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: ToDoRequest):
    todo = ToDo(**todo_request.model_dump())
    db.add(todo)
    db.commit()

@router.put("/update-todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency,
                      todo_request: ToDoRequest,
                      todo_id: int = Path(ge=1)):
    todo = db.query(ToDo).filter(ToDo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ToDo not found.")


    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.done = todo_request.done

    db.add(todo)
    db.commit()


@router.delete("/delete_todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo = db.query(ToDo).filter (ToDo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_N0T_FOUND, detail="ToDo not found.")
    db.delete(todo)
    db.commit()