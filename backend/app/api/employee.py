from datetime import date
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from app.core.dependencies import DbSession, HRUser
from app.core.security import hash_password
from app.models import Department, Employee, Role, User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


def employee_query():
    """Load employee details and related user/department efficiently."""
    return select(Employee).options(
        selectinload(Employee.user),
        selectinload(Employee.department),
    )


def get_employee_or_404(db: DbSession, employee_id: int) -> Employee:
    employee = db.scalar(
        employee_query().where(Employee.id == employee_id)
    )
    if employee is None:
        raise HTTPException(404, "Employee not found")
    return employee


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    payload: EmployeeCreate,
    db: DbSession,
    current_user: HRUser,
):
    email = str(payload.email).strip().lower()
    employee_code = payload.employee_code.strip()

    if not employee_code:
        raise HTTPException(422, "Employee code cannot be blank")

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )
    if existing_user:
        raise HTTPException(409, "Email is already registered")

    existing_employee = db.scalar(
        select(Employee).where(
            Employee.employee_code == employee_code
        )
    )
    if existing_employee:
        raise HTTPException(409, "Employee code already exists")

    department = None
    if payload.department_id is not None:
        department = db.get(Department, payload.department_id)
        if department is None or not department.is_active:
            raise HTTPException(400, "Active department not found")

    employee_role = db.scalar(
        select(Role).where(Role.name == "EMPLOYEE")
    )
    if employee_role is None:
        raise HTTPException(500, "EMPLOYEE role is not configured")

    if payload.joining_date > date.today():
        raise HTTPException(
            422, "Joining date cannot be in the future"
        )

    user = User(
        email=email,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        hashed_password=hash_password(payload.password),
        role_id=employee_role.id,
        is_active=True,
    )

    employee = Employee(
        employee_code=employee_code,
        department=department,
        designation=payload.designation.strip(),
        joining_date=payload.joining_date,
        salary=payload.salary,
        phone=payload.phone.strip() if payload.phone else None,
        address=payload.address,
        user=user,
    )

    db.add(employee)

    try:
        db.commit()
        db.refresh(employee)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Email or employee code already exists"
        ) from None

    return get_employee_or_404(db, employee.id)


@router.get("/", response_model=list[EmployeeResponse])
def list_employees(
    db: DbSession,
    current_user: HRUser,
    search: str | None = Query(default=None, max_length=100),
    department_id: int | None = Query(default=None, gt=0),
    designation: str | None = Query(default=None, max_length=100),
    is_active: bool | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = employee_query().join(User, Employee.user_id == User.id)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Employee.employee_code.ilike(term),
                Employee.designation.ilike(term),
                User.first_name.ilike(term),
                User.last_name.ilike(term),
                User.email.ilike(term),
            )
        )

    if department_id is not None:
        query = query.where(
            Employee.department_id == department_id
        )

    if designation and designation.strip():
        query = query.where(
            Employee.designation.ilike(
                f"%{designation.strip()}%"
            )
        )

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    query = query.order_by(Employee.id).offset(offset).limit(limit)
    return db.scalars(query).all()


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: DbSession,
    current_user: HRUser,
):
    return get_employee_or_404(db, employee_id)


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: DbSession,
    current_user: HRUser,
):
    employee = get_employee_or_404(db, employee_id)
    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            422, "Provide at least one field to update"
        )

    if "first_name" in changes:
        if changes["first_name"] is None or not changes["first_name"].strip():
            raise HTTPException(422, "First name cannot be blank")
        employee.user.first_name = changes.pop("first_name").strip()

    if "last_name" in changes:
        if changes["last_name"] is None or not changes["last_name"].strip():
            raise HTTPException(422, "Last name cannot be blank")
        employee.user.last_name = changes.pop("last_name").strip()

    if "department_id" in changes:
        department_id = changes["department_id"]
        if department_id is None:
            employee.department = None
        else:
            department = db.get(Department, department_id)
            if department is None or not department.is_active:
                raise HTTPException(400, "Active department not found")
            employee.department = department
        changes.pop("department_id")

    if "designation" in changes:
        value = changes["designation"]
        if value is None or not value.strip():
            raise HTTPException(422, "Designation cannot be blank")
        changes["designation"] = value.strip()

    if "joining_date" in changes:
        value = changes["joining_date"]
        if value is not None and value > date.today():
            raise HTTPException(
                422, "Joining date cannot be in the future"
            )

    if "phone" in changes and changes["phone"] is not None:
        changes["phone"] = changes["phone"].strip() or None

    for field, value in changes.items():
        setattr(employee, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Employee update conflicts with existing data") from None

    return get_employee_or_404(db, employee_id)


@router.delete("/{employee_id}")
def deactivate_employee(
    employee_id: int,
    db: DbSession,
    current_user: HRUser,
):
    employee = get_employee_or_404(db, employee_id)

    if not employee.user.is_active:
        raise HTTPException(409, "Employee is already inactive")

    employee.user.is_active = False

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Unable to deactivate employee") from None

    return {
        "message": "Employee deactivated successfully",
        "employee_id": employee.id,
    }
