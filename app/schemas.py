from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
from enum import Enum


# --- ENUMS (to match models.py) ---
class RoleEnum(str, Enum):
    Admin = "Admin"
    Manager = "Manager"
    Employee = "Employee"

class LeaveTypeEnum(str, Enum):
    paid = "paid"
    unpaid = "unpaid"
    sick = "sick"

class LeaveStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# --- EMPLOYEE SCHEMAS ---
class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    department: str
    role: RoleEnum
    manager_id: Optional[str] = None
    date_joined: date
    is_active: Optional[bool] = True


class EmployeeCreate(EmployeeBase):
    firebase_uid: Optional[str] = None


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    role: Optional[RoleEnum] = None
    manager_id: Optional[str] = None
    date_joined: Optional[date] = None
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    id: str
    firebase_uid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# --- LEAVE REQUEST SCHEMAS ---
class LeaveRequestBase(BaseModel):
    employee_id: str
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    reason: str


class LeaveRequestCreate(LeaveRequestBase):
    employee_id: str
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    status: Optional[LeaveStatusEnum] = LeaveStatusEnum.pending
    reason: str


class LeaveRequestUpdate(BaseModel):
    status: Optional[LeaveStatusEnum]
    manager_comments: Optional[str]


class LeaveRequestResponse(LeaveRequestBase):
    id: int
    status: LeaveStatusEnum
    manager_comments: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
