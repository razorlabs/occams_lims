"""Remove labbok column

Revision ID: 6b1d8781f453
Revises: 849666a56cd7
Create Date: 2016-09-20 17:06:53.740507

"""

# revision identifiers, used by Alembic.
revision = '6b1d8781f453'
down_revision = '849666a56cd7'
branch_labels = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('aliquot', 'labbook')
    op.drop_column('aliquot_audit', 'labbook')


def downgrade():
    pass
