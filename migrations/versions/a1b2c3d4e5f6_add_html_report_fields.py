"""add optional HTML report fields to test_runs

Revision ID: a1b2c3d4e5f6
Revises: 69ba7fca6275
Create Date: 2026-04-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '69ba7fca6275'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('test_runs', sa.Column('html_report_url', sa.String(), nullable=True))
    op.add_column('test_runs', sa.Column('html_report_html', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('test_runs', 'html_report_html')
    op.drop_column('test_runs', 'html_report_url')
