from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# Guardrail for JSON ingest body size; raise MAX_HTML_REPORT_CHARS if you need larger uploads.
MAX_HTML_REPORT_CHARS = 12_000_000


class TestCaseCreate(BaseModel):
    name: str
    module: str
    status: str
    duration_ms: int
    defect_id: Optional[str] = None


class TestRunCreate(BaseModel):
    suite_name: str
    environment: str
    build_version: str
    test_cases: list[TestCaseCreate]
    # Optional: link to a hosted HTML report (e.g. GitHub Pages, public artifact URL).
    html_report_url: Optional[str] = None
    # Optional: single-file HTML body for inline viewing on the dashboard (pytest-html, etc.).
    html_report_html: Optional[str] = Field(default=None, max_length=MAX_HTML_REPORT_CHARS)

    @field_validator('html_report_url')
    @classmethod
    def trim_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        return s or None


class TestCaseResponse(TestCaseCreate):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class TestRunResponse(BaseModel):
    id: int
    suite_name: str
    environment: str
    build_version: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    test_cases: list[TestCaseResponse]
    html_report_url: Optional[str] = None
    has_html_report_inline: bool = False
    has_html_report_zip: bool = False
    html_report_index_path: Optional[str] = None

    class Config:
        from_attributes = True
