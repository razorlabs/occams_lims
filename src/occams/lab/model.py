""" Lab Models
"""

from sqlalchemy import text
from sqlalchemy.orm import relation as Relationship
from sqlalchemy.orm import backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKey
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import Date
from sqlalchemy.types import Enum
from sqlalchemy.types import Float
from sqlalchemy.types import Integer
from sqlalchemy.types import Time
from sqlalchemy.types import Unicode
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import Index
from sqlalchemy.schema import Table

import zope.interface
from occams.lab import interfaces
from occams.datastore.model import Model
from occams.datastore.model.metadata import AutoNamed
from occams.datastore.model.metadata import Describeable
from occams.datastore.model.metadata import Referenceable
from occams.datastore.model.metadata import Modifiable
from occams.datastore.model.auditing import Auditable
# from occams.lab.interfaces import ISpecimen
# from occams.lab.interfaces import IAliquot

from avrc.aeh.model import *


NOW = text('CURRENT_TIMESTAMP')

specimentype_study_table = Table('specimentype_study', Model.metadata,
    Column(
        'study_id',
        Integer,
        ForeignKey('study.id', name='fk_specimentype_study_study_id', ondelete='CASCADE',),
        primary_key=True
        ),
    Column(
        'specimentype_id',
         Integer,
         ForeignKey('specimentype.id', name='fk_specimentype_study_specimentype_id', ondelete='CASCADE',),
         primary_key=True
         ),
    )

specimentype_cycle_table = Table('specimentype_cycle', Model.metadata,
    Column(
        'cycle_id',
        Integer,
        ForeignKey('cycle.id', name='fk_specimentype_cycle_cycle_id', ondelete='CASCADE',),
        primary_key=True
        ),
    Column(
        'specimentype_id',
         Integer,
         ForeignKey('specimentype.id', name='fk_specimentype_cycle_specimentype_id', ondelete='CASCADE',),
         primary_key=True
         ),
    )


class SpecimenState(Model, AutoNamed, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the destination, such as address, contact info, etc.
    Right now we just need a vocabulary
    """
    zope.interface.implements(interfaces.IOccamsVocabulary)

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name'),
            )

class AliquotState(Model, AutoNamed, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the destination, such as address, contact info, etc.
    Right now we just need a vocabulary
    """
    zope.interface.implements(interfaces.IOccamsVocabulary)

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name'),
            )

class Location(Model, AutoNamed, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the destination, such as address, contact info, etc.
    Right now we just need a vocabulary
    """
    zope.interface.implements(interfaces.IOccamsVocabulary)

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name'),
            )

class SpecialInstruction(Model, AutoNamed, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the special instruction
    Right now we just need a vocabulary
    """
    zope.interface.implements(interfaces.IOccamsVocabulary)

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name'),
            )

class SpecimenType(Model, AutoNamed, Referenceable, Describeable, Modifiable):
    """
    """
    zope.interface.implements(interfaces.ISpecimenType)

    ## Tube type always matches the specimen type
    tube_type = Column(Unicode)

    default_tubes = Column(Integer)

    location_id = Column(Integer)

    location = Relationship(
            Location,
            primaryjoin=(location_id==Location.id)
            )

    studies = Relationship(
        Study,
        secondary=specimentype_study_table,
        collection_class=set,
        backref=backref(
            name='specimen_types',
            collection_class=set,
            )
        )
    cycles = Relationship(
        Cycle,
        secondary=specimentype_cycle_table,
        collection_class=set,
        backref=backref(
            name='specimen_types',
            collection_class=set,
            )
        )

    # aliquot_types backreffed in AliquotType

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['location_id'],
                refcolumns=['location.id'],
                name='fk_%s_location_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            UniqueConstraint('name'),
            )

class AliquotType(Model, AutoNamed,Referenceable, Describeable, Modifiable):
    """
    """
    zope.interface.implements(interfaces.IAliquotType)

    specimen_type_id = Column(Integer, nullable=False)

    specimen_type = Relationship(
            SpecimenType,
            backref=backref(
                name='aliquot_types',
                primaryjoin='SpecimenType.id == AliquotType.specimen_type_id',
                collection_class=attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(specimen_type_id == SpecimenType.id)
            )

    location_id = Column(Integer)

    location = Relationship(
            Location,
            primaryjoin=(location_id==Location.id)
            )

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['specimen_type_id'],
                refcolumns=['specimentype.id'],
                name='fk_%s_specimentype_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            ForeignKeyConstraint(
                columns=['location_id'],
                refcolumns=['location.id'],
                name='fk_%s_location_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            UniqueConstraint('specimen_type_id', 'name'),
            )

