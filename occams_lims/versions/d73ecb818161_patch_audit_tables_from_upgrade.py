"""Patch audit tables from upgrade

Revision ID: d73ecb818161
Revises: 7739dda4276
Create Date: 2016-01-19 14:28:12.177603

"""

# revision identifiers, used by Alembic.
revision = 'd73ecb818161'
down_revision = '7739dda4276'
branch_labels = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    """
    Patch the audit table to include the amount column.
    This is the exact logic as the previous version, but for the corresponding
    audit table, since we forgot it.
    """
    op.add_column('aliquot_audit', sa.Column('amount', sa.Numeric()))

    aliquot_type_table = sa.sql.table(
        'aliquottype',
        sa.sql.column('id'),
        sa.sql.column('name'),
        sa.sql.column('units'))

    aliquot_audit_table = sa.sql.table(
        'aliquot_audit',
        sa.sql.column('aliquot_type_id'),
        sa.sql.column('cell_amount'),
        sa.sql.column('volume'),
        sa.sql.column('amount'))

    types = {
        'cell_amount': {
            'units': op.inline_literal(u'x10^6'),
            'column': aliquot_audit_table.c.cell_amount,
        },
        'volume': {
            'units': op.inline_literal(u'mL'),
            'column': aliquot_audit_table.c.volume,
        },
        'each': {
            'units': op.inline_literal(u'ea'),
            'column': sa.case([
                ((aliquot_audit_table.c.cell_amount > op.inline_literal(0)),
                    aliquot_audit_table.c.cell_amount),
                ((aliquot_audit_table.c.volume > op.inline_literal(0)),
                    aliquot_audit_table.c.volume)
            ])

        },
    }

    columns = {
        u'blood-spot': types['each'],
        u'csf': types['volume'],
        u'csfpellet': types['each'],
        u'gscells': types['cell_amount'],
        u'gsplasma': types['volume'],
        u'heparin-plasma': types['volume'],
        u'lymphoid': types['each'],
        u'pbmc': types['cell_amount'],
        u'plasma': types['volume'],
        u'rs-gut': types['each'],
        u'serum': types['volume'],
        u'swab': types['each'],
        u'ti-gut': types['each'],
        u'urine': types['volume'],
        u'wb-plasma': types['volume'],
        u'whole-blood': types['volume'],
    }

    op.execute(
        aliquot_type_table.update()
        .values(
            units=sa.case(value=aliquot_type_table.c.name, whens=[
                (column_name, type_['units'])
                for column_name, type_ in columns.items()
            ], else_=sa.null()))
    )

    op.execute(
        aliquot_audit_table.update()
        .where(
            aliquot_type_table.c.id == aliquot_audit_table.c.aliquot_type_id)
        .values(
            # Using the units of measure, pull in the correct value
            amount=sa.case(value=aliquot_type_table.c.name, whens=[
                (column_name, type_['column'])
                for column_name, type_ in columns.items()
            ], else_=sa.null()))
    )

    op.alter_column('aliquottype', 'units', nullable=False)
    op.drop_column('aliquot_audit', 'cell_amount')
    op.drop_column('aliquot_audit', 'volume')


def downgrade():
    pass
