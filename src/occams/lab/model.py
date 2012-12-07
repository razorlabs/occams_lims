""" Lab Models
"""

from sqlalchemy import text
from sqlalchemy import types
from sqlalchemy import schema
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import event

import zope.interface
from occams.lab import interfaces
from occams.datastore.model import ModelClass
from occams.datastore.model.metadata import AutoNamed
from occams.datastore.model.metadata import Describeable
from occams.datastore.model.metadata import Referenceable
from occams.datastore.model.metadata import Modifiable
from occams.datastore.model.auditing import Auditable

from avrc.aeh.model import *

LabModel = ModelClass(u'LabModel')

NOW = text('CURRENT_TIMESTAMP')

__all__ = (
           'specimentype_study_table',
           'specimentype_cycle_table',
           'site_lab_location_table',
           'SpecimenState',
           'AliquotState',
           'Location',
           'SpecialInstruction',
           'SpecimenType',
           'AliquotType',
           'Specimen',
           'Aliquot'
           )


specimentype_study_table = schema.Table('specimentype_study', LabModel.metadata,
    schema.Column(
        'study_id',
        types.Integer,
        schema.ForeignKey(Study.id, name='fk_specimentype_study_study_id', ondelete='CASCADE',),
        primary_key=True
        ),
    schema.Column(
        'specimentype_id',
         types.Integer,
         schema.ForeignKey('specimentype.id', name='fk_specimentype_study_specimentype_id', ondelete='CASCADE',),
         primary_key=True
         ),
    )

specimentype_cycle_table = schema.Table('specimentype_cycle', LabModel.metadata,
    schema.Column(
        'cycle_id',
        types.Integer,
        schema.ForeignKey(Cycle.id, name='fk_specimentype_cycle_cycle_id', ondelete='CASCADE',),
        primary_key=True
        ),
    schema.Column(
        'specimentype_id',
         types.Integer,
         schema.ForeignKey('specimentype.id', name='fk_specimentype_cycle_specimentype_id', ondelete='CASCADE',),
         primary_key=True
         ),
    )

site_lab_location_table = schema.Table('site_lab_location', LabModel.metadata,
    schema.Column(
        'site_id',
        types.Integer,
        schema.ForeignKey(Site.id, name='fk_site_lab_location_site_id', ondelete='CASCADE',),
        primary_key=True
        ),
     schema.Column(
        'location_id',
        types.Integer,
        schema.ForeignKey('location.id', name='fk_site_lab_location_location_id', ondelete='CASCADE',),
        ),
    )

