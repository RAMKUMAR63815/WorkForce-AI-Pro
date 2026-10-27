
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, case
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import DbSession, HRUser, AuthenticatedUser
from app.models import Department, Employee, User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
)

router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
)


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    payload: DepartmentCreate,
    db: DbSession,
    current_user: HRUser,
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(422, "Department name cannot be blank")

    existing = db.scalar(
        select(Department).where(Department.name == name)
    )
    if existing:
        raise HTTPException(409, "Department already exists")

    department = Department(
        name=name,
        description=payload.description.strip()
        if payload.description and payload.description.strip()
        else None,
        is_active=True,
    )

    db.add(department)
    try:
        db.commit()
        db.refresh(department)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Department already exists") from None

    return department
@router.get("/statistics")
def department_statistics(
    db: DbSession,
    current_user: HRUser,
) -> list[dict]:
    """Return employee statistics for each department."""

    query = (
        select(
            Department.id.label("department_id"),
            Department.name.label("department_name"),
            Department.is_active.label("is_active"),
            func.count(Employee.id).label("total_employees"),
            func.count(
                case(
                    (User.is_active.is_(True), Employee.id)
                )
            ).label("active_employees"),
        )
        .outerjoin(
            Employee,
            Employee.department_id == Department.id,
        )
        .outerjoin(
            User,
            User.id == Employee.user_id,
        )
        .group_by(
            Department.id,
            Department.name,
            Department.is_active,
        )
        .order_by(Department.name)
    )

    results = db.execute(query).mappings().all()

    return [dict(row) for row in results]

@router.get("/", response_model=list[DepartmentResponse])
def list_departments(
    db: DbSession,
    current_user: AuthenticatedUser,
    include_inactive: bool = Query(default=False),
):
    query = select(Department).order_by(Department.name)

    # Only ADMIN/HR may request inactive departments.
    if not include_inactive or current_user.role.name not in {"ADMIN", "HR"}:
        query = query.where(Department.is_active.is_(True))

    return db.scalars(query).all()


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: int,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    department = db.get(Department, department_id)

    if department is None or (
        not department.is_active
        and current_user.role.name not in {"ADMIN", "HR"}
    ):
        raise HTTPException(404, "Department not found")

    return department


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    db: DbSession,
    current_user: HRUser,
):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(404, "Department not found")

    changes = payload.model_dump(exclude_unset=True) #model_dump() — converts the Pydantic model into a Python dictionary.exclude_unset=True — excludes fields the client did not provide in the request.

    if not changes:
        raise HTTPException(422, "Provide at least one field to update")

    if "name" in changes:
        if changes["name"] is None or not changes["name"].strip():
            raise HTTPException(422, "Department name cannot be blank")

        changes["name"] = changes["name"].strip()

        duplicate = db.scalar(
            select(Department).where(
                Department.name == changes["name"],
                Department.id != department_id,
            )
        )
        if duplicate:
            raise HTTPException(409, "Department name already exists")

    if "description" in changes and changes["description"] is not None:
        changes["description"] = changes["description"].strip() or None

    for field, value in changes.items():
        setattr(department, field, value)

    try:
        db.commit()
        db.refresh(department)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Department name already exists") from None

    return department


@router.delete("/{department_id}")
def deactivate_department(
    department_id: int,
    db: DbSession,
    current_user: HRUser,
):
    department = db.get(Department, department_id)

    if department is None:
        raise HTTPException(404, "Department not found")

    if not department.is_active:
        raise HTTPException(409, "Department is already inactive")

    department.is_active = False
    db.commit()

    return {
        "message": "Department deactivated successfully",
        "department_id": department.id,
    }
