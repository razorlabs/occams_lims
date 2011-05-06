from datetime import datetime
from datetime import date

from zope import interface

import zope.schema

from plone.directives import form
from hive.lab import MessageFactory as _
from hive.lab.interfaces.labels import ILabel

from hive.lab import utilities as utils
    
class IViewableSpecimen(form.Schema):
 
    patient_title = zope.schema.TextLine(
        title=u"Patient OUR#",
        readonly=True
        )

    patient_initials = zope.schema.TextLine(
        title=u"Initials",
        readonly=True
        )
  
    patient_legacy_number = zope.schema.TextLine(
        title=u"Patient Legacy (AEH) Number",
        readonly=True
        )

    study_title = zope.schema.TextLine(
        title=u"Study",
        readonly=True
        )
 
    protocol_title = zope.schema.TextLine(
        title=u"Protocol Week",
        readonly=True
        )
        
    pretty_specimen_type = zope.schema.Choice(
        title=_(u"Specimen Type"),
        source=utils.SpecimenAliquotVocabulary(u"specimen_type")
        )
        
    pretty_tube_type = zope.schema.Choice(
        title=_(u"Tube Type"),
        source=utils.SpecimenAliquotVocabulary(u"specimen_tube_type"),
        )

class ISpecimenBlueprint(form.Schema):
    """
    Blueprint the system can use to create specimen
    """
    title = zope.schema.TextLine(
        title=_(u'Specimen Title'),
        )
        
    specimen_type_title = zope.schema.TextLine(
        title=_(u'Specimen Type Title'),
        )
    specimen_type = zope.schema.TextLine(
        title=_(u'Specimen Type'),
        )
        
    default_tubes = zope.schema.Int(
        title=_(u'Default tubes count'),
        required=False,
        )

    tube_type_title = zope.schema.TextLine(
        title=_(u'Tube Type Title'),
        )
        
    tube_type = zope.schema.TextLine(
        title=_(u'Tube Type Value'),
        )

class ISpecimenLabel(ILabel):
    """
    A Specimen Label
    """
    
    pretty_specimen_type = zope.schema.Choice(
        title=_(u"Specimen Type"),
        source=utils.SpecimenAliquotVocabulary(u"specimen_type")
        ) 

from z3c.relationfield.schema import RelationList, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder
#from plone.app.dexterity.behaviors.related import IRelatedItems
from hive.lab.vocabularies import SpecimenVocabulary

# class ISpecimenRequests(form.Schema):
#     """
#     """
# 
#                   
#     related_specimen = zope.schema.List(
#         title=_(u'label_related_specimen', default=u'Specimen'),
#         default=[],
#         value_type=zope.schema.Choice(title=u"Specimen",
#                       source=SpecimenVocabulary()),
#         required=False,
#         )
#         
# zope.interface.alsoProvides(ISpecimenRequests, form.IFormFieldProvider)

class IAvailableSpecimen(form.Schema):
    """
    """
    form.fieldset('specimen', label=u"Specimen",
                  fields=['related_specimen'])
                  
    related_specimen = RelationList(
        title=_(u'label_related_specimen', default=u'Available Specimen'),
        default=[],
        value_type=RelationChoice(
            title=u"Specimen", source=ObjPathSourceBinder(
                object_provides=ISpecimenBlueprint.__identifier__
            )
        ),
        required=False)
zope.interface.alsoProvides(IAvailableSpecimen, form.IFormFieldProvider)

class IRequiredSpecimen(form.Schema):
    """
    """
    form.fieldset('specimen', label=u"Specimen",
                  fields=['related_specimen'])
                  
    related_specimen = zope.schema.List(
        title=_(u'label_related_specimen', default=u'Specimen'),
        default=[],
        value_type=zope.schema.Choice(title=u"Specimen",
                      source=SpecimenVocabulary()),
        required=False)
zope.interface.alsoProvides(IRequiredSpecimen, form.IFormFieldProvider)

class IRequestSpecimen(interface.Interface):
    """
    Marker class for items that require specimen
    """
    pass