class Specimen(Model, AutoNamed, Referenceable, Auditable, Modifiable):
    """ Speccialized table for specimen data. Note that only one specimen can be
        drawn from a patient/protocol/type.

        Attributes:
            id: (int) machine generated primary key
            subject_id: (int) reference to the subject this specimen was
                drawn from
            subject: (object) the relation to the subject
            protocol_id: (int) reference to the protocol this specimen was
                drawn for
            protocol: (object) the relation to the protocol
            state: (str) current state of the specimen
            collect_date: (datetime) the date/time said specimen was collected
            type: (str) the type of specimen
            destination: (str) the destination of where the specimen is sent to.
            tubes: (int) number of tubes collected (optional, if applicable)
            volume_per_tube: (int) volume of each tube (optional, if applicable)
            notes: (str) optinal notes that can be entered by users (optional)
            aliquot: (list) convenience relation to the aliquot parts generated
                from this speciemen
    """
    zope.interface.implements(interfaces.ISpecimen)

    specimen_type_id = Column(Integer, nullable=False)

    specimen_type = Relationship(
            SpecimenType,
            backref=backref(
                name='specimen',
                primaryjoin='SpecimenType.id == Specimen.specimen_type_id',
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(specimen_type_id == SpecimenType.id)
            )

    patient_id = Column(Integer, nullable=False)

    patient = Relationship(
            Patient,
            backref=backref(
                name='specimen',
                primaryjoin='Patient.id==Specimen.patient_id',
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(patient_id==Patient.id)
            )

    cycle_id = Column(Integer)

    cycle = Relationship(
            Cycle,
            backref=backref(
                name='specimen',
                primaryjoin='Cycle.id==Specimen.cycle_id',
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(cycle_id==Cycle.id)
            )

    state_id = Column(
            Integer,
            nullable=False
            )

    state = Relationship(
            SpecimenState,
            primaryjoin=(state_id==SpecimenState.id)
            )

    collect_date = Column(Date)

    collect_time = Column(Time)

    location_id = Column(Integer)

    location = Relationship(
            Location,
            backref=backref(
                name='specimen',
                primaryjoin='Location.id==Specimen.location_id',
                ),
            primaryjoin=(location_id==Location.id)
            )

    tubes = Column(Integer)

    notes = Column(Unicode)

    study_cycle_label = Column(Unicode(255))

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['specimen_type_id'],
                refcolumns=['specimentype.id'],
                name='fk_%s_specimentype_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=['patient.id'],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            ForeignKeyConstraint(
                columns=['cycle_id'],
                refcolumns=['cycle.id'],
                name='fk_%s_cycle_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            ForeignKeyConstraint(
                columns=['location_id'],
                refcolumns=['location.id'],
                name='fk_%s_location_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['specimenstate.id'],
                name='fk_%s_specimenstate_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            # UniqueConstraint('patient_id', 'cycle_id', 'specimen_type_id'),
            )

class Aliquot(Model, AutoNamed, Referenceable, Auditable, Modifiable):
    """ Specialized table for aliquot parts generated from a specimen.

        Attributes:
            id: (int) machine generated primary key
            specimen_id: (int) the specimen this aliquot was generated from
    """
    zope.interface.implements(interfaces.IAliquot)

    specimen_id = Column(Integer, nullable=False)

    specimen = Relationship(
            Specimen,
            backref=backref(
                name='aliquot',
                primaryjoin='Specimen.id == Aliquot.specimen_id',
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(specimen_id == Specimen.id)
            )

    aliquot_type_id = Column(Integer, nullable=False)

    aliquot_type = Relationship(
            AliquotType,
            backref=backref(
                name='aliquot',
                primaryjoin='AliquotType.id == Aliquot.aliquot_type_id',
                cascade='all, delete, delete-orphan',
                ),
            primaryjoin=(aliquot_type_id == AliquotType.id)
            )

    state_id = Column(
            Integer,
            nullable=False
            )

    state = Relationship(
            AliquotState,
            primaryjoin=(state_id==AliquotState.id)
            )

    labbook = Column(Unicode)

    volume = Column(Float)

    cell_amount = Column(Float)

    store_date = Column(Date)

    freezer = Column(Unicode)

    rack = Column(Unicode)

    box = Column(Unicode)

    location_id = Column(Integer)

    location = Relationship(
            Location,
            backref=backref(
                name='aliquot',
                primaryjoin='Aliquot.location_id == Location.id',
                ),
            primaryjoin=(location_id==Location.id)
            )

    thawed_num = Column(Integer)

    inventory_date = Column(Date)

    sent_date = Column(Date)

    sent_name = Column(Unicode)

    sent_notes = Column(Unicode)

    notes = Column(Unicode)

    special_instruction_id = Column(Integer)

    special_instruction = Relationship(
            SpecialInstruction,
            primaryjoin=(special_instruction_id == SpecialInstruction.id)
            )


    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['specimen_id'],
                refcolumns=['specimen.id'],
                name='fk_%s_specimen_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),

            ForeignKeyConstraint(
                columns=['aliquot_type_id'],
                refcolumns=['aliquottype.id'],
                name='fk_%s_aliquottype_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),

            ForeignKeyConstraint(
                columns=['location_id'],
                refcolumns=['location.id'],
                name='fk_%s_location_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),

            ForeignKeyConstraint(
                columns=['special_instruction_id'],
                refcolumns=['specialinstruction.id'],
                name='fk_%s_specialinstruction_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['aliquotstate.id'],
                name='fk_%s_aliquotstate_id' % cls.__tablename__,
                ondelete='SET NULL',
                ),
            )

if __name__ == '__main__': # pragma: no cover
    import sqlalchemy
    # A convenient way for checking the model even correctly loads the tables
    Model.metadata.create_all(bind=sqlalchemy.create_engine('sqlite://', echo=True))
