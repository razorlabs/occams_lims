"""Add lims box row and column

Revision ID: e5bb162d0fda
Revises: 21f0039af048
Create Date: 2018-01-25 13:30:27.230330

"""

# revision identifiers, used by Alembic.
revision = 'e5bb162d0fda'
down_revision = '21f0039af048'
branch_labels = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    """
    Add box_row and box_column to aliquot and aliquot audit for box reference
    """

    op.add_column('aliquot', sa.Column('box_row', sa.Unicode()))
    op.add_column('aliquot', sa.Column('box_column', sa.Unicode()))

    op.add_column('aliquot_audit', sa.Column('box_row', sa.Unicode()))
    op.add_column('aliquot_audit', sa.Column('box_column', sa.Unicode()))

def downgrade():

    op.drop_column('aliquot', 'box_row')
    op.drop_column('aliquot', 'box_column')
    op.drop_column('aliquot_audit', 'box_row')
    op.drop_column('aliquot_audit', 'box_column')

