from pathlib import Path
from uuid import uuid4
from fastapi import Query
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from app.core.dependencies import DbSession, AuthenticatedUser, HRUser
from app.models.document import Document
from app.models.employee import Employee
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_TYPES = {
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
}


@router.post("/my", response_model=DocumentResponse)
async def upload_my_document(
    db: DbSession,
    current_user: AuthenticatedUser,
    category: str = Form(..., min_length=2, max_length=50),
    file: UploadFile = File(...),
):
    """Employee uploads a document to their own profile."""

    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(404, "Employee profile not found.")

    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_TYPES:
        raise HTTPException(
            400,
            "Only PDF, PNG, and JPEG files are allowed.",
        )

    if file.content_type not in ALLOWED_TYPES[extension]:
        raise HTTPException(
            400,
            "File content type does not match an allowed type.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(400, "The uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Maximum file size is 5 MB.")

    # Generate a safe, unpredictable stored filename.
    stored_filename = f"{uuid4().hex}{extension}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / stored_filename

    try:
        with file_path.open("xb") as destination:
            destination.write(content)

        document = Document(
            employee_id=employee.id,
            uploaded_by=current_user.id,
            file_name=original_name,
            stored_filename=stored_filename,
            category=category.strip().upper(),
            content_type=file.content_type,
            size_bytes=len(content),
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    finally:
        await file.close()


@router.get("/my", response_model=list[DocumentResponse])
def get_my_documents(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    """Employee sees only their own documents."""

    employee = db.scalar(
        select(Employee).where(
            Employee.user_id == current_user.id
        )
    )

    if employee is None:
        raise HTTPException(404, "Employee profile not found.")

    return db.scalars(
        select(Document)
        .where(Document.employee_id == employee.id)
        .order_by(Document.created_at.desc())
    ).all()



@router.get("/", response_model=list[DocumentResponse])
def get_all_documents(
    db: DbSession,
    current_user: HRUser,
    employee_id: int | None = Query(default=None, gt=0),
    category: str | None = Query(
        default=None,
        min_length=2,
        max_length=50,
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """HR/Admin searches document metadata."""

    query = select(Document)

    if employee_id is not None:
        query = query.where(
            Document.employee_id == employee_id
        )

    if category:
        query = query.where(
            Document.category == category.strip().upper()
        )

    return db.scalars(
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()



@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    """Only the document owner or HR/Admin can download a file."""

    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(404, "Document not found.")

    employee = db.scalar(
        select(Employee).where(
            Employee.id == document.employee_id
        )
    )

    is_hr_or_admin = current_user.role in {"HR", "ADMIN"}
    is_owner = (
        employee is not None
        and employee.user_id == current_user.id
    )

    if not is_hr_or_admin and not is_owner:
        raise HTTPException(403, "You cannot access this document.")

    file_path = UPLOAD_DIR / document.stored_filename

    if not file_path.is_file():
        raise HTTPException(404, "Stored document file not found.")

    return FileResponse(
        path=file_path,
        media_type=document.content_type,
        filename=document.file_name,
    )

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    """Owner or HR/Admin can delete a document."""

    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(404, "Document not found.")

    employee = db.get(Employee, document.employee_id)

    is_hr_or_admin = current_user.role in {"HR", "ADMIN"}
    is_owner = (
        employee is not None
        and employee.user_id == current_user.id
    )

    if not is_hr_or_admin and not is_owner:
        raise HTTPException(
            403,
            "You cannot delete this document.",
        )

    file_path = UPLOAD_DIR / document.stored_filename

    # Remove the database record first.
    db.delete(document)
    db.commit()

    # Then remove the stored file, if it exists.
    file_path.unlink(missing_ok=True)

    return {"message": "Document deleted successfully."}
