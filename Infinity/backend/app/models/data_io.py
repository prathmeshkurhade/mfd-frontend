"""Pydantic models for Data Import/Export."""

from typing import List, Optional

from pydantic import BaseModel


class ImportError(BaseModel):
    """Error encountered during import."""

    row: int
    column: Optional[str] = None
    error: str


class ImportResult(BaseModel):
    """Result of data import operation."""

    total_rows: int
    imported: int
    skipped: int
    failed: int
    errors: List[ImportError]


class ImportValidationResult(BaseModel):
    """Result of import file validation."""

    valid: bool
    columns_found: List[str]
    columns_missing: List[str]
    row_count: int


class ExportRequest(BaseModel):
    """Request for data export."""

    entity_type: str
    filters: Optional[dict] = None
    format: str = "xlsx"  # xlsx or csv
