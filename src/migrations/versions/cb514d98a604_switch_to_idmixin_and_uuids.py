"""switch to IDMixin and UUIDs

Revision ID: cb514d98a604
Revises: 4f0b8a12
Create Date: 2025-10-15 23:28:14.696043

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'cb514d98a604'
down_revision: Union[str, None] = '4f0b8a12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### custom migration to rebuild tables with UUID keys ###
    # Drop dependent tables first to avoid type cast issues
    with op.batch_alter_table('permission', schema=None) as batch_op:
        pass
    op.drop_table('permission')

    with op.batch_alter_table('user_role', schema=None) as batch_op:
        pass
    op.drop_table('user_role')

    with op.batch_alter_table('post', schema=None) as batch_op:
        pass
    op.drop_table('post')

    with op.batch_alter_table('rate_limit', schema=None) as batch_op:
        pass
    op.drop_table('rate_limit')

    # Drop base tables
    with op.batch_alter_table('user', schema=None) as batch_op:
        pass
    op.drop_table('user')

    with op.batch_alter_table('tier', schema=None) as batch_op:
        pass
    op.drop_table('tier')

    with op.batch_alter_table('role', schema=None) as batch_op:
        pass
    op.drop_table('role')

    # Re-create base tables with UUID primary keys
    op.create_table(
        'role',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_name'), 'role', ['name'], unique=True)

    op.create_table(
        'tier',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'user',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=30), nullable=False),
        sa.Column('username', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=50), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('phone_number', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('tier_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['tier_id'], ['tier.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_tier_id'), 'user', ['tier_id'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)

    op.create_table(
        'rate_limit',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tier_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('limit', sa.Integer(), nullable=False),
        sa.Column('period', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tier_id'], ['tier.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_rate_limit_tier_id'), 'rate_limit', ['tier_id'], unique=False)

    op.create_table(
        'permission',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('permission_name', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('role_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['role.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('permission_name', 'role_id', name='uq_permission_role'),
        sa.UniqueConstraint('permission_name', 'user_id', name='uq_permission_user')
    )
    op.create_index(op.f('ix_permission_permission_name'), 'permission', ['permission_name'], unique=False)
    op.create_index(op.f('ix_permission_role_id'), 'permission', ['role_id'], unique=False)
    op.create_index(op.f('ix_permission_user_id'), 'permission', ['user_id'], unique=False)

    op.create_table(
        'post',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_by_user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=30), nullable=False),
        sa.Column('text', sa.String(length=63206), nullable=False),
        sa.Column('media_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_post_created_by_user_id'), 'post', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_post_is_deleted'), 'post', ['is_deleted'], unique=False)

    # Token blacklist was dropped earlier and is not part of the current models
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user_role', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('user_role', 'role_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('user_role', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.add_column('user', sa.Column('uuid', sa.UUID(), autoincrement=False, nullable=False))
    op.create_unique_constraint(op.f('user_uuid_key'), 'user', ['uuid'], postgresql_nulls_not_distinct=False)
    op.create_index(op.f('ix_user_is_deleted'), 'user', ['is_deleted'], unique=False)
    op.alter_column('user', 'deleted_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True)
    op.alter_column('user', 'updated_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True)
    op.alter_column('user', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)
    op.alter_column('user', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('user', 'tier_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.alter_column('tier', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False,
               existing_server_default=sa.text("nextval('tier_id_seq'::regclass)"))
    op.alter_column('role', 'updated_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True)
    op.alter_column('role', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)
    op.alter_column('role', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False,
               existing_server_default=sa.text("nextval('role_id_seq'::regclass)"))
    op.alter_column('rate_limit', 'updated_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True)
    op.alter_column('rate_limit', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)
    op.alter_column('rate_limit', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('rate_limit', 'tier_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.add_column('post', sa.Column('uuid', sa.UUID(), autoincrement=False, nullable=False))
    op.create_unique_constraint(op.f('post_uuid_key'), 'post', ['uuid'], postgresql_nulls_not_distinct=False)
    op.create_index(op.f('ix_post_is_deleted'), 'post', ['is_deleted'], unique=False)
    op.alter_column('post', 'deleted_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True)
    op.alter_column('post', 'updated_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True)
    op.alter_column('post', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)
    op.alter_column('post', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('post', 'created_by_user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('permission', 'updated_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True)
    op.alter_column('permission', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)
    op.alter_column('permission', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('permission', 'role_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.alter_column('permission', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.create_table('token_blacklist',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('token', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('expires_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('token_blacklist_pkey'))
    )
    op.create_index(op.f('ix_token_blacklist_token'), 'token_blacklist', ['token'], unique=True)
    # ### end Alembic commands ###
