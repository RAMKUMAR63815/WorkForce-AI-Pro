
import csv
import io
import json
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select

from app.api.rbac import DbSession, HRUser
from app.models.dataset import AttritionDataset
from app.schemas.dataset import DatasetResponse

router = APIRouter(prefix="/datasets", tags=["Dataset Management"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "datasets"
MAX_FILE_SIZE = 20 * 1024 * 1024

REQUIRED_COLUMNS = {
    "attrition",
    "age",
    "monthlyincome",
    "yearsatcompany",
    "overtime",
    "jobsatisfaction",
}


def normalize_column(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def validate_row(row: dict, seen_keys: set, row_number: int):
    normalized = {
        normalize_column(str(key)): (value or "").strip()
        for key, value in row.items()
        if key is not None
    }

    errors = []

    def get_value(name: str) -> str:
        return normalized.get(name, "")

    attrition = get_value("attrition").lower()
    if attrition not in {"yes", "no", "1", "0", "true", "false"}:
        errors.append("Attrition must be Yes/No, 1/0, or true/false.")

    numeric_rules = {
        "age": (18, 100),
        "monthlyincome": (0, 100000000),
        "yearsatcompany": (0, 100),
        "jobsatisfaction": (1, 4),
    }

    for column, (minimum, maximum) in numeric_rules.items():
        value = get_value(column)
        try:
            number = float(value)
            if not number.is_integer():
                errors.append(f"{column} must be a whole number.")
            elif not minimum <= number <= maximum:
                errors.append(
                    f"{column} must be between {minimum} and {maximum}."
                )
        except (ValueError, TypeError):
            errors.append(f"{column} must be numeric.")

    overtime = get_value("overtime").lower()
    if overtime not in {"yes", "no", "1", "0", "true", "false"}:
        errors.append("OverTime must be Yes/No, 1/0, or true/false.")

    employee_key = (
        get_value("employeenumber")
        or get_value("employeeid")
        or get_value("employee_id")
    )

    if employee_key:
        duplicate_key = ("employee", employee_key)
    else:
        duplicate_key = (
            "row",
            json.dumps(normalized, sort_keys=True),
        )

    if duplicate_key in seen_keys:
        errors.append("Duplicate employee identifier or duplicate row.")
    else:
        seen_keys.add(duplicate_key)

    return errors


@router.post("/", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    db: DbSession,
    current_user: HRUser,
    dataset_name: str = Form(min_length=2, max_length=150),
    file: UploadFile = File(...),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported.")

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(400, "Uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "CSV file cannot exceed 20 MB.")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "CSV must use UTF-8 encoding.")

    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(400, "CSV header row is missing.")

    normalized_headers = {
        normalize_column(name) for name in reader.fieldnames
    }
    missing = REQUIRED_COLUMNS - normalized_headers

    if missing:
        raise HTTPException(
            400,
            detail={
                "message": "CSV is missing required columns.",
                "missing_columns": sorted(missing),
            },
        )

    seen_keys = set()
    errors_report = []
    total_rows = 0
    valid_rows = 0

    for row_number, row in enumerate(reader, start=2):
        total_rows += 1
        errors = validate_row(row, seen_keys, row_number)

        if errors:
            if len(errors_report) < 1000:
                errors_report.append({
                    "row_number": row_number,
                    "errors": errors,
                })
        else:
            valid_rows += 1

    invalid_rows = total_rows - valid_rows

    latest_version = db.scalar(
        select(func.max(AttritionDataset.version)).where(
            AttritionDataset.dataset_name == dataset_name.strip()
        )
    )
    version = (latest_version or 0) + 1

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}.csv"
    destination = UPLOAD_DIR / stored_filename
    destination.write_bytes(content)

    dataset = AttritionDataset(
        dataset_name=dataset_name.strip(),
        version=version,
        original_filename=Path(file.filename).name,
        stored_filename=stored_filename,
        uploaded_by=current_user.id,
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        status="VALIDATED" if invalid_rows == 0 else "VALIDATION_ERRORS",
        validation_report=json.dumps(errors_report),
    )

    try:
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise

    return dataset


@router.get("/", response_model=list[DatasetResponse])
def list_datasets(
    db: DbSession,
    current_user: HRUser,
):
    return db.scalars(
        select(AttritionDataset).order_by(
            AttritionDataset.created_at.desc()
        )
    ).all()


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    db: DbSession,
    current_user: HRUser,
):
    dataset = db.get(AttritionDataset, dataset_id)

    if dataset is None:
        raise HTTPException(404, "Dataset not found.")

    return dataset


@router.get("/{dataset_id}/errors")
def get_dataset_validation_errors(
    dataset_id: int,
    db: DbSession,
    current_user: HRUser,
):
    dataset = db.get(AttritionDataset, dataset_id)

    if dataset is None:
        raise HTTPException(404, "Dataset not found.")

    return {
        "dataset_id": dataset.id,
        "dataset_name": dataset.dataset_name,
        "version": dataset.version,
        "total_rows": dataset.total_rows,
        "valid_rows": dataset.valid_rows,
        "invalid_rows": dataset.invalid_rows,
        "errors": json.loads(dataset.validation_report),
        "note": "At most 1000 invalid row reports are stored.",
    }
