from typing import Annotated
from fastapi import APIRouter, Depends, status, Path, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import RedirectResponse
from dotenv import load_dotenv
from models import ToDo
from sqlalchemy.orm import Session
from database import SessionLocal
from routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import markdown
from bs4 import BeautifulSoup



router = APIRouter(
    prefix="/todo",
    tags=["ToDo"]
)

templates = Jinja2Templates(directory="templates")


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

def redirect_to_login():
    redirect_response = RedirectResponse("/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response


@router.get("/todo-page")
async def render_todo(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todos = db.query(ToDo).filter(ToDo.owner_id == user.get("id")).all()
        return templates.TemplateResponse("todo.html", {"request": request, "todos": todos, "user": user})
    except:
        return redirect_to_login()


@router.get("/add-todo-page")
async def render_todo(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("todo.html", {"request": request, "user": user})
    except:
        return redirect_to_login()


@router.get("/edit-todo-page/{todo_id}")
async def render_todo(request: Request, db: db_dependency, todo_id: int):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todo = db.query(ToDo).filter(ToDo.id == todo_id).first()
        return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})
    except:
        return redirect_to_login()




@router.get("/read-all")
async def read_all(user: user_dependency, db: db_dependency = db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(ToDo).filter(ToDo.owner_id == user.get("id")).all()

@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
async def read_by_id(user: user_dependency, db: db_dependency, todo_id: int = Path(ge=1)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(ToDo).filter(ToDo.id == todo_id).filter(ToDo.owner_id == user.get("id")).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ToDo not found.")

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: ToDoRequest):
    todo = ToDo(**todo_request.model_dump(), owner_id=user.get("id"))
    todo.description = create_todo_with_gemini(todo_request.description)
    db.add(todo)
    db.commit()

@router.put("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency,
                      db: db_dependency,
                      todo_request: ToDoRequest,
                      todo_id: int = Path(ge=1)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    todo = db.query(ToDo).filter(ToDo.id == todo_id).filter(ToDo.owner_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ToDo not found.")


    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.done = todo_request.done

    db.add(todo)
    db.commit()


@router.delete("/delete_todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(ToDo).filter(ToDo.id == todo_id).filter(ToDo.owner_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_N0T_FOUND, detail="ToDo not found.")
    db.delete(todo)
    db.commit()


def markdown_to_text(markdown_text: str):
    html = markdown.markdown(markdown_text)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text




def create_todo_with_gemini(todo_string: str):
    load_dotenv()
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    llm = ChatGoogleGenerativeAI(model="gemini-pro")
    response = llm.invoke(
        [
            HumanMessage(content="I will provide you a todo item to add my list. What i want you to do is to create a longer and more comprehensive description of that todo item, my next message is my todo item."),
            HumanMessage(content=todo_string)
        ]
    )
    return markdown_to_text(response.content)

if __name__ == "__main__":

    print(db_dependency)