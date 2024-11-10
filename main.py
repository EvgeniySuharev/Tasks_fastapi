from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from backend.db_depends import get_db
from typing import Annotated
from sqlalchemy.orm import Session
from schemas import CreateUser, CreateTask
from sqlalchemy import insert, select, delete
from models.user import User
from models.task import Task
from fastapi.responses import RedirectResponse


app = FastAPI()
templates = Jinja2Templates(directory='templates')
security = HTTPBasic()


def get_current_user(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
        db: Annotated[Session, Depends(get_db)]
):
    query = select(User).where(User.name == credentials.username)
    user = db.scalar(query)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'User {credentials.username} not found',
            headers={'WWW-Authenticate': 'Basic'}
        )
    if user.password != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='password incorrect',
            headers={'WWW-Authenticate': 'Basic'}
        )
    return user


@app.get('/')
async def home(request: Request):
    context = {
        'request': request,
        'title': 'Главная'
    }
    return templates.TemplateResponse('tasks/base.html', context)


@app.get('/create_user/')
async def create_user(request: Request):
    context = {
        'request': request,
        'title': 'Зарегистрироваться',
    }
    return templates.TemplateResponse('users/registration.html', context)


@app.post('/register')
async def register_user(request: Request,
                        db: Annotated[Session, Depends(get_db)],
                        name=Form(max_length=20),
                        password1=Form(max_length=20),
                        password2=Form(max_length=20)):
    context = {
        'request': request,
        'title': 'Зарегистрироваться',
    }
    res = db.execute(select(User))
    users = res.scalars().all()
    for user in users:
        if user.name == name:
            context['msg'] = f'Пользователь {name} уже существует'
            return templates.TemplateResponse('users/registration.html', context)
    if password1 == password2:
        query = insert(User).values(
            name=name,
            password=password1,
        )
        db.execute(query)
        db.commit()
        context['msg'] = f'Пользователь {name} создан'
    else:
        context['msg'] = 'Пароли не совпадают'
    return templates.TemplateResponse('users/registration.html', context)


@app.get('/all_users/')
async def all_users(db: Annotated[Session, Depends(get_db)]):
    res = db.execute(select(User))
    users = res.scalars().all()
    return users


@app.post('/create_task')
async def create_task(request: Request,
                      db: Annotated[Session, Depends(get_db)],
                      title=Form(max_length=20),
                      content=Form(),
                      user_id=1):
    query = insert(Task).values(
        title=title,
        content=content,
        user_id=user_id
    )
    db.execute(query)
    db.commit()
    return RedirectResponse('/all_tasks/', status_code=status.HTTP_302_FOUND)


@app.get('/all_tasks/')
async def all_tasks(credentials: Annotated[HTTPBasicCredentials, Depends(get_current_user)],
                    request: Request,
                    db: Annotated[Session, Depends(get_db)]):
    res = db.execute(select(Task))
    tasks = res.scalars().all()
    context = {
        'request': request,
        'title': 'Мои задачи',
        'all_tasks': tasks
    }
    return templates.TemplateResponse('tasks/tasks.html', context)
