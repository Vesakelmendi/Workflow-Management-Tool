from pydantic import BaseModel, EmailStr
from typing import List, Optional
from .role import Role


class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    password: str  # In a real app, this would be hashed
    roles: List[Role] = []


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    roles: List[Role] = []
