"""recordings

Revision ID: b2afd90f70f0
Revises: 
Create Date: 2024-01-16 20:20:35.334937

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'b2afd90f70f0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'recording',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('transcript_text', sa.Text(), nullable=True),
        sa.Column('transcript_sentences', sa.Column('vector_json', JSONB), nullable=True),
        sa.Column('transcript_words', sa.Column('vector_json', JSONB), nullable=True),
        sa.Column('transcript_id', sa.Text(), nullable=True), # reference ID if using external vendor so we don't re-transcribe
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('media_file_url', sa.Text(), nullable=True),
        sa.Column('media_file_key', sa.Text(), nullable=True),
        sa.Column('media_duration_sec', sa.Numeric(), nullable=True),
        sa.Column('device_id', sa.Text(), nullable=True),
        sa.Column('series_id', sa.Text(), nullable=True),
    )
    op.create_table(
        'recording_annotation',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('device_id', sa.Text(), nullable=True), # TODO: redundant, rmv
        sa.Column('series_id', sa.Text(), nullable=True), # TODO: redundant, rmv
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('data', sa.Column('vector_json', JSONB), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('recording_id', sa.Integer, sa.ForeignKey('recording.id')),
    )


def downgrade() -> None:
    op.drop_table('recording_annotation')
    op.drop_table('recording')
