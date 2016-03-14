"""Update states

Removes unused states and clarifies labels

Revision ID: 9aadc4a90986
Revises: d73ecb818161
Create Date: 2016-03-09 10:34:25.686504

"""

# revision identifiers, used by Alembic.
revision = '9aadc4a90986'
down_revision = 'd73ecb818161'
branch_labels = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    specimen_table = sa.sql.table(
        'specimen',
        sa.sql.column('state_id')
    )
    specimen_state_table = sa.sql.table(
        'specimenstate',
        sa.sql.column('id'),
        sa.sql.column('name'),
        sa.sql.column('title')
    )
    aliquot_state_table = sa.sql.table(
        'aliquotstate',
        sa.sql.column('id'),
        sa.sql.column('name'),
        sa.sql.column('title')
    )

    # Transition all samples still batched to pending aliquot
    op.execute(
        specimen_table.update()
        .values(
            state_id=(
                sa.select([specimen_state_table.c.id])
                .where(specimen_state_table.c.name == op.inline_literal('pending-aliquot'))))
        .where(
            specimen_table.c.state_id.in_(
                sa.select([specimen_state_table.c.id])
                .where(specimen_state_table.c.name.in_([
                    op.inline_literal('complete'),
                    op.inline_literal('batched'),
                ]))))
    )

    op.execute(
        specimen_state_table.delete()
        .where(specimen_state_table.c.name.in_([
            op.inline_literal(name)
            for name in [
                'complete',
                'batched',
                'postponed',
                'prepared-aliquot',
                'rejected',
            ]
        ]))
    )

    op.execute(
        aliquot_state_table.delete()
        .where(aliquot_state_table.c.name.in_([
            op.inline_literal(name)
            for name in [
                'destroyed',
                'queued',
                'incorrect',
                'hold',
                'prepared',

                'deleted-1',
                'uncertain--4',
                'label-star',
                'richman-plus',
                'unused',
            ]
        ]))
    )

    op.execute(
        aliquot_state_table.update()
        .where(
            aliquot_state_table.c.name == op.inline_literal(u'pending-checkout'))
        .values(title=op.inline_literal(u'Pending Check Out'))
    )


def downgrade():
    pass
