from pydantic import BaseModel


class CreateTask(BaseModel):
    title: str
    content: str
    user_id: int


class CreateUser(BaseModel):
    name: str
    password: str
