from avrc.data.store._item import AbstractItem
from hive.lab import utilities as utils
from hive.lab.interfaces.aliquot import IAliquot, IAliquotBlueprint
from hive.lab.interfaces.lab import IFilterForm
from hive.lab.interfaces.specimen import ISpecimen,\
                                         ISpecimenBlueprint
from plone.dexterity import content
from zope.app.intid.interfaces import IIntIds
from zope.schema.fieldproperty import FieldProperty

import zope.component
import zope.interface




class Specimen(AbstractItem):
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
    specimen_type = FieldProperty(ISpecimen['specimen_type'])
    destination = FieldProperty(ISpecimen['destination'])
    tubes = FieldProperty(ISpecimen['tubes'])
    tube_type = FieldProperty(ISpecimen['tube_type'])
    notes = FieldProperty(ISpecimen['notes'])

    @classmethod
    def from_rslt(cls, rslt):
        obj = Specimen()
        obj.dsid = rslt.id
        obj.blueprint_zid = rslt.blueprint_zid
        obj.subject_zid = rslt.subject.zid
        obj.protocol_zid = rslt.protocol.zid
        obj.state = rslt.state.value
        obj.date_collected = rslt.collect_date
        obj.time_collected = rslt.collect_time
        obj.specimen_type = rslt.type.value
        obj.destination = rslt.destination.value
        obj.tubes = rslt.tubes
        obj.tube_type = rslt.tube_type.value
        obj.notes = rslt.notes
        obj.visit_zid = rslt.visit.zid
        return obj

    def visit(self):    
        intids = zope.component.getUtility(IIntIds)
        return intids.getObject(self.visit_zid)

class Aliquot(AbstractItem):
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
    special_instruction = FieldProperty(IAliquot["special_instruction"])

    @classmethod
    def from_rslt(cls, rslt):
        obj = cls()
        obj.dsid = rslt.id
        obj.specimen_dsid = rslt.specimen.id
        obj.type = rslt.type.value
        obj.state = rslt.state.value
        obj.volume = rslt.volume
        obj.cell_amount = rslt.cell_amount
        obj.store_date = rslt.store_date
        obj.freezer = rslt.freezer
        obj.rack = rslt.rack
        obj.box = rslt.box
        obj.storage_site = rslt.storage_site.value
        obj.thawed_num = rslt.thawed_num
        obj.analysis_status = rslt.analysis_status.value
        obj.sent_date = rslt.sent_date
        obj.sent_name = rslt.sent_name
        obj.notes = rslt.notes
        obj.special_instruction = rslt.special_instruction.value
        return obj


class SpecimenBlueprint(content.Container):
    zope.interface.implements(ISpecimenBlueprint)
    __doc__ = ISpecimenBlueprint.__doc__

    specimen_type = FieldProperty(ISpecimenBlueprint["specimen_type"])

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
        kwargs['specimen_type'] = self.specimen_type
        kwargs['destination'] = self.destination
        kwargs['tubes'] = self.default_tubes
        kwargs['tube_type'] = self.tube_type

        return Specimen(**kwargs)

    def getOmittedFields(self):
        omitted=['type']
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
                    retkw['specimen_type'] = basekw[key]
                elif key == 'after_date':
                    retkw[key] = basekw[key]
                    if not basekw.has_key('before_date') or basekw['before_date'] is None:
                        retkw['before_date'] = basekw[key]
                else:
                    retkw[key] = basekw[key]
        retkw.update({'specimen_type':self.specimen_type})
        return retkw
        
    def createAliquotMold(self, specimen):
        """
        Loop through the aliquot in this folder, and 
        create aliquots.
        """
        moldlist = []
        for aliquot_blueprint in self.listFolderContents({'portal_type':'hive.lab.aliquotblueprint'}):
            moldlist.append(aliquot_blueprint.createAliquot(specimen))
        return moldlist
        # Get the transaction and commit it?

class AliquotBlueprint(content.Item):
    zope.interface.implements(IAliquotBlueprint)
    __doc__ = IAliquotBlueprint.__doc__


    aliquot_type = FieldProperty(IAliquotBlueprint["aliquot_type"])
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
        kwargs['type'] = self.aliquot_type
        kwargs['volume'] = self.volume
        kwargs['cell_amount'] = self.cell_amount
        kwargs['store_date'] = specimen.date_collected
        kwargs['storage_site'] = self.storage_site
        kwargs['thawed_num'] = 0
        kwargs['special_instruction'] = self.special_instructions

        return Aliquot(**kwargs)

    def getOmittedFields(self):
        omitted=['type']
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
