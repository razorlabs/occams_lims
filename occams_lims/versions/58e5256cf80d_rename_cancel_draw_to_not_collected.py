"""Rename cancel draw to not collected

Revision ID: 58e5256cf80d
Revises: None
Create Date: 2016-09-28 16:10:14.091050

"""

# revision identifiers, used by Alembic.
revision = '58e5256cf80d'
down_revision = None
branch_labels = None

from alembic import op
import sqlalchemy as sa


def upgrade():

    specimen_state_table = sa.sql.table(
        'specimenstate',
        sa.sql.column('name'),
        sa.sql.column('title')
    )

    op.execute(
        specimen_state_table.update()
        .where(specimen_state_table.c.name == op.inline_literal('cancel-draw'))
        .values(
            name=op.inline_literal('not-collected'),
            title=op.inline_literal('Not Collected')
        )
    )


def downgrade():
    pass
