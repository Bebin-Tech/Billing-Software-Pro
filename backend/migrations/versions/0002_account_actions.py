"""Single-use password recovery and email verification.

Revision ID: 0002
"""
from alembic import op
import sqlalchemy as sa

revision='0002'
down_revision='0001'


def upgrade():
    op.add_column('users',sa.Column('email_verified',sa.Boolean(),nullable=False,server_default=sa.false()))
    for name in ['password_reset_tokens','email_verification_tokens']:
        op.create_table(name,sa.Column('id',sa.Integer(),primary_key=True),
            sa.Column('created_at',sa.DateTime(),nullable=False),sa.Column('updated_at',sa.DateTime(),nullable=False),
            sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id'),nullable=False),
            sa.Column('token_hash',sa.String(64),unique=True,nullable=False),
            sa.Column('expires_at',sa.DateTime(),nullable=False),sa.Column('used',sa.Boolean(),nullable=False))
        op.create_index(f'ix_{name}_user_id',name,['user_id'])


def downgrade():
    op.drop_table('email_verification_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_column('users','email_verified')
