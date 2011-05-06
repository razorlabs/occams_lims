from plone.dexterity import content
import zope.interface
from zope.schema.fieldproperty import FieldProperty
import zope.component

from avrc.data.store.lab import Specimen
from avrc.data.store.interfaces import IDatastore

from hive.lab.interfaces.specimen import ISpecimenBlueprint
from hive.lab.interfaces.aliquot import IAliquotBlueprint


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
        
        sm =  zope.component.getSiteManager(visit)
        ds = sm.queryUtility(IDatastore, 'fia')
        specimen_manager = ds.getSpecimenManager()
        
        kwargs = {}
        kwargs['subject_zid'] = subject_zid
        kwargs['protocol_zid'] = protocol_zid
        kwargs['state'] = u'pending-draw' 
        kwargs['date_collected'] = date_collected
        kwargs['specimen_type'] = self.specimen_type
        kwargs['destination'] = self.destination
        kwargs['tubes'] = self.default_tubes
        kwargs['tube_type'] = self.tube_type
        
        specimen_manager.put(Specimen(**kwargs))

    def aliquotSpecimen(self, specimen):
        """
        Loop through the aliquot in this folder, and 
        create aliquots.
        """
        for blueprint in self.folderContents({'portal_type':'IAliquotBlueprint'}):
            blueprint.createAliquot(specimen)
            
        setattr(specimen, 'state', u'aliquoted')
        
        
        

class AliquotBlueprint(content.Item):
    zope.interface.implements(IAliquotBlueprint)
    __doc__ = IAliquotBlueprint.__doc__
    
    
    
    # 
#     
# 
# class IAliquot(IComponent):
#     """ Mostly copied from aeh forms. Tons of work to do still. """
# 
#     dsid = zope.schema.Int(
#         title=_(u'Data Store Id'),
#         required=False,
#         )
# 
#     specimen_dsid = zope.schema.Int(
#         title=_(u'Data Store Specimen Id'),
#         required=False,
#         )
#     type = zope.schema.TextLine(
#         title=_(u'Type'),
#         )
# 
#     state = zope.schema.TextLine(
#         title=_(u'State'),
#         required=False
#         )
# 
#     volume = zope.schema.Float(
#         title=u'Volume (in ml.)',
#         required=False,
#         )
# 
#     cell_amount = zope.schema.Float(
#         title=_(u'Number of cells'),
#         description=_(u'measured in 10,000 increments'),
#         required=False,
#         )
# 
#     store_date = zope.schema.Date(
#         title=_(u'Store Date'),
#         required=False
#         )
# 
#     freezer = zope.schema.TextLine(
#         title=_(u'Freezer'),
#         required=False,
#         )
# 
#     rack = zope.schema.TextLine(
#         title=_(u'Rack'),
#         required=False,
#         )
# 
#     box = zope.schema.TextLine(
#         title=_(u'Box'),
#         required=False,
#         )
# 
#     thawed_num = zope.schema.Int(
#         title=_(u'Number of times thawed.'),
#         required=False,
#         )
# 
#     analysis_status = zope.schema.TextLine(
#         title=_(u'Sent for analysis?'),
#         required=False
#         )
# 
#     sent_date = zope.schema.Date(
#         title=_(u'Date sent'),
#         required=False
#         )
# 
#     storage_site = zope.schema.TextLine(
#         title=_(u'Enter the site where aliquot was sent'),
#         required=False
#         )
# 
#     sent_name = zope.schema.TextLine(
#         title=_(u'Please enter the name of the person the aliquot was sent to '
#                 u'OR the name of the person who placed the sample '
#                 u'on hold:'),
#         required=False,
#         )
# 
#     notes = zope.schema.Text(
#         title=_(u'Notes on this aliquot (if any):'),
#         required=False
#         )
# 
#     special_instruction = zope.schema.TextLine(
#         title=_(u'Special'),
#         description=u'',
#         required=False,
#         )
