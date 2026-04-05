"""add html_report_zip for Playwright multi-file HTML reports

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('test_runs', sa.Column('html_report_zip', sa.LargeBinary(), nullable=True))
    op.add_column('test_runs', sa.Column('html_report_index_path', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('test_runs', 'html_report_index_path')
    op.drop_column('test_runs', 'html_report_zip')
