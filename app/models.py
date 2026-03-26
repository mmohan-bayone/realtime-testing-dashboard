from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class TestRun(Base):
    __tablename__ = 'test_runs'

    id = Column(Integer, primary_key=True, index=True)
    suite_name = Column(String, index=True, nullable=False)
    environment = Column(String, index=True, nullable=False)
    build_version = Column(String, nullable=False)
    status = Column(String, default='RUNNING', nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    test_cases = relationship('TestCaseResult', back_populates='run', cascade='all, delete-orphan')


class TestCaseResult(Base):
    __tablename__ = 'test_case_results'

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey('test_runs.id'), nullable=False)
    name = Column(String, nullable=False)
    module = Column(String, nullable=False)
    status = Column(String, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    defect_id = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship('TestRun', back_populates='test_cases')
