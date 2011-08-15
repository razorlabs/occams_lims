""" Lab Models
"""
from avrc.aeh.model import Visit, \
                          visit_protocol_table
from avrc.data.store.model import Model
from hive.lab.content.objects import Aliquot as AliquotObject, \
                                     Specimen as SpecimenObject
from sqlalchemy import text
from sqlalchemy.orm import relation as Relationship
from sqlalchemy.schema import Column, \
                              ForeignKey, \
                              UniqueConstraint
from sqlalchemy.types import Boolean, \
                             Date, \
                             DateTime, \
                             Float, \
                             Integer, \
                             Time, \
                             Unicode
                           
__all__ = ('SpecimenAliquotTerm', 'Specimen', 'Aliquot', 'AliquotHistory',)

NOW = text('CURRENT_TIMESTAMP')

FALSE = text('FALSE')


class SpecimenAliquotTerm(Model):
    """ Specimen/Aliquot vocabulary source
    """
    __tablename__ = 'specimen_aliquot_term'

    id = Column(Integer, primary_key=True)

    vocabulary_name = Column(Unicode, nullable=False, index=True)

    title = Column(Unicode)

    token = Column(Unicode, nullable=False)

    value = Column(Unicode, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=NOW)

    modify_date = Column(DateTime, nullable=False, default=NOW, onupdate=NOW)

    __table_args = (
        UniqueConstraint('vocabulary_name', 'token', 'value'),
        dict()
        )


class Specimen(Model):
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
    __tablename__ = 'specimen'

    id = Column(Integer, primary_key=True)

    blueprint_zid = Column(Integer, nullable=True, unique=False)

    subject_id = Column(
        ForeignKey('subject.id', ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    subject = Relationship('Subject')

    protocol_id = Column(
        ForeignKey('protocol.id', ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    protocol = Relationship('Protocol')

    visit = Relationship(
        'Visit',
        uselist=False,
        secondary=visit_protocol_table,
        primaryjoin=((protocol_id == visit_protocol_table.c.protocol_id) & (Visit.subject_id == subject_id)),
        secondaryjoin=(Visit.id == visit_protocol_table.c.visit_id),
        foreign_keys=[visit_protocol_table.c.protocol_id, visit_protocol_table.c.visit_id, Visit.subject_id, ]
        )

    state_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    state = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=state_id == SpecimenAliquotTerm.id
        )

    collect_date = Column(Date)

    collect_time = Column(Time)

    type_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    type = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=type_id == SpecimenAliquotTerm.id
        )

    destination_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    destination = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=destination_id == SpecimenAliquotTerm.id
        )

    tubes = Column(Integer)

    tupe_type_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    tube_type = Relationship(
         'SpecimenAliquotTerm',
         primaryjoin=tupe_type_id == SpecimenAliquotTerm.id
         )

    notes = Column(Unicode)

    aliquot = Relationship('Aliquot')

    create_name = Column(Unicode(255))

    modify_name = Column(Unicode(255))

    study_cycle_label = Column(Unicode(255))

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=NOW)

    modify_date = Column(DateTime, nullable=False, default=NOW, onupdate=NOW)

    __table_args = (
        UniqueConstraint('subject_id', 'protocol_id', 'type'),
        dict()
        )

    def objectify(self):
        obj = SpecimenObject()
        obj.id = self.id
        obj.dsid = self.id
        obj.blueprint_zid = self.blueprint_zid
        if self.subject is not None:
            subject_zid = self.subject.zid
        else:
            subject_zid = None
        obj.subject_zid = subject_zid
        if self.protocol is not None:
            protocol_zid = self.protocol.zid
        else:
            protocol_zid = None
        obj.protocol_zid = protocol_zid
        if self.state is not None:
            state = self.state.value
        else:
            state = None
        obj.state = state
        obj.date_collected = self.collect_date
        obj.time_collected = self.collect_time
        if self.type is not None:
            type = self.type.value
        else:
            type = None
        obj.type = type
        if self.destination is not None:
            destination = self.destination.value
        else:
            destination = None
        obj.destination = destination
        obj.tubes = self.tubes
        if self.tube_type is not None:
            tube_type = self.tube_type.value
        else:
            tube_type = None
        obj.tube_type = tube_type
        obj.notes = self.notes
        if self.visit is not None:
            visit_zid = self.visit.zid
        else:
            visit_zid = None
        obj.visit_zid = visit_zid
        return obj

