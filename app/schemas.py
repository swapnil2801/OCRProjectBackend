from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime  # accept datetime type

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class HistoryBase(BaseModel):
    file_name: str
    scan_type: str
    extracted_text: str

class HistoryCreate(HistoryBase):
    pass

class HistoryOut(HistoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True