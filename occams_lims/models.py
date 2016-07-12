from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
import sqlalchemy as sa
from sqlalchemy import orm, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.collections import attribute_mapped_collection

from occams_datastore import models as datastore
from occams_studies import models as studies


class LimsModel(datastore.Base):
    __abstract__ = True
    # TODO: move this to 'lims' schema'
    metadata = sa.MetaData()


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


specimentype_study_table = sa.Table(
    'specimentype_study',
    LimsModel.metadata,
    sa.Column(
        'study_id',
        sa.Integer,
        sa.ForeignKey(
            studies.Study.id,
            name='fk_specimentype_study_study_id',
            ondelete='CASCADE'),
        primary_key=True),
    sa.Column(
        'specimentype_id',
        sa.Integer,
        sa.ForeignKey(
            'specimentype.id',
            name='fk_specimentype_study_specimentype_id',
            ondelete='CASCADE'),
        primary_key=True))


specimentype_cycle_table = sa.Table(
    'specimentype_cycle',
    LimsModel.metadata,
    sa.Column(
        'cycle_id',
        sa.Integer,
        sa.ForeignKey(
            studies.Cycle.id,
            name='fk_specimentype_cycle_cycle_id',
            ondelete='CASCADE'),
        primary_key=True),
    sa.Column(
        'specimentype_id',
        sa.Integer,
        sa.ForeignKey(
            'specimentype.id',
            name='fk_specimentype_cycle_specimentype_id',
            ondelete='CASCADE',),
        primary_key=True))


site_lab_location_table = sa.Table(
    'site_lab_location',
    LimsModel.metadata,
    sa.Column(
        'site_id',
        sa.Integer,
        sa.ForeignKey(
            studies.Site.id,
            name='fk_site_lab_location_site_id',
            ondelete='CASCADE'),
        primary_key=True),
    sa.Column(
        'location_id',
        sa.Integer,
        sa.ForeignKey(
            'location.id',
            name='fk_site_lab_location_location_id',
            ondelete='CASCADE')))


class SpecimenState(LimsModel,
                    datastore.Describeable,
                    datastore.Referenceable,
                    datastore.Modifiable):
    """
    We may wish to add information here about the destination,
    such as address, contact info, etc.
    Right now we just need a vocabulary
    """

    __tablename__ = 'specimenstate'

    @declared_attr
    def __table_args__(cls):
        return (
            sa.UniqueConstraint('name'),)


@event.listens_for(SpecimenState.__table__, 'after_create')
def populate_default_specimen_states(target, connection, **kw):
    """
    We currently only ship with hard-coded states.

    This method expectecs the current connection to be annotated with
    a user in the info "blame" key. This user is ideally created after the
    "user" table is created.
    """

    blame = connection.info['blame']
    user_table = datastore.User.__table__

    result = connection.execute(
        user_table
        .select()
        .where(user_table.c.key == blame))

    user = result.fetchone()
    blame_id = user['id']

    def state(**kw):
        values = kw.copy()
        values.update({
            'create_user_id': blame_id,
            'modify_user_id': blame_id,
        })
        return values

    connection.execute(target.insert().values([
        state(name=u'pending-draw', title=u'Pending Draw'),
        state(name=u'cancel-draw', title=u'Draw Cancelled'),
        state(name=u'pending-aliquot', title=u'Pending Aliquot'),
        state(name=u'aliquoted', title=u'Aliquoted'),
        state(name=u'rejected', title=u'Rejected'),
        state(name=u'prepared-aliquot', title=u'Prepared for Aliquot'),
        state(name=u'complete', title=u'Complete'),
        state(name=u'batched', title=u'Batched'),
        state(name=u'postponed', title=u'Draw Postponed'),
    ]))


class AliquotState(LimsModel,
                   datastore.Describeable,
                   datastore.Referenceable,
                   datastore.Modifiable):
    """
    We may wish to add information here about the destination,
    such as address, contact info, etc.
    Right now we just need a vocabulary
    """

    __tablename__ = 'aliquotstate'

    @declared_attr
    def __table_args__(cls):
        return (
            sa.UniqueConstraint('name'),)


