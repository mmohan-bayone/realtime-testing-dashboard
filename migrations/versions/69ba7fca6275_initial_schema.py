"""initial schema

Revision ID: 69ba7fca6275
Revises: 
Create Date: 2026-03-26 23:28:10.973944

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69ba7fca6275'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'test_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('suite_name', sa.String(), nullable=False),
        sa.Column('environment', sa.String(), nullable=False),
        sa.Column('build_version', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='RUNNING'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_test_runs_id'), 'test_runs', ['id'], unique=False)
    op.create_index(op.f('ix_test_runs_environment'), 'test_runs', ['environment'], unique=False)
    op.create_index(op.f('ix_test_runs_suite_name'), 'test_runs', ['suite_name'], unique=False)

    op.create_table(
        'test_case_results',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('run_id', sa.Integer(), sa.ForeignKey('test_runs.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('module', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('defect_id', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index(op.f('ix_test_case_results_id'), 'test_case_results', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_test_case_results_id'), table_name='test_case_results')
    op.drop_table('test_case_results')
    op.drop_index(op.f('ix_test_runs_suite_name'), table_name='test_runs')
    op.drop_index(op.f('ix_test_runs_environment'), table_name='test_runs')
    op.drop_index(op.f('ix_test_runs_id'), table_name='test_runs')
    op.drop_table('test_runs')
