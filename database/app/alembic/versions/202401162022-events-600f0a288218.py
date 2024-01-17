"""events

Revision ID: 600f0a288218
Revises: 182661869dba
Create Date: 2024-01-16 20:22:49.223215

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '600f0a288218'
down_revision = '182661869dba'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'event',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('data', sa.Column('vector_json', JSONB), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('device_id', sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('event')
