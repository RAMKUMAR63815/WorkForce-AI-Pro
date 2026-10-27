
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    uploaded_by: int
    file_name: str
    category: str
    content_type: str
    size_bytes: int
    created_at: datetime
