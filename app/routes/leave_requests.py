from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database, schemas
from datetime import date

router = APIRouter(prefix="/leave-requests", tags=["Leave Requests"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/balance/{employee_id}")
def get_leave_balance(employee_id: str, db: Session = Depends(get_db)):
    # Check if employee exists
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Define leave allowances
    leave_allowance = {
        models.LeaveTypeEnum.paid: 20,
        models.LeaveTypeEnum.sick: 10,
        models.LeaveTypeEnum.unpaid: 0  # usually unlimited/untracked
    }

    # Prepare result
    balance = {}

    for leave_type, total_allowed in leave_allowance.items():
        # Fetch approved leaves of this type
        leaves = (
            db.query(models.LeaveRequest)
            .filter(
                models.LeaveRequest.employee_id == employee_id,
                models.LeaveRequest.status == models.LeaveStatusEnum.approved,
                models.LeaveRequest.leave_type == leave_type
            )
            .all()
        )

        # Sum total leave days
        total_taken = sum((lr.end_date - lr.start_date).days + 1 for lr in leaves)

        # Calculate remaining
        remaining = total_allowed - total_taken
        if remaining < 0:
            remaining = 0

        balance[leave_type.value] = {
            "total_allowed": total_allowed,
            "leaves_taken": total_taken,
            "leaves_remaining": remaining
        }

    return {
        "employee_id": employee_id,
        "employee_name": f"{employee.first_name} {employee.last_name}",
        "leave_balance": balance
    }

@router.post("/apply", response_model=schemas.LeaveRequestResponse)
def create_leave_request(leave_data: schemas.LeaveRequestCreate, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.id == leave_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check for start_date should not be less than today. 
    if leave_data.start_date < date.today():
        raise HTTPException(status_code=400, detail="Cannot apply leave for past dates")
    
    # Check for overlapping leaves
    overlapping_leave = db.query(models.LeaveRequest)\
        .filter(
            models.LeaveRequest.employee_id == leave_data.employee_id,
            models.LeaveRequest.status.in_([models.LeaveStatusEnum.approved, models.LeaveStatusEnum.pending]),
            models.LeaveRequest.start_date <= leave_data.end_date,
            models.LeaveRequest.end_date >= leave_data.start_date
        ).first()

    if overlapping_leave:
        raise HTTPException(
            status_code=400,
            detail=f"Leave overlaps with existing leave from {overlapping_leave.start_date} to {overlapping_leave.end_date}"
        )
    
    # Define leave allowances
    leave_allowance = {
        models.LeaveTypeEnum.paid: 20,
        models.LeaveTypeEnum.sick: 10,
        models.LeaveTypeEnum.unpaid: 0  # unlimited/untracked
    }

    # Calculate total taken leaves of this type
    approved_leaves = db.query(models.LeaveRequest)\
        .filter(
            models.LeaveRequest.employee_id == leave_data.employee_id,
            models.LeaveRequest.status == models.LeaveStatusEnum.approved,
            models.LeaveRequest.leave_type == leave_data.leave_type
        ).all()

    total_taken = sum((lr.end_date - lr.start_date).days + 1 for lr in approved_leaves)

    requested_days = (leave_data.end_date - leave_data.start_date).days + 1
    remaining_balance = leave_allowance[leave_data.leave_type] - total_taken

    if requested_days > remaining_balance:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient leave balance. Requested {requested_days} days, remaining {remaining_balance} days."
        )

    new_leave = models.LeaveRequest(
        employee_id=leave_data.employee_id,
        leave_type=leave_data.leave_type,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        status=leave_data.status or models.LeaveStatusEnum.pending,
        reason=leave_data.reason
    )

    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    return new_leave

@router.patch("/{leave_id}")
def update_leave_request(
    leave_id: str,
    leave_update: schemas.LeaveRequestUpdate,
    db: Session = Depends(get_db)
):
    leave_request = db.query(models.LeaveRequest).filter(models.LeaveRequest.id == leave_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # Update only status and manager_comments if provided
    if leave_update.status is not None:
        leave_request.status = leave_update.status.value
    if leave_update.manager_comments is not None:
        leave_request.manager_comments = leave_update.manager_comments

    db.commit()
    db.refresh(leave_request)
    return leave_request

@router.get("/history/{employee_id}")
def view_leave_history(employee_id: str, db: Session = Depends(get_db)):
    leave_history = db.query(models.LeaveRequest)\
                      .filter(models.LeaveRequest.employee_id == employee_id)\
                      .order_by(models.LeaveRequest.start_date.desc())\
                      .all()
    
    if not leave_history:
        raise HTTPException(status_code=404, detail="No leave history found for this employee")
    
    return leave_history