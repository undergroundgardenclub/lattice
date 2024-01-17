"""device-message

Revision ID: 182661869dba
Revises: b2afd90f70f0
Create Date: 2024-01-16 20:22:09.866759

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '182661869dba'
down_revision = 'b2afd90f70f0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'device_message',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('device_id', sa.Text(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('data', sa.Column('vector_json', JSONB), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table('device_message')

