from typing import Annotated
from fastapi import FastAPI, Depends, status, Path, HTTPException
from pydantic import BaseModel, Field

from models import Base, ToDo
from sqlalchemy.orm import Session
from database import engine, SessionLocal
app = FastAPI()

Base.metadata.create_all(bind=engine)

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

@app.get("/read-all")
async def read_all(db: db_dependency):
    return db.query(ToDo).all()

@app.get("/get-by-id/{todo_id}", status_code=status.HTTP_200_OK)
async def read_by_id(db: db_dependency, todo_id: int = Path(ge=1)):
    todo = db.query(ToDo).filter(ToDo.id == todo_id).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ToDo not found.")

@app.post("/create-todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: ToDoRequest):
    todo = ToDo(**todo_request.model_dump())
    db.add(todo)
    db.commit()

@app.put("/update-todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@app.delete("/delete_todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo = db.query(ToDo).filter (ToDo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_N0T_FOUND, detail="ToDo not found.")
    db.delete(todo)
    db.commit()