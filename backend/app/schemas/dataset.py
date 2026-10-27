
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_name: str
    version: int
    original_filename: str
    uploaded_by: int
    total_rows: int
    valid_rows: int
    invalid_rows: int
    status: str
    created_at: datetime