# class IRequestSpecimen(ISpecimenRequests):
#     """
#     """
#     pass

# 
#     def requestedSpecimen():
#         """ """
#         pass
#         
#     def addRequestedSpecimen():
#         """ """
#         pass
#         
#     def getSpecimenFormList():
#         """ get the list of specimens for this visit """
#         pass
#         
#     def getOptionalSpecimenFormVocabulary():
#         """ get the list of remaining specimens that can be requested """
#         pass
        

        
# class ACDSpecimen(Specimen):
#     interface.implements(ACD)
#     def __init__(self, **kwargs):
#         super(ACDSpecimen, self).__init__(**kwargs)
#         self.specimen_type = u"acd"
#         if self.tubes is None:
#             self.tubes = 3
#         if self.tube_type is None:
#             self.tube_type = u'acdyellowtop'
# 
#     @property
#     def title(self):
#         intids = component.getUtility(IIntIds)
#         cycle = intids.getObject(self.protocol_zid)
#         study = cycle.aq_parent
#         return '%s, %s, %s' % (study.title, cycle.title, "PBMC & Plasma")        


# class IAliquotableSpecimen(ISpecimen):
#     """
#     """
#     def aliquot():
#         """
#         """
# 
# class AliquotableSpecimen(grok.Adapter):
#     """
#     Translates a patient to a datastore subject
#     """
#     grok.context(ISpecimen)
#     grok.provides(IAliquotableSpecimen)
# 
#     def aliquot(self):
# 
#         args = {}
#         args['specimen_dsid'] = self.dsid
#         args['store_date'] = self.date_collected
#         args['notes'] = self.notes
# 
#         newaliquotlist = []
#         if str(self.specimen_type) == 'acd':
#             args['aliquot_type'] = unicode('plasma')
#             args['volume'] = 1.0
#             args['cell_amount'] = None
#             aliquot = Aliquot(**args)
#             newaliquotlist.append(aliquot)
#             
#             args['aliquot_type'] = unicode('pbmc')
#             args['volume'] = None
#             args['cell_amount'] = 5.0
#             aliquot = Aliquot(**args)
#             newaliquotlist.append(aliquot)
#             
#         elif str(self.specimen_type) == 'csf':
#             args['aliquot_type'] = unicode('csfpellet')
#             args['volume'] = None
#             args['cell_amount'] = None
#             aliquot = Aliquot(**args)
#             newaliquotlist.append(aliquot)
#             args['aliquot_type'] = unicode('csf')
#             args['volume'] = None
#             args['cell_amount'] = 1.0
#             aliquot = Aliquot(**args)
#             newaliquotlist.append(aliquot)
#         elif str(self.specimen_type) == 'serum':
#             args['aliquot_type'] = unicode('serum')
#             args['volume'] = 1.0
#             args['cell_amount'] = None
#             aliquot = Aliquot(**args)
#             newaliquotlist.append(aliquot)
#         elif str(self.specimen_type) == 'swab':
#             args['aliquot_type'] = unicode('swab')
#             args['volume'] = None
#             args['cell_amount'] = None
#             aliquot = Aliquot(**args)
#             newaliquotlist.append(aliquot)
#         elif str(self.specimen_type) == 'genital-secretion':
#             args['aliquot_type'] = unicode('gscells')
#             args['volume'] = None
#             args['cell_amount'] = 1.0
#             aliquot = Aliquot(**args)
#             newaliquotlist.append(aliquot)
#             args['aliquot_type'] = unicode('gsplasma')
#             args['volume'] = 1.0
#             args['cell_amount'] = None
#             aliquot = Aliquot(**args)
#             newaliquotlist.append(aliquot)
#         elif str(self.specimen_type) == 'rs-gut':
#             args['aliquot_type'] = unicode('rs-gut')
#             args['volume'] = 1.0
#             args['cell_amount'] = None
#             aliquot = Aliquot(**args)
#             newaliquotlist.append(aliquot)
#         elif str(self.specimen_type) == 'ti-gut':
#             args['aliquot_type'] = unicode('ti-gut')
#             args['volume'] = 1.0
#             args['cell_amount'] = None
#             aliquot = Aliquot(**args)
#             newaliquotlist.append(aliquot)
#         return newaliquotlist
 
 
 
