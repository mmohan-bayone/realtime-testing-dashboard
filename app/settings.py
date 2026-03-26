import os
from typing import List


def _parse_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(',') if item.strip()]


DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./qa_dashboard.db')
CORS_ORIGINS = _parse_csv(os.getenv('CORS_ORIGINS', '*'))
AUTO_CREATE_SCHEMA = os.getenv('AUTO_CREATE_SCHEMA', 'true').lower() == 'true'
