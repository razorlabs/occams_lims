from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    """
    Adds the site_lab_location_table for determining which location
    a given patient's specimen should be sent.
    Also adds badly needed indexes
    """
    metadata = MetaData(migrate_engine)
    site_table = Table(u'site', metadata, autoload=True)
    location_table = Table(u'location', metadata, autoload=True)
    specimen_type_table = Table(u'specimentype', metadata, autoload=True)
    aliquot_type_table = Table(u'aliquottype', metadata, autoload=True)
    specimen_table = Table(u'specimen', metadata, autoload=True)
    aliquot_table = Table(u'aliquot', metadata, autoload=True)

    site_lab_location_table = Table('site_lab_location', metadata,
        Column('site_id', Integer,
        ForeignKey(
            site_table.c.id,
            name='fk_site_lab_location_site_id',
            ondelete='CASCADE',),
        primary_key=True
        ),
        Column('location_id', Integer,
        ForeignKey(
            location_table.c.id,
            name='fk_site_lab_location_location_id',
            ondelete='CASCADE',),
        primary_key=True
        ),
    )

    ix_specimen_specimen_type_index = Index('ix_specimen_specimen_type_id', specimen_table.c.specimen_type_id)
    ix_specimen_patient_index = Index('ix_specimen_patient_id', specimen_table.c.patient_id)
    ix_specimen_cycle_index = Index('ix_specimen_cycle_id', specimen_table.c.cycle_id)
    ix_specimen_location_index = Index('ix_specimen_location_id', specimen_table.c.location_id)
    ix_specimen_state_index = Index('ix_specimen_state_id', specimen_table.c.state_id)

    ix_aliquot_specimen_index = Index('ix_aliquot_specimen_id', aliquot_table.c.specimen_id)
    ix_aliquot_aliquot_type_index = Index('ix_aliquot_aliquot_type_id', aliquot_table.c.aliquot_type_id)
    ix_aliquot_location_index = Index('ix_aliquot_location_id', aliquot_table.c.location_id)
    ix_aliquot_state_index = Index('ix_aliquot_state_id', aliquot_table.c.state_id)

    site_lab_location_table.create(migrate_engine)
    specimen_type_table.c.location_id.drop()
    aliquot_type_table.c.location_id.drop()
    specimen_table.c.study_cycle_label.drop()


    ix_specimen_specimen_type_index.drop()
    ix_specimen_patient_index.drop()
    ix_specimen_cycle_index.drop()
    ix_specimen_location_index.drop()
    ix_specimen_state_index.drop()

    ix_aliquot_specimen_index.drop()
    ix_aliquot_aliquot_type_index.drop()
    ix_aliquot_location_index.drop()
    ix_aliquot_state_index.drop()

    ix_specimen_specimen_type_index.create()
    ix_specimen_patient_index.create()
    ix_specimen_cycle_index.create()
    ix_specimen_location_index.create()
    ix_specimen_state_index.create()

    ix_aliquot_specimen_index.create()
    ix_aliquot_aliquot_type_index.create()
    ix_aliquot_location_index.create()
    ix_aliquot_state_index.create()

def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)

    site_location_table = Table('site_lab_location', metadata, autoload=True)
    specimen_type_table = Table(u'specimentype', metadata, autoload=True)
    aliquot_type_table = Table(u'aliquottype', metadata, autoload=True)
    location_table = Table(u'location', metadata, autoload=True)
    specimen_table = Table(u'specimen', metadata, autoload=True)
    aliquot_table = Table(u'aliquot', metadata, autoload=True)

    location_column = Column('location_id', Integer)

    site_location_table.drop()
    location_column.create(specimen_type_table)
    location_column.create(aliquot_type_table)

    aliquottype_location_fk =  ForeignKeyConstraint([aliquot_type_table.c.location_id], [location_table.c.id], name='fk_aliquottype_location_id', ondelete='SET NULL')
    specimentype_location_fk =  ForeignKeyConstraint([specimen_type_table.c.location_id], [location_table.c.id], name='fk_specimentype_location_id', ondelete='SET NULL')

    aliquottype_location_fk.create()
    specimentype_location_fk.create()

    ix_specimen_specimen_type_index = Index('ix_specimen_specimen_type_id', specimen_table.c.specimen_type_id)
    ix_specimen_patient_index = Index('ix_specimen_patient_id', specimen_table.c.patient_id)
    ix_specimen_cycle_index = Index('ix_specimen_cycle_id', specimen_table.c.cycle_id)
    ix_specimen_location_index = Index('ix_specimen_location_id', specimen_table.c.location_id)
    ix_specimen_state_index = Index('ix_specimen_state_id', specimen_table.c.state_id)

    ix_aliquot_specimen_index = Index('ix_aliquot_specimen_id', aliquot_table.c.specimen_id)
    ix_aliquot_aliquot_type_index = Index('ix_aliquot_aliquot_type_id', aliquot_table.c.aliquot_type_id)
    ix_aliquot_location_index = Index('ix_aliquot_location_id', aliquot_table.c.location_id)
    ix_aliquot_state_index = Index('ix_aliquot_state_id', aliquot_table.c.state_id)


    ix_specimen_specimen_type_index.drop()
    ix_specimen_patient_index.drop()
    ix_specimen_cycle_index.drop()
    ix_specimen_location_index.drop()
    ix_specimen_state_index.drop()

    ix_aliquot_specimen_index.drop()
    ix_aliquot_aliquot_type_index.drop()
    ix_aliquot_location_index.drop()
    ix_aliquot_state_index.drop()

