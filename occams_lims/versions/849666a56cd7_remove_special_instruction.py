"""Remove 'Special Instruction'

Revision ID: 849666a56cd7
Revises: 9aadc4a90986
Create Date: 2016-09-09 09:20:15.005059

"""

# revision identifiers, used by Alembic.
revision = '849666a56cd7'
down_revision = '9aadc4a90986'
branch_labels = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('aliquot', 'special_instruction_id')
    op.drop_table('specialinstruction')


def downgrade():
    pass