@event.listens_for(AliquotState.__table__, 'after_create')
def populate_default_aliquot_states(target, connection, **kw):
    """
    We currently only ship with hard-coded states.

    This method expectecs the current connection to be annotated with
    a user in the info "blame" key. This user is ideally created after the
    "user" table is created.
    """

    blame = connection.info['blame']
    user_table = datastore.User.__table__

    result = connection.execute(
        user_table
        .select()
        .where(user_table.c.key == blame))

    user = result.fetchone()
    blame_id = user['id']

    def state(**kw):
        values = kw.copy()
        values.update({
            'create_user_id': blame_id,
            'modify_user_id': blame_id,
        })
        return values

    connection.execute(target.insert().values([
        state(name=u'pending', title=u'Pending Check In'),
        state(name=u'checked-in', title=u'Checked In'),
        state(name=u'checked-out', title=u'CHecked Out'),
        state(name=u'hold', title=u'On Hold'),
        state(name=u'prepared', title=u'Prepared for Check In'),
        state(name=u'incorrect', title=u'Inaccurate Data'),
        state(name=u'pending-checkout', title=u'Check Out'),
        state(name=u'queued', title=u'Hold in Queue'),
        state(name=u'missing', title=u'Missing'),
        state(name=u'destroyed', title=u'Destroyed'),
    ]))


class Location(LimsModel,
               datastore.Describeable,
               datastore.Referenceable,
               datastore.Modifiable):
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
    sites = orm.relationship(
        studies.Site,
        secondary=site_lab_location_table,
        backref=orm.backref(
            name='lab_location',
            uselist=False))

    is_enabled = sa.Column(
        sa.Boolean,
        doc='Indicates that this lab manages samples through the app')

    active = sa.Column(
        sa.Boolean,
        doc='Indicates that this samples can be sent to this location')

    long_title1 = sa.Column(sa.Unicode, doc='Address Line 1')

    long_title2 = sa.Column(sa.Unicode, doc='Address Line 2')

    address_street = sa.Column(sa.Unicode)

    address_city = sa.Column(sa.Unicode)

    address_state = sa.Column(sa.Unicode)

    address_zip = sa.Column(sa.Unicode)

    phone_number = sa.Column(sa.Unicode)

    fax_number = sa.Column(sa.Unicode)

    @declared_attr
    def __table_args__(cls):
        return (
            sa.UniqueConstraint('name'),
            sa.Index('ix_%s_active' % cls.__tablename__, 'active'))


class SpecialInstruction(LimsModel,
                         datastore.Describeable,
                         datastore.Referenceable,
                         datastore.Modifiable):
    """
    We may wish to add information here about the special instruction
    Right now we just need a vocabulary
    """

    __tablename__ = 'specialinstruction'

    @declared_attr
    def __table_args__(cls):
        return (
            sa.UniqueConstraint('name'), )


class SpecimenType(LimsModel,
                   datastore.Referenceable,
                   datastore.Describeable,
                   datastore.Modifiable):

    __tablename__ = 'specimentype'

    tube_type = sa.Column(
        sa.Unicode,
        doc='The Type of tube used for this specimen type')

    default_tubes = sa.Column(sa.Integer, doc='Default tubes count')

    # aliquot_types backreffed in AliquotType

# Avoid name collisions with "studies" module
SpecimenType.studies = orm.relationship(
    studies.Study,
    secondary=specimentype_study_table,
    collection_class=set,
    backref=orm.backref(
        name='specimen_types',
        collection_class=set))

SpecimenType.cycles = orm.relationship(
    studies.Cycle,
    secondary=specimentype_cycle_table,
    collection_class=set,
    backref=orm.backref(
        name='specimen_types',
        collection_class=set))


