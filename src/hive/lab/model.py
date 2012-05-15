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


from occams.datastore.model import Model
from occams.datastore.model.storage import ENTITY_STATE_NAMES
from occams.datastore.model.metadata import AutoNamed
from occams.datastore.model.metadata import Describeable
from occams.datastore.model.metadata import Referenceable
from occams.datastore.model.metadata import Modifiable
from occams.datastore.model.auditing import Auditable

from hive.lab.interfaces.specimen import ISpecimen
from hive.lab.interfaces.aliquot import IAliquot

from avrc.aeh.model import *


__all__ = ('SpecimenAliquotTerm', 'Specimen', 'Aliquot', 'AliquotHistory',)

NOW = text('CURRENT_TIMESTAMP')

SPECIMEN_STATE_NAMES = sorted([term.token for term in ISpecimen['state'].vocabulary])

ALIQUOT_STATE_NAMES = sorted([term.token for term in IAliquot['state'].vocabulary])


class Location(Model, AutoNamed, Describeable, Referenceable, Auditable, Modifiable):
    """
    We may wish to add information here about the destination, such as address, contact info, etc.
    Right now we just need a vocabulary
    """

    value = Column(Unicode, nullable=False, unique=True)


class SpecialInstruction(Model, AutoNamed, Describeable, Referenceable, Auditable, Modifiable):
    """
    We may wish to add information here about the special instruction
    Right now we just need a vocabulary
    """


    value = Column(Unicode, nullable=False, unique=True)


class SpecimenType(Model, AutoNamed, Describeable, Referenceable, Auditable, Modifiable):
    """
    """

    blueprint_zid = Column(Integer, nullable=True, unique=True)

    ## Tube type always matches the specimen type
    tube_type = Column(Unicode)


class AliquotType(Model, AutoNamed, Describeable, Referenceable, Auditable, Modifiable):
    """
    """

    blueprint_zid = Column(Integer, nullable=True, unique=True)

    specimen_type_id = Column(Integer, ForeignKey(SpecimenType.id), nullable=False,)

    specimen_type = Relationship(
            SpecimenType,
            backref=backref(
                name='aliquot_type',
                collection_class=attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
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
            is_active: (bool) internal marker to indicate this entry is
                being used.
            create_date: (datetime) internal metadata of when entry was created
            modify_date: (datetime) internal metadata of when entry was modified
    """

    specimen_type_id = Column(Integer, ForeignKey(SpecimenType.id), nullable=False,)

    specimen_type = Relationship(
            SpecimenType,
            backref=backref(
                name='specimen',
                collection_class=attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
            )

    patient_id = Column(Integer, ForeignKey(Patient.id), nullable=False,)

    patient = Relationship(
            Patient,
            backref=backref(
                name='specimen',
                collection_class=attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
            )

    cycle_id = Column(Integer, ForeignKey(Cycle.id), nullable=False,)

    cycle = Relationship(
            Cycle,
            backref=backref(
                name='specimen',
                collection_class=attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
            )

    visit = Relationship(
        Visit,
        uselist=False,
        secondary=visit_cycle_table,
        primaryjoin=((cycle_id == visit_cycle_table.c.cycle_id) & (Visit.patient_id == patient_id)),
        secondaryjoin=(Visit.id == visit_cycle_table.c.visit_id),
        foreign_keys=[visit_cycle_table.c.cycle_id, visit_cycle_table.c.visit_id, Visit.patient_id, ]
        )

    state = Column(
        Enum(*ENTITY_STATE_NAMES, name='specimen_state'),
        nullable=False,
        server_default=ISpecimen['state'].default
        )

    collect_date = Column(Date)

    collect_time = Column(Time)

    location_id = Column(Integer, ForeignKey(Location.id))

    location = Relationship(
            Location,
            backref=backref(
                name='specimen',
                collection_class=attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
            )

    tubes = Column(Integer)

    notes = Column(Unicode)

    study_cycle_label = Column(Unicode(255))

    __table_args = (
        UniqueConstraint('patient_id', 'cycle_id', 'specimen_type'),
        )


class Aliquot(Model, AutoNamed, Referenceable, Auditable, Modifiable):
    """ Specialized table for aliquot parts generated from a specimen.

        Attributes:
            id: (int) machine generated primary key
            specimen_id: (int) the specimen this aliquot was generated from
    """

    specimen_id = Column(Integer, ForeignKey(Specimen.id), nullable=False,)

    specimen = Relationship(
            Specimen,
            backref=backref(
                name='aliquot',
                collection_class=attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
            )

    aliquot_type_id = Column(Integer, ForeignKey(AliquotType.id), nullable=False,)

    aliquot_type = Relationship(
            AliquotType,
            backref=backref(
                name='aliquot_type',
                collection_class=attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
            )

    state = Column(
        Enum(*ENTITY_STATE_NAMES, name='specimen_state'),
        nullable=False,
        server_default=ISpecimen['state'].default
        )

    labbook = Column(Unicode)

    volume = Column(Float)

    cell_amount = Column(Float)

    store_date = Column(Date)

    freezer = Column(Unicode)

    rack = Column(Unicode)

    box = Column(Unicode)

    location_id = Column(Integer, ForeignKey(Location.id))

    location = Relationship(
            Location,
            backref=backref(
                name='aliquot',
                collection_class=attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
            )

    thawed_num = Column(Integer)

    inventory_date = Column(Date)

    sent_date = Column(Date)

    sent_name = Column(Unicode)

    sent_notes = Column(Unicode)

    notes = Column(Unicode)

    special_instruction_id = Column(Integer, ForeignKey(SpecialInstruction.id), nullable=False,)

    special_instruction = Relationship(
            SpecialInstruction,
            backref=backref(
                name='aliquot',
                collection_class=attribute_mapped_collection('name'),
                cascade='all, delete, delete-orphan',
                ),
            )

if __name__ == '__main__': # pragma: no cover
    import sqlalchemy
    # A convenient way for checking the model even correctly loads the tables
    Model.metadata.create_all(bind=sqlalchemy.create_engine('sqlite://', echo=True))