# #----------------------------------------------------------------------------
# # PBMC and Plasma
# #----------------------------------------------------------------------------
# class ACD(ISpecimen):
# 
#     formtitle = interface.Attribute(_(u"PBMC & Plasma"))
# 
# 
# class ACDSpecimen(Specimen):
#     interface.implements(ACD)
#     def __init__(self, **kwargs):
#         super(ACDSpecimen, self).__init__(**kwargs)
#         self.specimen_type = u"acd"
#         if self.tubes is None:
#             self.tubes = 3
#         if self.tube_type is None:
#             self.tube_type = u'acdyellowtop'
# 
#     @property
#     def title(self):
#         intids = component.getUtility(IIntIds)
#         cycle = intids.getObject(self.protocol_zid)
#         study = cycle.aq_parent
#         return '%s, %s, %s' % (study.title, cycle.title, "PBMC & Plasma")
# 
#     def aliquot(self):
#         newaliquotlist = []
#         plasmaargs = {'aliquot_type': u'plasma', 'volume': 1.0}
#         pbmcargs5 = {'aliquot_type': u'pbmc', 'cell_amount': 5.0}
#         pbmcargs10 = {'aliquot_type': u'pbmc', 'cell_amount': 10.0}
#         for i in range(10):
#             plasma = Aliquot(**plasmaargs)
#             newaliquotlist.append(plasma)
#         for i in range(6):
#             pbmc = Aliquot(**pbmcargs5)
#             newaliquotlist.append(pbmc)
#         for i in range(4):
#             pbmc = Aliquot(**pbmcargs10)
#             newaliquotlist.append(pbmc)
#         return newaliquotlist
# 
# # -----------------------------------------------------------------------------
# # CSF
# # -----------------------------------------------------------------------------
# class CSF(ISpecimen):
# 
#     formtitle = interface.Attribute(_(u"CSF Specimen"))
# 
# class CSFSpecimen(Specimen):
#     interface.implements(CSF)
# 
#     def __init__(self, **kwargs):
#         super(CSFSpecimen, self).__init__(**kwargs)
#         self.specimen_type = u"csf"
#         if self.tubes is None:
#             self.tubes = 2
#         if self.tube_type is None:
#             self.tube_type = u'csf'
# 
#     @property
#     def title(self):
#         intids = component.getUtility(IIntIds)
#         cycle = intids.getObject(self.protocol_zid)
#         study = cycle.aq_parent
#         return '%s, %s, %s' % (study.title, cycle.title, "CSF Specimen")
# 
#     def aliquot(self):
#         newaliquotlist = []
#         csfpelletargs = {'aliquot_type': u'csfpellet'}
#         csfargs = {'aliquot_type': u'csf', 'volume':1.0}
# 
#         csfpellet = Aliquot(**csfpelletargs)
#         newaliquotlist.append(csfpellet)
# 
#         for i in range(4):
#             csf = Aliquot(**csfargs)
#             newaliquotlist.append(csf)
#         return newaliquotlist
# 
# 
# # -----------------------------------------------------------------------------
# # Serum Bank
# # -----------------------------------------------------------------------------
# 
# class Serum(ISpecimen):
# 
#     formtitle = interface.Attribute(_(u"Serum Specimen"))
# 
# class SerumSpecimen(Specimen):
#     interface.implements(Serum)
# 
#     def __init__(self, **kwargs):
#         super(SerumSpecimen, self).__init__(**kwargs)
#         self.specimen_type = u"serum"
#         if self.tubes is None:
#             self.tubes = 1
#         if self.tube_type is None:
#             self.tube_type = u'10mlsst'
# 
#     @property
#     def title(self):
#         intids = component.getUtility(IIntIds)
#         cycle = intids.getObject(self.protocol_zid)
#         study = cycle.aq_parent
#         return '%s, %s, %s' % (study.title, cycle.title, "Serum Specimen")
# 
# 
#     def aliquot(self):
#         newaliquotlist = []
#         serumargs = {'aliquot_type': u'serum', 'volume':1.0}
# 
#         for i in range(2):
#             serum = Aliquot(**serumargs)
#             newaliquotlist.append(serum)
#         return newaliquotlist
# 
# # -----------------------------------------------------------------------------
# # HSV Anal PCR
# # -----------------------------------------------------------------------------
# 
# class AnalSwab(ISpecimen):
# 
#     formtitle = interface.Attribute(_(u"Anal Swab"))
# 
# class AnalSwabSpecimen(Specimen):
#     interface.implements(AnalSwab)
# 
#     def __init__(self, **kwargs):
#         super(AnalSwabSpecimen, self).__init__(**kwargs)
#         self.specimen_type = u"swab"
#         if self.tubes is None:
#             self.tubes = 1
#         if self.tube_type is None:
#             self.tube_type = u'dacronswab'
# 
#     @property
#     def title(self):
#         intids = component.getUtility(IIntIds)
#         cycle = intids.getObject(self.protocol_zid)
#         study = cycle.aq_parent
#         return '%s, %s, %s' % (study.title, cycle.title, "Anal Swab")
# 
#     def aliquot(self):
#         newaliquotlist = []
#         swabargs = {'aliquot_type': u'swab'}
# 
#         swab = Aliquot(**swabargs)
#         newaliquotlist.append(swab)
# 
#         return newaliquotlist
# 
# 
# # -----------------------------------------------------------------------------
# # Genital Secretions
# # -----------------------------------------------------------------------------
# 
# class GenitalSecretions(ISpecimen):
# 
#     formtitle = interface.Attribute(_(u"Genital Secretions"))
# 
# class GSSpecimen(Specimen):
#     interface.implements(GenitalSecretions)
# 
#     def __init__(self, **kwargs):
#         super(GSSpecimen, self).__init__(**kwargs)
#         self.specimen_type = u"genital-secretion"
#         if self.tube_type is None:
#             self.tube_type = u'gskit'
# 
#     @property
#     def title(self):
#         intids = component.getUtility(IIntIds)
#         cycle = intids.getObject(self.protocol_zid)
#         study = cycle.aq_parent
#         return '%s, %s, %s' % (study.title, cycle.title, "Genital Secretions")
# 
# 
#     def aliquot(self):
#         newaliquotlist = []
#         gscellsargs = {'aliquot_type': u'gscells', 'cell_amount':1.0}
#         gsplasmaargs = {'aliquot_type': u'gsplasma', 'volume':1.0}
# 
#         for i in range(4):
#             gscells = Aliquot(**gscellsargs)
#             newaliquotlist.append(gscells)
#         for i in range(5):
#             gsplasma = Aliquot(**gsplasmaargs)
#             newaliquotlist.append(gsplasma)
# 
#         return newaliquotlist
# 
# # -----------------------------------------------------------------------------
# # Recto-Signmoidal-Gut
# # -----------------------------------------------------------------------------
# 
# class RSGut(ISpecimen):
# 
#     formtitle = interface.Attribute(_(u"RS-GUT Specimen"))
# 
# class RSGutSpecimen(Specimen):
#     interface.implements(RSGut)
# 
#     def __init__(self, **kwargs):
#         super(RSGutSpecimen, self).__init__(**kwargs)
#         self.specimen_type = u"rs-gut"
#         self.tubes = 1
#         self.tube_type = u"rs-gut"
# 
# 
#     @property
#     def title(self):
#         intids = component.getUtility(IIntIds)
#         cycle = intids.getObject(self.protocol_zid)
#         study = cycle.aq_parent
#         return '%s, %s, %s' % (study.title, cycle.title, "RS-GUT Specimen")
# 
#     def aliquot(self):
#         return [Aliquot(aliquot_type=u"rs-gut", volume=1.0)]
# 
# # -----------------------------------------------------------------------------
# # Terminal-Ilial Gut
# # -----------------------------------------------------------------------------
# 
# class TIGut(ISpecimen):
# 
#     formtitle = interface.Attribute(_(u"TI-GUT Specimen"))
# 
# class TIGutSpecimen(Specimen):
#     interface.implements(TIGut)
# 
#     def __init__(self, **kwargs):
#         super(TIGutSpecimen, self).__init__(**kwargs)
#         self.specimen_type = u"ti-gut"
#         self.tubes = 1
#         self.tube_type = u"ti-gut"
# 
#     @property
#     def title(self):
#         intids = component.getUtility(IIntIds)
#         cycle = intids.getObject(self.protocol_zid)
#         study = cycle.aq_parent
#         return '%s, %s, %s' % (study.title, cycle.title, "TI-GUT Specimen")
# 
#     def aliquot(self):
#         return [Aliquot(aliquot_type=u"ti-gut", volume=1.0)]
# 
# 
# # -----------------------------------------------------------------------------
# # -----------------------------------------------------------------------------
# 
# 
# # class SpecimenToDSSpecimen(grok.Adapter):
# #     """
# #     Translates a patient to a datastore subject
# #     """
# #     grok.context(interface.Interface)
# #     grok.provides(IDSSpecimen)
# # 
# #     subject_zid = FieldProperty(IDSSpecimen['subject_zid'])
# #     protocol_zid = FieldProperty(IDSSpecimen['protocol_zid'])
# #     state = FieldProperty(IDSSpecimen['state'])
# #     date_collected = FieldProperty(IDSSpecimen['date_collected'])
# #     time_collected = FieldProperty(IDSSpecimen['time_collected'])
# #     specimen_type = FieldProperty(IDSSpecimen['specimen_type'])
# #     destination = FieldProperty(IDSSpecimen['destination'])
# #     tubes = FieldProperty(IDSSpecimen['tubes'])
# #     tube_type = FieldProperty(IDSSpecimen['tube_type'])
# #     notes = FieldProperty(IDSSpecimen['notes'])
# # 
# # 
# #     def __init__(self, context):
# #         self.context = context
# #         ## This context doesn't exist in plone, so fake things if necessary
# # 
# #         self.dsid = getattr(context, 'dsid', None)
# #         self.subject_zid = context.subject_zid
# #         self.protocol_zid = context.protocol_zid
# #         self.state = context.state
# #         self.date_collected = context.date_collected
# #         self.time_collected = context.time_collected
# #         self.specimen_type = context.specimen_type
# #         self.destination = context.destination
# #         self.tubes = context.tubes
# #         self.tube_type = context.tube_type
# #         self.notes = context.notes
# 
# # 
# # class DSSpecimenToSpecimen(Specimen, grok.Adapter):
# #     """
# #     Translates a patient to a datastore subject
# #     """
# #     grok.context(interface.Interface)
# #     grok.provides(ISpecimen)
# # 
# #     def __init__(self, context):
# #         self.context = context
# #         ## This context doesn't exist in plone, so fake things if necessary
# #         self.dsid = context.dsid
# #         self.subject_zid = context.subject_zid
# #         self.protocol_zid = context.protocol_zid
# #         self.state = context.state
# #         self.date_collected = context.date_collected
# #         self.time_collected = context.time_collected
# #         self.specimen_type = context.specimen_type
# #         self.destination = context.destination
# #         self.tubes = context.tubes
# #         self.tube_type = context.tube_type
# #         self.notes = context.notes
# # 