class Aliquot(Model):
    """ Specialized table for aliquot parts generated from a specimen.

        Attributes:
            id: (int) machine generated primary key
            specimen_id: (int) the specimen this aliquot was generated from
    """
    __tablename__ = 'aliquot'

    id = Column(Integer, primary_key=True)

    specimen_id = Column(
        ForeignKey(Specimen.id, ondelete='CASCADE'),
        nullable=False,
        index=True,
        )

    specimen = Relationship('Specimen')

    type_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    type = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=type_id == SpecimenAliquotTerm.id
        )

    volume = Column(Float)

    cell_amount = Column(Float)

    state_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    state = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=state_id == SpecimenAliquotTerm.id
        )

    store_date = Column(Date)

    freezer = Column(Unicode)

    rack = Column(Unicode)

    box = Column(Unicode)

    storage_site_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    storage_site = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=storage_site_id == SpecimenAliquotTerm.id
        )

    thawed_num = Column(Integer)

    analysis_status_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        index=True
        )

    analysis_status = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=analysis_status_id == SpecimenAliquotTerm.id,
        )

    inventory_date = Column(Date,
             nullable=True)

    sent_date = Column(Date)

    sent_name = Column(Unicode)

    sent_site_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    sent_site = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=(sent_site_id == SpecimenAliquotTerm.id)
        )

    sent_notes = Column(Unicode)

    notes = Column(Unicode)

    special_instruction_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    special_instruction = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=special_instruction_id == SpecimenAliquotTerm.id
        )

    create_name = Column(Unicode(255))

    modify_name = Column(Unicode(255))

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=NOW)

    modify_date = Column(DateTime, nullable=False, default=NOW, onupdate=NOW)


    def objectify(self):
        obj = AliquotObject()
        obj.id = self.id
        obj.dsid = self.id
        obj.specimen_dsid = self.specimen.id
        if self.type is not None:
            type = self.type.value
        else:
            type = None
        obj.type = type
        if self.state is not None:
            state = self.state.value
        else:
            state = None
        obj.state = state
        obj.volume = self.volume
        obj.cell_amount = self.cell_amount
        obj.store_date = self.store_date
        obj.freezer = self.freezer
        obj.rack = self.rack
        obj.box = self.box
        if self.storage_site is not None:
            storage_site = self.storage_site.value
        else:
            storage_site = None
        obj.storage_site = storage_site
        obj.thawed_num = self.thawed_num
        if self.analysis_status is not None:
            analysis_status = self.analysis_status.value
        else:
            analysis_status = None
        obj.analysis_status = analysis_status
        obj.sent_date = self.sent_date
        obj.sent_name = self.sent_name
        obj.notes = self.notes
        obj.sent_notes = self.sent_notes
        if self.special_instruction is not None:
            special_instruction = self.special_instruction.value
        else:
            special_instruction = None
        obj.special_instruction = special_instruction
        return obj



class AliquotHistory(Model):
    """ Keeps track of aliquot state history.
    """

    __tablename__ = 'aliquot_history'

    id = Column(Integer, primary_key=True)

    aliquot_id = Column(
        ForeignKey(Aliquot.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )
        
    aliquot = Relationship('Aliquot')

    from_state_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    from_state = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=from_state_id == SpecimenAliquotTerm.id
        )

    to_state_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    to_state = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=to_state_id == SpecimenAliquotTerm.id
        )

    action_date = Column(DateTime, nullable=False)

    create_date = Column(DateTime, nullable=False, default=NOW)

    create_name = Column(Unicode, nullable=False)

