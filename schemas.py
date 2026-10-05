from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ProductCreate(BaseModel):
    name: str
    description: str
    price: int
    file_url: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    file_url: Optional[str] = None


class OrderCreate(BaseModel):
    user_id: int
    product_id: int