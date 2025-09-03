from sqlalchemy import Column, String, Integer, Date, DateTime, Text, Boolean, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

# --- ENUMS ---
class RoleEnum(str, enum.Enum):
    Admin = "Admin"
    Manager = "Manager"
    Employee = "Employee"

class LeaveTypeEnum(str, enum.Enum):
    paid = "paid"
    unpaid = "unpaid"
    sick = "sick"

class LeaveStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# --- EMPLOYEES TABLE ---
class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    firebase_uid = Column(String(100), unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    manager_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    date_joined = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    manager = relationship("Employee", remote_side=[id], backref="subordinates")
    leave_requests = relationship("LeaveRequest", back_populates="employee")


# --- LEAVE REQUESTS TABLE ---
class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    leave_type = Column(Enum(LeaveTypeEnum), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(LeaveStatusEnum), default=LeaveStatusEnum.pending)
    reason = Column(Text, nullable=False)
    manager_comments = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="leave_requests")
