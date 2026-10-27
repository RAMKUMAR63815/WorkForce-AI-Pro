
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.rbac import DbSession, HRUser
from app.models.employee import Employee
from app.models.user import User
from app.models.attrition_prediction import AttritionPrediction
from app.models.workforce_forecast import WorkforceForecast
from app.schemas.workforce_forecast import WorkforceForecastResponse

router = APIRouter(
    prefix="/workforce-forecast",
    tags=["Workforce Forecasting"],
)


@router.post(
    "/generate",
    response_model=WorkforceForecastResponse,
)
def generate_forecast(
    db: DbSession,
    current_user: HRUser,
    months: int = Query(default=12, ge=1, le=12),
):
    # Count employees whose linked user accounts are active.
    current_headcount = db.scalar(
        select(func.count(Employee.id))
        .join(User, Employee.user_id == User.id)
        .where(User.is_active.is_(True))
    ) or 0

    if current_headcount == 0:
        raise HTTPException(
            status_code=400,
            detail="No active employees are available for forecasting.",
        )

    # Get active employee IDs.
    active_employee_ids = set(
        db.scalars(
            select(Employee.id)
            .join(User, Employee.user_id == User.id)
            .where(User.is_active.is_(True))
        ).all()
    )

    # Read predictions newest first.
    predictions = db.scalars(
        select(AttritionPrediction)
        .where(AttritionPrediction.employee_id.is_not(None))
        .order_by(
            AttritionPrediction.created_at.desc(),
            AttritionPrediction.id.desc(),
        )
    ).all()

    # Keep only the latest prediction for each active employee.
    latest_risks = {}

    for prediction in predictions:
        employee_id = prediction.employee_id

        if employee_id not in active_employee_ids:
            continue

        if employee_id not in latest_risks:
            latest_risks[employee_id] = max(
                0.0,
                min(100.0, float(prediction.risk_percentage)),
            )

    if not latest_risks:
        raise HTTPException(
            status_code=400,
            detail=(
                "No employee-linked attrition predictions found. "
                "Generate predictions for employees first."
            ),
        )

    # Risk-weighted planning estimate, not a validated forecast.
    expected_attrition_12_months = sum(
        risk / 100.0 for risk in latest_risks.values()
    )

    # Scale the scenario linearly to the requested horizon.
    projected_attrition = (
        expected_attrition_12_months * months / 12
    )

    projected_headcount = max(
        0.0,
        current_headcount - projected_attrition,
    )

    projected_retention_rate = (
        projected_headcount / current_headcount
    ) * 100

    assumptions = (
        "Risk-weighted planning scenario. Each employee's latest "
        "risk percentage is treated as a relative risk estimate. "
        "The estimate is scaled linearly by the requested months. "
        "This is not a calibrated attrition probability or a "
        "validated future headcount forecast. Employees without "
        "predictions are not included in the risk-weighted estimate."
    )

    forecast = WorkforceForecast(
        forecast_months=months,
        current_headcount=current_headcount,
        employees_with_predictions=len(latest_risks),
        expected_attrition_12_months=round(
            expected_attrition_12_months, 2
        ),
        projected_attrition=round(projected_attrition, 2),
        projected_headcount=round(projected_headcount, 2),
        projected_retention_rate=round(
            projected_retention_rate, 2
        ),
        assumptions=assumptions,
        generated_by=current_user.id,
    )

    db.add(forecast)
    db.commit()
    db.refresh(forecast)

    return forecast


@router.get(
    "/history",
    response_model=list[WorkforceForecastResponse],
)
def get_forecast_history(
    db: DbSession,
    current_user: HRUser,
    limit: int = Query(default=20, ge=1, le=100),
):
    return db.scalars(
        select(WorkforceForecast)
        .order_by(WorkforceForecast.created_at.desc())
        .limit(limit)
    ).all()
