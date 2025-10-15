from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# Base schema (shared across responses, never contains sensitive info)
class UserBase(BaseModel):
    username: str
    email: EmailStr
    subscriber: bool = False
    ai_personality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Schema for creating a new user (includes password)
class CreateUser(UserBase):
    password: str


# Schema for updating a user (all fields optional)
class UpdateUser(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    subscriber: Optional[bool] = None
    ai_personality: Optional[str] = None
    password: Optional[str] = None

    class Config:
        from_attributes = True


# Schema for returning user data (e.g., API responses)
class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True
