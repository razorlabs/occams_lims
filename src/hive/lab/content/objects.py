from avrc.data.store.storage import Item
from hive.lab import utilities as utils
from hive.lab.interfaces.aliquot import IAliquot, \
                                        IAliquotBlueprint
from hive.lab.interfaces.lab import IFilterForm
from hive.lab.interfaces.specimen import ISpecimen, \
                                         ISpecimenBlueprint
from plone.dexterity import content
from zope.app.intid.interfaces import IIntIds
from zope.schema.fieldproperty import FieldProperty
import zope.component
import zope.interface


class Specimen(Item):
    """ See `ISpecimen`
    """
    zope.interface.implements(ISpecimen)
    
    dsid = FieldProperty(ISpecimen['dsid'])
    blueprint_zid = FieldProperty(ISpecimen['blueprint_zid'])
    subject_zid = FieldProperty(ISpecimen['subject_zid'])
    protocol_zid = FieldProperty(ISpecimen['protocol_zid'])
    state = FieldProperty(ISpecimen['state'])
    date_collected = FieldProperty(ISpecimen['date_collected'])
    time_collected = FieldProperty(ISpecimen['time_collected'])
    type = FieldProperty(ISpecimen['type'])
    destination = FieldProperty(ISpecimen['destination'])
    tubes = FieldProperty(ISpecimen['tubes'])
    tube_type = FieldProperty(ISpecimen['tube_type'])
    notes = FieldProperty(ISpecimen['notes'])

    @classmethod
    def from_rslt(cls, rslt):
        obj = cls()
        obj.dsid = rslt.id
        obj.blueprint_zid = rslt.blueprint_zid
        if rslt.subject is not None:
            subject_zid = rslt.subject.zid
        else:
            subject_zid = None
        obj.subject_zid = subject_zid
        if rslt.protocol is not None:
            protocol_zid = rslt.protocol.zid
        else:
            protocol_zid = None
        obj.protocol_zid = protocol_zid
        if rslt.state is not None:
            state = rslt.state.value
        else:
            state = None
        obj.state = state
        obj.date_collected = rslt.collect_date
        obj.time_collected = rslt.collect_time
        if rslt.type is not None:
            type = rslt.type.value
        else:
            type = None
        obj.type = type
        if rslt.destination is not None:
            destination = rslt.destination.value
        else:
            destination = None
        obj.destination = destination
        obj.tubes = rslt.tubes
        if rslt.tube_type is not None:
            tube_type = rslt.tube_type.value
        else:
            tube_type = None
        obj.tube_type = tube_type
        obj.notes = rslt.notes
        if rslt.visit is not None:
            visit_zid = rslt.visit.zid
        else:
            visit_zid = None
        obj.visit_zid = visit_zid
        return obj

    def visit(self):
        intids = zope.component.getUtility(IIntIds)
        if self.visit_zid:
            try:
                visit = intids.getObject(self.visit_zid)
            except KeyError:
                visit = None
        else:
            visit = None
        return visit

class Aliquot(Item):
    """ See `IAliquot`
    """
    zope.interface.implements(IAliquot)


    dsid = FieldProperty(IAliquot["dsid"])
    specimen_dsid = FieldProperty(IAliquot["specimen_dsid"])
    type = FieldProperty(IAliquot["type"])
    state = FieldProperty(IAliquot["state"])
    volume = FieldProperty(IAliquot["volume"])
    cell_amount = FieldProperty(IAliquot["cell_amount"])
    store_date = FieldProperty(IAliquot["store_date"])
    freezer = FieldProperty(IAliquot["freezer"])
    rack = FieldProperty(IAliquot["rack"])
    box = FieldProperty(IAliquot["box"])
    storage_site = FieldProperty(IAliquot["storage_site"])
    thawed_num = FieldProperty(IAliquot["thawed_num"])
    analysis_status = FieldProperty(IAliquot["analysis_status"])
    sent_date = FieldProperty(IAliquot["sent_date"])
    sent_name = FieldProperty(IAliquot["sent_name"])
    notes = FieldProperty(IAliquot["notes"])
    sent_notes = FieldProperty(IAliquot["sent_notes"])
    special_instruction = FieldProperty(IAliquot["special_instruction"])

    @classmethod
    def from_rslt(cls, rslt):
        obj = cls()
        obj.dsid = rslt.id
        obj.specimen_dsid = rslt.specimen.id
        if rslt.type is not None:
            type = rslt.type.value
        else:
            type = None
        obj.type = type
        if rslt.state is not None:
            state = rslt.state.value
        else:
            state = None
        obj.state = state
        obj.volume = rslt.volume
        obj.cell_amount = rslt.cell_amount
        obj.store_date = rslt.store_date
        obj.freezer = rslt.freezer
        obj.rack = rslt.rack
        obj.box = rslt.box
        if rslt.storage_site is not None:
            storage_site = rslt.storage_site.value
        else:
            storage_site = None
        obj.storage_site = storage_site
        obj.thawed_num = rslt.thawed_num
        if rslt.analysis_status is not None:
            analysis_status = rslt.analysis_status.value
        else:
            analysis_status = None
        obj.analysis_status = analysis_status
        obj.sent_date = rslt.sent_date
        obj.sent_name = rslt.sent_name
        obj.notes = rslt.notes
        obj.sent_notes = rslt.sent_notes
        if rslt.special_instruction is not None:
            special_instruction = rslt.special_instruction.value
        else:
            special_instruction = None
        obj.special_instruction = special_instruction
        return obj


