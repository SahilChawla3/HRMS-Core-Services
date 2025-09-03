from fastapi import FastAPI
from app.routes import employees

# Create DB tables (only if not using Alembic)
# models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Employee Management API")

# Register routes
app.include_router(employees.router)
# app.include_router(leave_requests.router, prefix="/leave-requests", tags=["Leave Requests"])    