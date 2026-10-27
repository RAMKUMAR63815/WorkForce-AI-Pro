
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.core.dependencies import DbSession, AuthenticatedUser, HRUser
from app.models.employee import Employee
from app.models.payroll import Payroll
from app.schemas.payroll import PayrollCreate, PayrollResponse
from datetime import date, datetime
from io import BytesIO
from fastapi import Response
from fastapi.responses import StreamingResponse
from app.models.attendance import Attendance

router = APIRouter(
    prefix="/payroll",
    tags=["Payroll"],
)


@router.post(
    "/process",
    response_model=PayrollResponse,
)
def process_payroll(
    payload: PayrollCreate,
    db: DbSession,
    current_user: HRUser,
):
    """HR/Admin processes monthly employee payroll."""

    employee = db.get(Employee, payload.employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    existing = db.scalar(
        select(Payroll).where(
            Payroll.employee_id == employee.id,
            Payroll.year == payload.year,
            Payroll.month == payload.month,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Payroll already processed for this month.",
        )

    basic_salary = Decimal(str(employee.salary))
    allowance = payload.allowance
    deduction = payload.deduction

    net_salary = basic_salary + allowance - deduction

    if net_salary < 0:
        raise HTTPException(
            status_code=400,
            detail="Deductions cannot exceed total earnings.",
        )

    payroll = Payroll(
        employee_id=employee.id,
        year=payload.year,
        month=payload.month,
        basic_salary=basic_salary,
        allowance=allowance,
        deduction=deduction,
        net_salary=net_salary,
        status="PROCESSED",
    )

    db.add(payroll)
    db.commit()
    db.refresh(payroll)

    return payroll


@router.get(
    "/my",
    response_model=list[PayrollResponse],
)
def get_my_payroll(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    """Employee views their own salary history."""

    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee profile not found.",
        )

    return db.scalars(
        select(Payroll)
        .where(Payroll.employee_id == employee.id)
        .order_by(Payroll.year.desc(), Payroll.month.desc())
    ).all()


@router.get(
    "/",
    response_model=list[PayrollResponse],
)
def get_all_payroll(
    db: DbSession,
    current_user: HRUser,
    year: int | None = None,
    month: int | None = None,
):
    """HR/Admin views payroll records."""

    query = select(Payroll)

    if year is not None:
        query = query.where(Payroll.year == year)

    if month is not None:
        if month < 1 or month > 12:
            raise HTTPException(
                status_code=400,
                detail="Month must be between 1 and 12.",
            )

        query = query.where(Payroll.month == month)

    return db.scalars(
        query.order_by(
            Payroll.year.desc(),
            Payroll.month.desc(),
        )
    ).all()

def build_attendance_summary(
    db: DbSession,
    employee_id: int,
    year: int,
    month: int,
):
    """Summarize attendance for one calendar month."""

    if not 1 <= month <= 12:
        raise HTTPException(
            status_code=400,
            detail="Month must be between 1 and 12.",
        )

    start_date = datetime(year, month, 1)

    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    records = db.scalars(
        select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.check_in >= start_date,
            Attendance.check_in < end_date,
        )
    ).all()

    # Count unique calendar days, not individual check-in records.
    attendance_dates = {
        record.check_in.date()
        for record in records
    }

    completed_records = [
        record for record in records
        if record.worked_minutes is not None
    ]

    total_minutes = sum(
        record.worked_minutes
        for record in completed_records
    )

    return {
        "employee_id": employee_id,
        "year": year,
        "month": month,
        "attendance_days": len(attendance_dates),
        "completed_sessions": len(completed_records),
        "open_sessions": len(records) - len(completed_records),
        "total_worked_minutes": total_minutes,
        "total_worked_hours": round(total_minutes / 60, 2),
    }


@router.get("/attendance-summary/my")
def my_payroll_attendance_summary(
    db: DbSession,
    current_user: AuthenticatedUser,
    year: int = date.today().year,
    month: int = date.today().month,
):
    """Employee views their own monthly attendance summary."""

    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee profile not found.",
        )

    return build_attendance_summary(
        db, employee.id, year, month
    )


@router.get("/attendance-summary/{employee_id}")
def employee_payroll_attendance_summary(
    employee_id: int,
    db: DbSession,
    current_user: HRUser,
    year: int = date.today().year,
    month: int = date.today().month,
):
    """HR/Admin views an employee's monthly attendance summary."""

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    return build_attendance_summary(
        db, employee.id, year, month
    )


def generate_payslip_pdf(payroll: Payroll, employee: Employee) -> BytesIO:
    """Generate a simple PDF from a saved payroll record."""

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    content = [
        Paragraph("WorkForce AI Pro — Payslip", styles["Title"]),
        Spacer(1, 8 * mm),
        Paragraph(
            f"Employee Code: {employee.employee_code}",
            styles["Normal"],
        ),
        Paragraph(
            f"Designation: {employee.designation}",
            styles["Normal"],
        ),
        Paragraph(
            f"Payroll Period: {payroll.month:02d}/{payroll.year}",
            styles["Normal"],
        ),
        Spacer(1, 8 * mm),
    ]

    salary_table = Table(
        [
            ["Salary Component", "Amount (INR)"],
            ["Basic Salary", f"Rs. {payroll.basic_salary:,.2f}"],
            ["Allowances", f"Rs. {payroll.allowance:,.2f}"],
            ["Deductions", f"Rs. {payroll.deduction:,.2f}"],
            ["Net Salary", f"Rs. {payroll.net_salary:,.2f}"],
            ["Payroll Status", payroll.status],
        ],
        colWidths=[85 * mm, 65 * mm],
    )

    salary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"),
        ])
    )

    content.extend([
        salary_table,
        Spacer(1, 8 * mm),
        Paragraph(
            "This payslip reflects the payroll record stored in the system.",
            styles["Italic"],
        ),
    ])

    document.build(content)
    buffer.seek(0)
    return buffer


@router.get("/my/{payroll_id}/payslip.pdf")
def download_my_payslip(
    payroll_id: int,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    """Employee downloads only their own payslip."""

    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee profile not found.",
        )

    payroll = db.get(Payroll, payroll_id)

    if payroll is None or payroll.employee_id != employee.id:
        raise HTTPException(
            status_code=404,
            detail="Payslip not found.",
        )

    pdf = generate_payslip_pdf(payroll, employee)

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="payslip_{payroll.year}_'
                f'{payroll.month:02d}.pdf"'
            )
        },
    )


@router.get("/{payroll_id}/payslip.pdf")
def download_employee_payslip(
    payroll_id: int,
    db: DbSession,
    current_user: HRUser,
):
    """HR/Admin downloads an employee's payslip."""

    payroll = db.get(Payroll, payroll_id)

    if payroll is None:
        raise HTTPException(
            status_code=404,
            detail="Payslip not found.",
        )

    employee = db.get(Employee, payroll.employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    pdf = generate_payslip_pdf(payroll, employee)

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="payslip_{payroll.year}_'
                f'{payroll.month:02d}.pdf"'
            )
        },
    )