class AliquotType(LimsModel,
                  datastore.Referenceable,
                  datastore.Describeable,
                  datastore.Modifiable):

    __tablename__ = 'aliquottype'

    specimen_type_id = sa.Column(sa.Integer, nullable=False)

    specimen_type = orm.relationship(
        SpecimenType,
        backref=orm.backref(
            name='aliquot_types',
            primaryjoin='SpecimenType.id == AliquotType.specimen_type_id',
            collection_class=attribute_mapped_collection('name'),
            order_by='AliquotType.title',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(specimen_type_id == SpecimenType.id),
        doc='The Type specimen from which this aliquot type is derived')

    units = sa.Column(sa.Unicode, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=['specimen_type_id'],
                refcolumns=['specimentype.id'],
                name='fk_%s_specimentype_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.UniqueConstraint('specimen_type_id', 'name'),
            sa.Index(
                'ix_%s_specimen_type_id' % cls.__tablename__,
                'specimen_type_id'))


class Specimen(LimsModel,
               datastore.Referenceable,
               datastore.Auditable,
               datastore.Modifiable):
    """
    Speccialized table for specimen data. Note that only one specimen can be
    drawn from a patient/protocol/type.
    """

    __tablename__ = 'specimen'

    specimen_type_id = sa.Column(sa.Integer, nullable=False)

    specimen_type = orm.relationship(
        SpecimenType,
        backref=orm.backref(
            name='specimen',
            primaryjoin='SpecimenType.id == Specimen.specimen_type_id',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(specimen_type_id == SpecimenType.id),
        doc='The Type specimen')

    patient_id = sa.Column(sa.Integer, nullable=False)

    patient = orm.relationship(
        studies.Patient,
        backref=orm.backref(
            name='specimen',
            primaryjoin='Patient.id==Specimen.patient_id',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(patient_id == studies.Patient.id),
        doc='The source patient')

    cycle_id = sa.Column(sa.Integer)

    cycle = orm.relationship(
        studies.Cycle,
        backref=orm.backref(
            name='specimen',
            primaryjoin='Cycle.id==Specimen.cycle_id',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(cycle_id == studies.Cycle.id),
        doc='The cycle for which this specimen was collected')

    state_id = sa.Column(sa.Integer, nullable=False)

    state = orm.relationship(
        SpecimenState,
        primaryjoin=(state_id == SpecimenState.id))

    collect_date = sa.Column(sa.Date)

    collect_time = sa.Column(sa.Time)

    location_id = sa.Column(sa.Integer)

    location = orm.relationship(
        Location,
        backref=orm.backref(
            name='specimen',
            primaryjoin='Location.id==Specimen.location_id'),
        primaryjoin=(location_id == Location.id),
        doc='The current location of the specimen')

    previous_location_id = sa.Column(sa.Integer)

    previous_location = orm.relationship(
        Location,
        backref=orm.backref(
            name='previous_specimen',
            primaryjoin='Location.id==Specimen.previous_location_id'),
        primaryjoin=(previous_location_id == Location.id),
        doc='The processing location for the specimen')

    tubes = sa.Column(sa.Integer)

    notes = sa.Column(sa.Unicode)

    @property
    def visit_date(self):
        session = orm.object_session(self)
        query = (
            session.query(studies.Visit)
            .filter(studies.Visit.patient == self.patient)
            .filter(studies.Visit.cycles.any(id=self.cycle.id)))
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
            sa.ForeignKeyConstraint(
                columns=['specimen_type_id'],
                refcolumns=['specimentype.id'],
                name='fk_%s_specimentype_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.ForeignKeyConstraint(
                columns=['patient_id'],
                refcolumns=[studies.Patient.id],
                name='fk_%s_patient_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.ForeignKeyConstraint(
                columns=['cycle_id'],
                refcolumns=[studies.Cycle.id],
                name='fk_%s_cycle_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.ForeignKeyConstraint(
                columns=['location_id'],
                refcolumns=['location.id'],
                name='fk_%s_location_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.ForeignKeyConstraint(
                columns=['previous_location_id'],
                refcolumns=['location.id'],
                name='fk_%s_previous_location_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['specimenstate.id'],
                name='fk_%s_specimenstate_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.Index(
                'ix_%s_specimen_type_id' % cls.__tablename__,
                'specimen_type_id'),
            sa.Index('ix_%s_patient_id' % cls.__tablename__, 'patient_id'),
            sa.Index('ix_%s_cycle_id' % cls.__tablename__, 'cycle_id'),
            sa.Index('ix_%s_location_id' % cls.__tablename__, 'location_id'),
            sa.Index(
                'ix_%s_previous_location_id' % cls.__tablename__,
                'previous_location_id'),
            sa.Index('ix_%s_state_id' % cls.__tablename__, 'state_id'))


class Aliquot(LimsModel,
              datastore.Referenceable,
              datastore.Auditable,
              datastore.Modifiable):
    """
    Specialized table for aliquot parts generated from a specimen.
    """

    __tablename__ = 'aliquot'

    specimen_id = sa.Column(sa.Integer, nullable=False)

    specimen = orm.relationship(
        Specimen,
        backref=orm.backref(
            name='aliquot',
            primaryjoin='Specimen.id == Aliquot.specimen_id',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(specimen_id == Specimen.id),
        doc='The source specimen that this aliquot sample was extracted from')

    aliquot_type_id = sa.Column(sa.Integer, nullable=False)

    aliquot_type = orm.relationship(
        AliquotType,
        backref=orm.backref(
            name='aliquot',
            primaryjoin='AliquotType.id == Aliquot.aliquot_type_id',
            cascade='all, delete, delete-orphan'),
        primaryjoin=(aliquot_type_id == AliquotType.id))

    state_id = sa.Column(sa.Integer, nullable=False)

    state = orm.relationship(
        AliquotState,
        primaryjoin=(state_id == AliquotState.id))

    labbook = sa.Column(sa.Unicode, doc='Lab Book number')

    amount = sa.Column('amount', sa.Numeric)

    store_date = sa.Column(sa.Date)

    freezer = sa.Column(sa.Unicode)

    rack = sa.Column(sa.Unicode)

    box = sa.Column(sa.Unicode)

    location_id = sa.Column(sa.Integer)

    location = orm.relationship(
        Location,
        backref=orm.backref(
            name='aliquot',
            primaryjoin='Aliquot.location_id == Location.id'),
        primaryjoin=(location_id == Location.id))

    previous_location_id = sa.Column(sa.Integer)

    previous_location = orm.relationship(
        Location,
        backref=orm.backref(
            name='stored_aliquot',
            primaryjoin='Aliquot.previous_location_id == Location.id'),
        primaryjoin=(previous_location_id == Location.id))

    thawed_num = sa.Column(sa.Integer)

    inventory_date = sa.Column(sa.Date)

    sent_date = sa.Column(sa.Date, doc='Date sent for analysis')

    sent_name = sa.Column(sa.Unicode)

    sent_notes = sa.Column(sa.Unicode)

    notes = sa.Column(sa.Unicode)

    special_instruction_id = sa.Column(sa.Integer)

    special_instruction = orm.relationship(
        SpecialInstruction,
        primaryjoin=(special_instruction_id == SpecialInstruction.id))

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=['specimen_id'],
                refcolumns=['specimen.id'],
                name='fk_%s_specimen_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.ForeignKeyConstraint(
                columns=['aliquot_type_id'],
                refcolumns=['aliquottype.id'],
                name='fk_%s_aliquottype_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.ForeignKeyConstraint(
                columns=['location_id'],
                refcolumns=['location.id'],
                name='fk_%s_location_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.ForeignKeyConstraint(
                columns=['previous_location_id'],
                refcolumns=['location.id'],
                name='fk_%s_previous_location_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.ForeignKeyConstraint(
                columns=['special_instruction_id'],
                refcolumns=['specialinstruction.id'],
                name='fk_%s_specialinstruction_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['aliquotstate.id'],
                name='fk_%s_aliquotstate_id' % cls.__tablename__,
                ondelete='SET NULL'),
            sa.Index('ix_%s_specimen_id' % cls.__tablename__, 'specimen_id'),
            sa.Index(
                'ix_%s_aliquot_type_id' % cls.__tablename__,
                'aliquot_type_id'),
            sa.Index('ix_%s_location_id' % cls.__tablename__, 'location_id'),
            sa.Index(
                'ix_%s_previous_location_id' % cls.__tablename__,
                'previous_location_id'),
            sa.Index('ix_%s_state_id' % cls.__tablename__, 'state_id'))
