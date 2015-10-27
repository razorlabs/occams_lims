from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import (
    Table, Column,
    ForeignKey, ForeignKeyConstraint, UniqueConstraint, Index,
    Boolean, Date, Time, Float, Integer, Unicode)
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from occams_datastore.models import (
    ModelClass, Referenceable, Describeable, Modifiable, Auditable)
from occams_studies.models import Site, Patient, Study, Cycle, Visit

Base = ModelClass('Base')


class groups:

    @staticmethod
    def principal(location=None, group=None):
        """
        Generates the principal name used internally by this application
        Supported keyword parameters are:
            site --  The site code
            group -- The group name
        """
        return location.name + ':' + group if location else group

    @staticmethod
    def administrator():
        return groups.principal(group='administrator')

    @staticmethod
    def manager(location=None):
        return groups.principal(location=location, group='manager')

    @staticmethod
    def worker(location=None):
        return groups.principal(location=location, group='worker')

    @staticmethod
    def member(location=None):
        return groups.principal(location=location, group='member')


class LabFactory(dict):

    __acl__ = [
        (Allow, groups.administrator(), ALL_PERMISSIONS),
        (Allow, Authenticated, 'view')
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        db_session = self.request.db_session
        try:
            lab = db_session.query(Location).filter_by(name=key).one()
        except orm.exc.NoResultFound:
            raise KeyError

        return lab


class SpecimenFactory(dict):

    __acl__ = [
        (Allow, groups.administrator(), ALL_PERMISSIONS),
        (Allow, Authenticated, 'view')
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        db_session = self.request.db_session
        try:
            specimen = db_session.query(Specimen).filter_by(id=key).one()
        except orm.exc.NoResultFound:
            raise KeyError
        specimen.__parent__ = self
        return specimen


class AliquotFactory(dict):

    __acl__ = [
        (Allow, groups.administrator(), ALL_PERMISSIONS),
        (Allow, Authenticated, 'view')
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        db_session = self.request.db_session
        try:
            aliquot = db_session.query(Aliquot).filter_by(id=key).one()
        except orm.exc.NoResultFound:
            raise KeyError
        aliquot.__parent__ = self
        return aliquot


specimentype_study_table = Table(
    'specimentype_study',
    Base.metadata,
    Column('study_id',
           Integer,
           ForeignKey(Study.id,
                      name='fk_specimentype_study_study_id',
                      ondelete='CASCADE'),
           primary_key=True),
    Column('specimentype_id',
           Integer,
           ForeignKey('specimentype.id',
                      name='fk_specimentype_study_specimentype_id',
                      ondelete='CASCADE'),
           primary_key=True))


specimentype_cycle_table = Table(
    'specimentype_cycle',
    Base.metadata,
    Column('cycle_id',
           Integer,
           ForeignKey(Cycle.id,
                      name='fk_specimentype_cycle_cycle_id',
                      ondelete='CASCADE'),
           primary_key=True),
    Column('specimentype_id',
           Integer,
           ForeignKey('specimentype.id',
                      name='fk_specimentype_cycle_specimentype_id',
                      ondelete='CASCADE',),
           primary_key=True))


site_lab_location_table = Table(
    'site_lab_location',
    Base.metadata,
    Column('site_id',
           Integer,
           ForeignKey(Site.id,
                      name='fk_site_lab_location_site_id',
                      ondelete='CASCADE'),
           primary_key=True),
    Column('location_id',
           Integer,
           ForeignKey('location.id',
                      name='fk_site_lab_location_location_id',
                      ondelete='CASCADE')))


class SpecimenState(Base, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the destination,
    such as address, contact info, etc.
    Right now we just need a vocabulary
    """

    __tablename__ = 'specimenstate'

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name'),)


class AliquotState(Base, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the destination,
    such as address, contact info, etc.
    Right now we just need a vocabulary
    """

    __tablename__ = 'aliquotstate'

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name'),)


class Location(Base, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the destination,
    such as address, contact info, etc.
    Right now we just need a vocabulary
    """

    __tablename__ = 'location'

    @property
    def __acl__(self):
        acl = [
            (Allow, groups.administrator(), ALL_PERMISSIONS),
            (Allow, groups.manager(), ('view', 'edit', 'delete', 'process')),
            (Allow, groups.worker(self), ('view', 'process')),
            (Allow, groups.member(self), 'view')
        ]

        return acl

    # TODO: Seems like this was ever meant to be 1:1
    sites = relationship(
        Site,
        secondary=site_lab_location_table,
        backref=backref(
            name='lab_location',
            uselist=False))

    is_enabled = Column(
        Boolean,
        doc='Indicates that this lab manages samples through the app')

    active = Column(
        Boolean,
        doc='Indicates that this samples can be sent to this location')

    long_title1 = Column(Unicode, doc='Address Line 1')

    long_title2 = Column(Unicode, doc='Address Line 2')

    address_street = Column(Unicode)

    address_city = Column(Unicode)

    address_state = Column(Unicode)

    address_zip = Column(Unicode)

    phone_number = Column(Unicode)

    fax_number = Column(Unicode)

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name'),
            Index('ix_%s_active' % cls.__tablename__, 'active'))


class SpecialInstruction(Base, Describeable, Referenceable, Modifiable):
    """
    We may wish to add information here about the special instruction
    Right now we just need a vocabulary
    """

    __tablename__ = 'specialinstruction'

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('name'), )


class SpecimenType(Base, Referenceable, Describeable, Modifiable):

    __tablename__ = 'specimentype'

    tube_type = Column(
        Unicode,
        doc='The Type of tube used for this specimen type')

    default_tubes = Column(Integer, doc='Default tubes count')

    studies = relationship(
        Study,
        secondary=specimentype_study_table,
        collection_class=set,
        backref=backref(
            name='specimen_types',
            collection_class=set))

    cycles = relationship(
        Cycle,
        secondary=specimentype_cycle_table,
        collection_class=set,
        backref=backref(
            name='specimen_types',
            collection_class=set))

    # aliquot_types backreffed in AliquotType


class AliquotType(Base, Referenceable, Describeable, Modifiable):

    __tablename__ = 'aliquottype'

    specimen_type_id = Column(Integer, nullable=False)

    specimen_type = relationship(
        SpecimenType,
        backref=backref(
            name='aliquot_types',
            primaryjoin='SpecimenType.id == AliquotType.specimen_type_id',
            collection_class=attribute_mapped_collection('name'),
            order_by='AliquotType.title',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(specimen_type_id == SpecimenType.id),
        doc='The Type specimen from which this aliquot type is derived')

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['specimen_type_id'],
                refcolumns=['specimentype.id'],
                name='fk_%s_specimentype_id' % cls.__tablename__,
                ondelete='CASCADE'),
            UniqueConstraint('specimen_type_id', 'name'),
            Index('ix_%s_specimen_type_id' % cls.__tablename__,
                  'specimen_type_id'))


class Specimen(Base, Referenceable, Auditable, Modifiable):
    """
    Speccialized table for specimen data. Note that only one specimen can be
    drawn from a patient/protocol/type.
    """

    __tablename__ = 'specimen'

    specimen_type_id = Column(Integer, nullable=False)

    specimen_type = relationship(
        SpecimenType,
        backref=backref(
            name='specimen',
            primaryjoin='SpecimenType.id == Specimen.specimen_type_id',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(specimen_type_id == SpecimenType.id),
        doc='The Type specimen')

    patient_id = Column(Integer, nullable=False)

    patient = relationship(
        Patient,
        backref=backref(
            name='specimen',
            primaryjoin='Patient.id==Specimen.patient_id',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(patient_id == Patient.id),
        doc='The source patient')

    cycle_id = Column(Integer)

    cycle = relationship(
        Cycle,
        backref=backref(
            name='specimen',
            primaryjoin='Cycle.id==Specimen.cycle_id',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(cycle_id == Cycle.id),
        doc='The cycle for which this specimen was collected')

    state_id = Column(Integer, nullable=False)

    state = relationship(
        SpecimenState,
        primaryjoin=(state_id == SpecimenState.id))

    collect_date = Column(Date)

    collect_time = Column(Time)

    location_id = Column(Integer)

    location = relationship(
        Location,
        backref=backref(
            name='specimen',
            primaryjoin='Location.id==Specimen.location_id'),
        primaryjoin=(location_id == Location.id),
        doc='The current location of the specimen')

    previous_location_id = Column(Integer)

    previous_location = relationship(
        Location,
        backref=backref(
            name='previous_specimen',
            primaryjoin='Location.id==Specimen.previous_location_id'),
        primaryjoin=(previous_location_id == Location.id),
        doc='The processing location for the specimen')

    tubes = Column(Integer)

    notes = Column(Unicode)

    @property
    def visit_date(self):
        session = orm.object_session(self)
        query = (
            session.query(Visit)
            .filter(Visit.patient == self.patient)
            .filter(Visit.cycles.any(id=self.cycle.id)))
        try:
            visit = query.one()
        except orm.exc.NoResultFound:
            return self.collect_date
        except orm.exc.MultipleResultsFound:
            return self.collect_date
        else:
            return visit.visit_date

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['specimen_type_id'],
                refcolumns=['specimentype.id'],
                name='fk_%s_specimentype_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=[Patient.id],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=['cycle_id'],
                refcolumns=[Cycle.id],
                name='fk_%s_cycle_id' % cls.__tablename__,
                ondelete='SET NULL'),
            ForeignKeyConstraint(
                columns=['location_id'],
                refcolumns=['location.id'],
                name='fk_%s_location_id' % cls.__tablename__,
                ondelete='SET NULL'),
            ForeignKeyConstraint(
                columns=['previous_location_id'],
                refcolumns=['location.id'],
                name='fk_%s_previous_location_id' % cls.__tablename__,
                ondelete='SET NULL'),
            ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['specimenstate.id'],
                name='fk_%s_specimenstate_id' % cls.__tablename__,
                ondelete='SET NULL'),
            Index('ix_%s_specimen_type_id' % cls.__tablename__,
                  'specimen_type_id'),
            Index('ix_%s_patient_id' % cls.__tablename__, 'patient_id'),
            Index('ix_%s_cycle_id' % cls.__tablename__, 'cycle_id'),
            Index('ix_%s_location_id' % cls.__tablename__, 'location_id'),
            Index('ix_%s_previous_location_id' % cls.__tablename__,
                  'previous_location_id'),
            Index('ix_%s_state_id' % cls.__tablename__, 'state_id'))


class Aliquot(Base, Referenceable, Auditable, Modifiable):
    """
    Specialized table for aliquot parts generated from a specimen.
    """

    __tablename__ = 'aliquot'

    specimen_id = Column(Integer, nullable=False)

    specimen = relationship(
        Specimen,
        backref=backref(
            name='aliquot',
            primaryjoin='Specimen.id == Aliquot.specimen_id',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(specimen_id == Specimen.id),
        doc='The source specimen that this aliquot sample was extracted from')

    aliquot_type_id = Column(Integer, nullable=False)

    aliquot_type = relationship(
        AliquotType,
        backref=backref(
            name='aliquot',
            primaryjoin='AliquotType.id == Aliquot.aliquot_type_id',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(aliquot_type_id == AliquotType.id))

    state_id = Column(Integer, nullable=False)

    state = relationship(
        AliquotState,
        primaryjoin=(state_id == AliquotState.id))

    labbook = Column(Unicode, doc='Lab Book number')

    _volume = Column('volume', Float, doc='Volume of liquot aliquot')

    _cell_amount = Column('cell_amount', Float, doc='Cell count of an aliquot')

    @property
    def amount(self):
        # TODO Check aliquot type for this
        return self._volume or self._cell_amount

    @amount.setter
    def amount(self, value):
        # TODO Check aliquot type for this
        self.volume = value

    store_date = Column(Date)

    freezer = Column(Unicode)

    rack = Column(Unicode)

    box = Column(Unicode)

    location_id = Column(Integer)

    location = relationship(
        Location,
        backref=backref(
            name='aliquot',
            primaryjoin='Aliquot.location_id == Location.id'),
        primaryjoin=(location_id == Location.id))

    previous_location_id = Column(Integer)

    previous_location = relationship(
        Location,
        backref=backref(
            name='stored_aliquot',
            primaryjoin='Aliquot.previous_location_id == Location.id'),
        primaryjoin=(previous_location_id == Location.id))

    thawed_num = Column(Integer)

    inventory_date = Column(Date)

    sent_date = Column(Date, doc='Date sent for analysis')

    sent_name = Column(Unicode)

    sent_notes = Column(Unicode)

    notes = Column(Unicode)

    special_instruction_id = Column(Integer)

    special_instruction = relationship(
        SpecialInstruction,
        primaryjoin=(special_instruction_id == SpecialInstruction.id))

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                columns=['specimen_id'],
                refcolumns=['specimen.id'],
                name='fk_%s_specimen_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=['aliquot_type_id'],
                refcolumns=['aliquottype.id'],
                name='fk_%s_aliquottype_id' % cls.__tablename__,
                ondelete='CASCADE'),
            ForeignKeyConstraint(
                columns=['location_id'],
                refcolumns=['location.id'],
                name='fk_%s_location_id' % cls.__tablename__,
                ondelete='SET NULL'),
            ForeignKeyConstraint(
                columns=['previous_location_id'],
                refcolumns=['location.id'],
                name='fk_%s_previous_location_id' % cls.__tablename__,
                ondelete='SET NULL'),
            ForeignKeyConstraint(
                columns=['special_instruction_id'],
                refcolumns=['specialinstruction.id'],
                name='fk_%s_specialinstruction_id' % cls.__tablename__,
                ondelete='SET NULL'),
            ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['aliquotstate.id'],
                name='fk_%s_aliquotstate_id' % cls.__tablename__,
                ondelete='SET NULL'),
            Index('ix_%s_specimen_id' % cls.__tablename__, 'specimen_id'),
            Index('ix_%s_aliquot_type_id' % cls.__tablename__,
                  'aliquot_type_id'),
            Index('ix_%s_location_id' % cls.__tablename__, 'location_id'),
            Index('ix_%s_previous_location_id' % cls.__tablename__,
                  'previous_location_id'),
            Index('ix_%s_state_id' % cls.__tablename__, 'state_id'))