# # class IAliquotableSpecimen(ISpecimen):
# #     """
# #     """
# #     def aliquot():
# #         """
# #         """
# # 
# # class AliquotableSpecimen(grok.Adapter):
# #     """
# #     Translates a patient to a datastore subject
# #     """
# #     grok.context(interface.Interface)
# #     grok.provides(IAliquotableSpecimen)
# # 
# #     dsid = FieldProperty(ISpecimen['dsid'])
# #     protocol_zid = FieldProperty(ISpecimen['protocol_zid'])
# #     subject_zid = FieldProperty(ISpecimen['subject_zid'])
# #     state = FieldProperty(ISpecimen['state'])
# #     date_collected = FieldProperty(ISpecimen['date_collected'])
# #     time_collected = FieldProperty(ISpecimen['time_collected'])
# #     specimen_type = FieldProperty(ISpecimen['specimen_type'])
# #     destination = FieldProperty(ISpecimen['destination'])
# #     tubes = FieldProperty(ISpecimen['tubes'])
# #     tube_type = FieldProperty(ISpecimen['tube_type'])
# #     notes = FieldProperty(ISpecimen['notes'])
# # 
# #     def __init__(self, context):
# #         self.context = context
# #         ## This context doesn't exist in plone, so fake things if necessary
# #         self.dsid = context.dsid
# #         self.subject_zid = context.subject_zid
# #         self.protocol_zid = context.protocol_zid
# #         self.state = context.state
# #         self.date_collected = context.date_collected
# #         self.time_collected = context.time_collected
# #         self.specimen_type = context.specimen_type
# #         self.destination = context.destination
# #         self.tubes = context.tubes
# #         self.tube_type = context.tube_type
# #         self.notes = context.notes
# # 
# # 
# #     def aliquot(self):
# # 
# #         args = {}
# #         args['specimen_dsid'] = self.dsid
# #         args['store_date'] = self.date_collected
# #         args['notes'] = self.notes
# # 
# #         newaliquotlist = []
# # 
# #         if str(self.specimen_type) == 'acd':
# #             args['aliquot_type'] = unicode('plasma')
# #             args['volume'] = 1.0
# #             args['cell_amount'] = None
# #             aliquot = Aliquot(**args)
# #             newaliquotlist.append(aliquot)
# #             args['aliquot_type'] = unicode('pbmc')
# #             args['volume'] = None
# #             args['cell_amount'] = 5.0
# #             aliquot = Aliquot(**args)
# #             newaliquotlist.append(aliquot)
# #         elif str(self.specimen_type) == 'csf':
# #             args['aliquot_type'] = unicode('csfpellet')
# #             args['volume'] = None
# #             args['cell_amount'] = None
# #             aliquot = Aliquot(**args)
# #             newaliquotlist.append(aliquot)
# #             args['aliquot_type'] = unicode('csf')
# #             args['volume'] = None
# #             args['cell_amount'] = 1.0
# #             aliquot = Aliquot(**args)
# #             newaliquotlist.append(aliquot)
# #         elif str(self.specimen_type) == 'serum':
# #             args['aliquot_type'] = unicode('serum')
# #             args['volume'] = 1.0
# #             args['cell_amount'] = None
# #             aliquot = Aliquot(**args)
# #             newaliquotlist.append(aliquot)
# #         elif str(self.specimen_type) == 'swab':
# #             args['aliquot_type'] = unicode('swab')
# #             args['volume'] = None
# #             args['cell_amount'] = None
# #             aliquot = Aliquot(**args)
# #             newaliquotlist.append(aliquot)
# #         elif str(self.specimen_type) == 'genital-secretion':
# #             args['aliquot_type'] = unicode('gscells')
# #             args['volume'] = None
# #             args['cell_amount'] = 1.0
# #             aliquot = Aliquot(**args)
# #             newaliquotlist.append(aliquot)
# #             args['aliquot_type'] = unicode('gsplasma')
# #             args['volume'] = 1.0
# #             args['cell_amount'] = None
# #             aliquot = Aliquot(**args)
# #             newaliquotlist.append(aliquot)
# #         elif str(self.specimen_type) == 'rs-gut':
# #             args['aliquot_type'] = unicode('rs-gut')
# #             args['volume'] = 1.0
# #             args['cell_amount'] = None
# #             aliquot = Aliquot(**args)
# #             newaliquotlist.append(aliquot)
# #         elif str(self.specimen_type) == 'ti-gut':
# #             args['aliquot_type'] = unicode('ti-gut')
# #             args['volume'] = 1.0
# #             args['cell_amount'] = None
# #             aliquot = Aliquot(**args)
# #             newaliquotlist.append(aliquot)
# #         return newaliquotlist
