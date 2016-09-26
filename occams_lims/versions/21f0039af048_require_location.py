"""Require location

Revision ID: 21f0039af048
Revises: 67d641702388
Create Date: 2016-09-20 18:30:36.135475

"""

# revision identifiers, used by Alembic.
revision = '21f0039af048'
down_revision = '67d641702388'
branch_labels = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('specimen', 'location_id', nullable=False)
    op.alter_column('specimen_audit', 'location_id', nullable=False)

    op.drop_constraint('fk_specimen_location_id', 'specimen')
    op.create_foreign_key(
        'fk_specimen_location_id',
        'specimen',
        'location',
        ['location_id'],
        ['id'],
        ondelete='CASCADE'
    )

    specimen_table = sa.sql.table(
        'specimen',
        sa.sql.column('id'),
        sa.sql.column('location_id'),
    )

    aliquot_table = sa.sql.table(
        'aliquot',
        sa.sql.column('id'),
        sa.sql.column('specimen_id'),
        sa.sql.column('location_id'),
    )

    aliquot_audit_table = sa.sql.table(
        'aliquot_audit',
        sa.sql.column('id'),
        sa.sql.column('location_id'),
    )

    # Use the specimen's location if one has not been assigned
    op.execute(
        aliquot_table.update()
        .where(
            (aliquot_table.c.specimen_id == specimen_table.c.id)
            & (aliquot_table.c.location_id == sa.null())
        )
        .values(location_id=specimen_table.c.location_id)
    )

    op.execute(
        aliquot_audit_table.update()
        .where(
            (aliquot_audit_table.c.id == aliquot_table.c.id)
            & (aliquot_audit_table.c.location_id == sa.null())
        )
        .values(location_id=aliquot_table.c.location_id)
    )

    op.alter_column('aliquot', 'location_id', nullable=False)
    op.alter_column('aliquot_audit', 'location_id', nullable=False)
    op.drop_constraint('fk_aliquot_location_id', 'aliquot')
    op.create_foreign_key(
        'fk_aliquot_location_id',
        'aliquot',
        'location',
        ['location_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    pass
