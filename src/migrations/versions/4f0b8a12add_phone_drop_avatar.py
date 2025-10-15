"""add phone_number to user and drop profile_image_url

Revision ID: 4f0b8a12
Revises: 70c95fc199c5
Create Date: 2025-10-15
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f0b8a12'
down_revision = '70c95fc199c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new nullable phone_number column
    op.add_column('user', sa.Column('phone_number', sa.String(length=32), nullable=True))

    # Remove profile_image_url column
    op.drop_column('user', 'profile_image_url')


def downgrade() -> None:
    # Restore profile_image_url column (non-nullable to match original schema)
    op.add_column('user', sa.Column('profile_image_url', sa.String(), nullable=False))

    # Drop phone_number column
    op.drop_column('user', 'phone_number')