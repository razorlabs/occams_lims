"""Require collect date/time

Revision ID: 67d641702388
Revises: 6b1d8781f453
Create Date: 2016-09-20 17:47:41.354458

"""

# revision identifiers, used by Alembic.
revision = '67d641702388'
down_revision = '6b1d8781f453'
branch_labels = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    for table_name in ('specimen', 'specimen_audit'):
        specimen_table = sa.sql.table(
            table_name,
            sa.sql.column('id'),
            sa.sql.column('collect_date'),
            sa.sql.column('collect_time'),
            sa.sql.column('create_date'),
        )

        op.execute(
            specimen_table.update()
            .where(specimen_table.c.collect_date == sa.null())
            .values(collect_date=specimen_table.c.create_date)
        )

        op.execute(
            specimen_table.update()
            .where(specimen_table.c.collect_time == sa.null())
            .values(collect_time=specimen_table.c.create_date)
        )

    op.alter_column(
        'specimen',
        'collect_date',
        nullable=False,
        server_default=sa.text('CURRENT_TIMESTAMP')
    )

    op.alter_column(
        'specimen',
        'collect_time',
        nullable=False,
        server_default=sa.text('CURRENT_TIMESTAMP')
    )

    op.alter_column(
        'specimen_audit',
        'collect_date',
        nullable=False
    )

    op.alter_column(
        'specimen_audit',
        'collect_time',
        nullable=False,
    )

    for table_name in ('aliquot', 'aliquot_audit'):
        op.alter_column(table_name, 'store_date', new_column_name='collect_date')
        op.add_column(table_name, sa.Column('collect_time', sa.Time))

        aliquot_table = sa.sql.table(
            table_name,
            sa.sql.column('id'),
            sa.sql.column('specimen_id'),
            sa.sql.column('collect_date'),
            sa.sql.column('collect_time'),
            sa.sql.column('create_date'),
            sa.sql.column('modify_date'),
        )

        # Use specimen collection date and times if unassigned

        op.execute(
            aliquot_table.update()
            .where(aliquot_table.c.collect_date == sa.null())
            .values(collect_date=aliquot_table.c.modify_date)
        )

        op.execute(
            aliquot_table.update()
            .where(aliquot_table.c.collect_time == sa.null())
            .values(collect_time=aliquot_table.c.modify_date)
        )

    op.alter_column(
        'aliquot',
        'collect_date',
        nullable=False,
        server_default=sa.text('CURRENT_TIMESTAMP')
    )

    op.alter_column(
        'aliquot',
        'collect_time',
        nullable=False,
        server_default=sa.text('CURRENT_TIMESTAMP')
    )

    op.alter_column(
        'aliquot_audit',
        'collect_date',
        nullable=False,
    )

    op.alter_column(
        'aliquot_audit',
        'collect_time',
        nullable=False,
    )


def downgrade():
    pass
