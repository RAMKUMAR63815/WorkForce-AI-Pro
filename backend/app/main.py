from fastapi import FastAPI
from contextlib import asynccontextmanager  # Defines startup and shutdown lifecycle code
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.db.seed import seed_initial_roles
from app.db.session import Base, engine
from app import models  # Registers all models with SQLAlchemy
from app.api.auth import router as auth_router
from app.api.rbac import router as rbac_router
from app.api.departments import router as departments_router
from app.api.employee import router as employees_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.attendance import router as attendance_router
from app.api.shifts import router as shifts_router
from app.api import leaves
from app.api import leave_balances
from app.api import dashboard
from app.api import payroll
from app.api import notification
from app.api import documents
from app.api import performance_reviews
from app.api import chat
from app.api import dataset
from app.api import attrition_prediction
from app.api import risk_monitoring
from app.api import workforce_forecast
from app.api import attrition_analytics
from app.api import hr_intervention
from app.api import attrition_alert
from app.api import workforce_monitoring
from app.services.monitoring_scheduler import (
    start_monitoring_scheduler,
    stop_monitoring_scheduler,
)
from app.api.workforce_dashboard import router as workforce_dashboard_router
from app.api.workforce_kpi_target import (
    router as workforce_kpi_target_router,
)
from app.api.workforce_kpi_breach import (
    router as workforce_kpi_breach_router,
)

from app.api.employee_risk_monitoring import (
    router as employee_risk_monitoring_router,
)
from app.api.employee_risk_alert import (
    router as employee_risk_alert_router,
)
from app.api.employee_risk_alert_actions import (
    router as employee_risk_alert_actions_router,
)
from app.api.employee_risk_alert_dashboard import (
    router as employee_risk_alert_dashboard_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables that do not already exist.
    Base.metadata.create_all(bind=engine)

    # Insert default roles if they do not exist.
    seed_initial_roles()

    try:
        # Start background monitoring.
        start_monitoring_scheduler()
        yield
    finally:
        # Stop background monitoring during shutdown.
        stop_monitoring_scheduler()  # Application starts accepting requests


# Create the main FastAPI application.
app = FastAPI(
    title="WorkForce AI Pro",
    description="HR Attrition Prediction & Workforce Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/api")
app.include_router(rbac_router, prefix="/api")
app.include_router(departments_router, prefix="/api")
app.include_router(employees_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(shifts_router, prefix="/api")
app.include_router(leaves.router, prefix="/api")
app.include_router(leave_balances.router,prefix="/api",)
app.include_router(dashboard.router, prefix="/api")
app.include_router(payroll.router, prefix="/api")
app.include_router(notification.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(performance_reviews.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(dataset.router, prefix="/api")
app.include_router(attrition_prediction.router, prefix="/api")
app.include_router(risk_monitoring.router, prefix="/api")
app.include_router(workforce_forecast.router, prefix="/api")
app.include_router(attrition_analytics.router, prefix="/api")
app.include_router(hr_intervention.router, prefix="/api")
app.include_router(attrition_alert.router, prefix="/api")
app.include_router(workforce_monitoring.router,prefix="/api",)
app.include_router(workforce_dashboard_router, prefix="/api")
app.include_router(workforce_kpi_target_router, prefix="/api")
app.include_router(workforce_kpi_breach_router, prefix="/api")
app.include_router(employee_risk_monitoring_router, prefix="/api")
app.include_router(employee_risk_alert_router, prefix="/api")
app.include_router(employee_risk_alert_actions_router,prefix="/api",)
app.include_router(employee_risk_alert_dashboard_router,prefix="/api",)
# Health-check endpoint to verify that the backend is running.
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "WorkForce AI Pro",
    }


# Database health-check endpoint to verify MySQL connectivity.
@app.get("/health/database")
def database_health_check() -> dict[str, str]:
    """Verify that MySQL accepts a query."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"status": "connected"}

    except SQLAlchemyError:
        # Avoid exposing credentials or internal errors.
        return {"status": "disconnected"}


# Root endpoint for basic application information.
@app.get("/")
def home():
    return {
        "message": "Welcome to WorkForce AI Pro",
        "docs": "/docs",
    }