class SpecimenBlueprint(content.Container):
    zope.interface.implements(ISpecimenBlueprint)
    __doc__ = ISpecimenBlueprint.__doc__

    type = FieldProperty(ISpecimenBlueprint["type"])

    default_tubes = FieldProperty(ISpecimenBlueprint["default_tubes"])

    tube_type = FieldProperty(ISpecimenBlueprint["tube_type"])

    destination = FieldProperty(ISpecimenBlueprint["destination"])

    def createSpecimen(self, subject_zid, protocol_zid, date_collected):
        """
        Build a set of keyword arguements and pass back a specimen matching this blueprint
        """
        intids = zope.component.getUtility(IIntIds)
        blueprint_zid = intids.getId(self)

        kwargs = {}
        kwargs['blueprint_zid'] = blueprint_zid
        kwargs['subject_zid'] = subject_zid
        kwargs['protocol_zid'] = protocol_zid
        kwargs['state'] = u'pending-draw'
        kwargs['date_collected'] = date_collected
        kwargs['type'] = hasattr(self, 'type') and self.type or self.specimen_type
        kwargs['destination'] = self.destination
        kwargs['tubes'] = self.default_tubes
        kwargs['tube_type'] = self.tube_type

        return Specimen(**kwargs)

    def getOmittedFields(self):
        omitted = ['type']
        return omitted

    def getFilter(self, basekw={}, states=[]):
        """
        return a dictionary with keywords for this item based on an existing set of keys
        """
        retkw = {}
        if basekw.has_key('after_date') and basekw['after_date'] is not None and (not basekw.has_key('before_date') or basekw['before_date'] is None):
            basekw['before_date'] = basekw['after_date']
        for key in IFilterForm.names():
            if basekw.has_key(key) and basekw[key] is not None:
                if key == 'show_all':
                    continue
                elif key == 'patient':
                    retkw['subject_zid'] = utils.getPatientForFilter(self, basekw[key])
                elif key == 'type':
                    retkw['type'] = basekw[key]
                elif key == 'after_date':
                    retkw[key] = basekw[key]
                    if not basekw.has_key('before_date') or basekw['before_date'] is None:
                        retkw['before_date'] = basekw[key]
                else:
                    retkw[key] = basekw[key]
        retkw.update({'type':self.type})
        return retkw

    def createAliquotMold(self, specimen):
        """
        Loop through the aliquot in this folder, and 
        create aliquots.
        """
        moldlist = []
        for id, aliquot_blueprint in self.contentItems({'portal_type':'hive.lab.aliquotblueprint'}):
            moldlist.append(aliquot_blueprint.createAliquot(specimen))
        return moldlist
        # Get the transaction and commit it?

class AliquotBlueprint(content.Item):
    zope.interface.implements(IAliquotBlueprint)
    __doc__ = IAliquotBlueprint.__doc__


    type = FieldProperty(IAliquotBlueprint["type"])
    volume = FieldProperty(IAliquotBlueprint["volume"])
    cell_amount = FieldProperty(IAliquotBlueprint["cell_amount"])
    storage_site = FieldProperty(IAliquotBlueprint["storage_site"])
    special_instructions = FieldProperty(IAliquotBlueprint["special_instructions"])


    def createAliquot(self, specimen):
        """
        Creat a mold from this template to create Aliquot
        """
        kwargs = {}
        kwargs['specimen_dsid'] = specimen.dsid
        kwargs['state'] = unicode('pending')
        kwargs['type'] = hasattr(self, 'type') and self.type or self.aliquot_type
        kwargs['volume'] = self.volume
        kwargs['cell_amount'] = self.cell_amount
        kwargs['store_date'] = specimen.date_collected
        kwargs['storage_site'] = self.storage_site
        kwargs['thawed_num'] = 0
        kwargs['special_instruction'] = self.special_instructions

        return Aliquot(**kwargs)

    def getOmittedFields(self):
        omitted = ['type']
        return omitted

    def getFilter(self, basekw={}, states=[]):
        """
        return a dictionary with keywords for this item based on an existing set of keys
        """
        retkw = {}
        if basekw.has_key('after_date') and basekw['after_date'] is not None and (not basekw.has_key('before_date') or basekw['before_date'] is None):
            basekw['before_date'] = basekw['after_date']
        for key in IFilterForm.names():
            if basekw.has_key(key) and basekw[key] is not None:
                if key == 'show_all':
                    continue
                elif key == 'patient':
                    retkw['subject_zid'] = utils.getPatientForFilter(self, basekw[key])
                elif key == 'after_date':
                    retkw[key] = basekw[key]
                    if not basekw.has_key('before_date') or basekw['before_date'] is None:
                        retkw['before_date'] = basekw[key]
                else:
                    retkw[key] = basekw[key]
        retkw.update({'type':self.aliquot_type})
        return retkw

