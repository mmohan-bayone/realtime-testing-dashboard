from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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

    class Config:
        from_attributes = True