class SpecimenState(LabModel, AutoNamed, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the destination, such as address, contact info, etc.
    Right now we just need a vocabulary
    """
    zope.interface.implements(interfaces.IOccamsVocabulary)

    @declared_attr
    def __table_args__(cls):
        return (
            schema.UniqueConstraint('name'),
            )

class AliquotState(LabModel, AutoNamed, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the destination, such as address, contact info, etc.
    Right now we just need a vocabulary
    """
    zope.interface.implements(interfaces.IOccamsVocabulary)

    @declared_attr
    def __table_args__(cls):
        return (
            schema.UniqueConstraint('name'),
            )

class Location(LabModel, AutoNamed, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the destination, such as address, contact info, etc.
    Right now we just need a vocabulary
    """
    zope.interface.implements(interfaces.IOccamsVocabulary)

    sites = orm.relationship(
        Site,
        secondary=site_lab_location_table,
        backref=orm.backref(
            name='lab_location',
            uselist=False
            ),
        )

    @declared_attr
    def __table_args__(cls):
        return (
            schema.UniqueConstraint('name'),
            )

class SpecialInstruction(LabModel, AutoNamed, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the special instruction
    Right now we just need a vocabulary
    """
    zope.interface.implements(interfaces.IOccamsVocabulary)

    @declared_attr
    def __table_args__(cls):
        return (
            schema.UniqueConstraint('name'),
            )

class SpecimenType(LabModel, AutoNamed, Referenceable, Describeable, Modifiable):
    zope.interface.implements(interfaces.ISpecimenType)

    __doc__ = interfaces.ISpecimenType.__doc__

    tube_type = schema.Column(types.Unicode)

    default_tubes = schema.Column(types.Integer)

    studies = orm.relationship(
        Study,
        secondary=specimentype_study_table,
        collection_class=set,
        backref=orm.backref(
            name='specimen_types',
            collection_class=set,
            )
        )
    cycles = orm.relationship(
        Cycle,
        secondary=specimentype_cycle_table,
        collection_class=set,
        backref=orm.backref(
            name='specimen_types',
            collection_class=set,
            )
        )

    # aliquot_types backreffed in AliquotType

class AliquotType(LabModel, AutoNamed,Referenceable, Describeable, Modifiable):
    zope.interface.implements(interfaces.IAliquotType)

    __doc__ = interfaces.IAliquotType.__doc__

    specimen_type_id = schema.Column(types.Integer, nullable=False)

    specimen_type = orm.relationship(
            SpecimenType,
            backref=orm.backref(
                name='aliquot_types',
                primaryjoin='SpecimenType.id == AliquotType.specimen_type_id',
                collection_class=orm.collections.attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(specimen_type_id == SpecimenType.id)
            )

    @declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=['specimen_type_id'],
                refcolumns=['specimentype.id'],
                name='fk_%s_specimentype_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.UniqueConstraint('specimen_type_id', 'name'),
            schema.Index('ix_%s_specimen_type_id' % cls.__tablename__, 'specimen_type_id'),
            )

class Specimen(LabModel, AutoNamed, Referenceable, Auditable, Modifiable):
    zope.interface.implements(interfaces.ISpecimen)

    __doc__ = interfaces.ISpecimen.__doc__

    specimen_type_id = schema.Column(types.Integer, nullable=False)

    specimen_type = orm.relationship(
            SpecimenType,
            backref=orm.backref(
                name='specimen',
                primaryjoin='SpecimenType.id == Specimen.specimen_type_id',
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(specimen_type_id == SpecimenType.id)
            )

    patient_id = schema.Column(types.Integer, nullable=False)

    patient = orm.relationship(
            Patient,
            backref=orm.backref(
                name='specimen',
                primaryjoin='Patient.id==Specimen.patient_id',
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(patient_id==Patient.id)
            )

    cycle_id = schema.Column(types.Integer)

    cycle = orm.relationship(
            Cycle,
            backref=orm.backref(
                name='specimen',
                primaryjoin='Cycle.id==Specimen.cycle_id',
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(cycle_id==Cycle.id)
            )

    state_id = schema.Column(
            types.Integer,
            nullable=False
            )

    state = orm.relationship(
            SpecimenState,
            primaryjoin=(state_id==SpecimenState.id)
            )

    collect_date = schema.Column(types.Date)

    collect_time = schema.Column(types.Time)

    location_id = schema.Column(types.Integer)

    location = orm.relationship(
            Location,
            backref=orm.backref(
                name='specimen',
                primaryjoin='Location.id==Specimen.location_id',
                ),
            primaryjoin=(location_id==Location.id)
            )

    previous_location_id = schema.Column(types.Integer)

    previous_location = orm.relationship(
            Location,
            backref=orm.backref(
                name='previous_specimen',
                primaryjoin='Location.id==Specimen.previous_location_id',
                ),
            primaryjoin=(previous_location_id==Location.id)
            )

    tubes = schema.Column(types.Integer)

    notes = schema.Column(types.Unicode)

    @declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=['specimen_type_id'],
                refcolumns=['specimentype.id'],
                name='fk_%s_specimentype_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=[Patient.id],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            schema.ForeignKeyConstraint(
                columns=['cycle_id'],
                refcolumns=[Cycle.id],
                name='fk_%s_cycle_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            schema.ForeignKeyConstraint(
                columns=['location_id'],
                refcolumns=['location.id'],
                name='fk_%s_location_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
           schema.ForeignKeyConstraint(
                columns=['previous_location_id'],
                refcolumns=['location.id'],
                name='fk_%s_previous_location_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            schema.ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['specimenstate.id'],
                name='fk_%s_specimenstate_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            schema.Index('ix_%s_specimen_type_id' % cls.__tablename__, 'specimen_type_id'),
            schema.Index('ix_%s_patient_id' % cls.__tablename__, 'patient_id'),
            schema.Index('ix_%s_cycle_id' % cls.__tablename__, 'cycle_id'),
            schema.Index('ix_%s_location_id' % cls.__tablename__, 'location_id'),
            schema.Index('ix_%s_previous_location_id' % cls.__tablename__, 'previous_location_id'),
            schema.Index('ix_%s_state_id' % cls.__tablename__, 'state_id'),
            )


# event.listen(
#     Specimen.location_id,
#     'set',
#     lambda t, v, o, i: setattr(t, 'previous_location_id', o)
#     )

class Aliquot(LabModel, AutoNamed, Referenceable, Auditable, Modifiable):
    zope.interface.implements(interfaces.IAliquot)

    __doc__ = interfaces.IAliquot.__doc__

    specimen_id = schema.Column(types.Integer, nullable=False)

    specimen = orm.relationship(
            Specimen,
            backref=orm.backref(
                name='aliquot',
                primaryjoin='Specimen.id == Aliquot.specimen_id',
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(specimen_id == Specimen.id)
            )

    aliquot_type_id = schema.Column(types.Integer, nullable=False)

    aliquot_type = orm.relationship(
            AliquotType,
            backref=orm.backref(
                name='aliquot',
                primaryjoin='AliquotType.id == Aliquot.aliquot_type_id',
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(aliquot_type_id == AliquotType.id)
            )

    state_id = schema.Column(
            types.Integer,
            nullable=False
            )

    state = orm.relationship(
            AliquotState,
            primaryjoin=(state_id==AliquotState.id)
            )

    labbook = schema.Column(types.Unicode)

    volume = schema.Column(types.Float)

    cell_amount = schema.Column(types.Float)

    store_date = schema.Column(types.Date)

    freezer = schema.Column(types.Unicode)

    rack = schema.Column(types.Unicode)

    box = schema.Column(types.Unicode)

    location_id = schema.Column(types.Integer)

    location = orm.relationship(
            Location,
            backref=orm.backref(
                name='aliquot',
                primaryjoin='Aliquot.location_id == Location.id',
                ),
            primaryjoin=(location_id==Location.id)
            )

    previous_location_id = schema.Column(types.Integer)

    previous_location = orm.relationship(
            Location,
            backref=orm.backref(
                name='stored_aliquot',
                primaryjoin='Aliquot.previous_location_id == Location.id',
                ),
            primaryjoin=(previous_location_id==Location.id)
            )

    thawed_num = schema.Column(types.Integer)

    inventory_date = schema.Column(types.Date)

    sent_date = schema.Column(types.Date)

    sent_name = schema.Column(types.Unicode)

    sent_notes = schema.Column(types.Unicode)

    notes = schema.Column(types.Unicode)

    special_instruction_id = schema.Column(types.Integer)

    special_instruction = orm.relationship(
            SpecialInstruction,
            primaryjoin=(special_instruction_id == SpecialInstruction.id)
            )


    @declared_attr
    def __table_args__(cls):
        return (
            schema.ForeignKeyConstraint(
                columns=['specimen_id'],
                refcolumns=['specimen.id'],
                name='fk_%s_specimen_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),

            schema.ForeignKeyConstraint(
                columns=['aliquot_type_id'],
                refcolumns=['aliquottype.id'],
                name='fk_%s_aliquottype_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),

            schema.ForeignKeyConstraint(
                columns=['location_id'],
                refcolumns=['location.id'],
                name='fk_%s_location_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),


            schema.ForeignKeyConstraint(
                columns=['previous_location_id'],
                refcolumns=['location.id'],
                name='fk_%s_previous_location_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),

            schema.ForeignKeyConstraint(
                columns=['special_instruction_id'],
                refcolumns=['specialinstruction.id'],
                name='fk_%s_specialinstruction_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            schema.ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['aliquotstate.id'],
                name='fk_%s_aliquotstate_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            schema.Index('ix_%s_specimen_id' % cls.__tablename__, 'specimen_id'),
            schema.Index('ix_%s_aliquot_type_id' % cls.__tablename__, 'aliquot_type_id'),
            schema.Index('ix_%s_location_id' % cls.__tablename__, 'location_id'),
            schema.Index('ix_%s_previous_location_id' % cls.__tablename__, 'previous_location_id'),
            schema.Index('ix_%s_state_id' % cls.__tablename__, 'state_id'),
            )

# event.listen(
#     Aliquot.location_id,
#     'set',
#     lambda t, v, o, i: setattr(t, 'previous_location_id', o)
#     )

if __name__ == '__main__': # pragma: no cover
    import sqlalchemy
    # A convenient way for checking the model even correctly loads the tables
    LabModel.metadata.create_all(bind=sqlalchemy.create_engine('sqlite://', echo=True))
