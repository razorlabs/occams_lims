from datetime import datetime
from datetime import date
from zope import interface
import zope.schema
from plone.directives import form
from z3c.relationfield.schema import RelationList, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder

from hive.lab.vocabularies import SpecimenVocabulary
from hive.lab import MessageFactory as _
from hive.lab.interfaces.labels import ILabel
from hive.lab import vocabularies
    
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
        source=vocabularies.SpecimenAliquotVocabulary(u"specimen_type")
        )
        
    pretty_tube_type = zope.schema.Choice(
        title=_(u"Tube Type"),
        source=vocabularies.SpecimenAliquotVocabulary(u"specimen_tube_type"),
        )

class ISpecimenBlueprint(form.Schema):
    """
    Blueprint the system can use to create specimen
    """
        
    specimen_type = zope.schema.Choice(
        title=_(u"Specimen Type"),
        source=vocabularies.SpecimenAliquotVocabulary(u"specimen_type")
        )
        
    default_tubes = zope.schema.Int(
        title=_(u'Default tubes count'),
        required=False,
        )
        
    tube_type = zope.schema.Choice(
        title=_(u"Tube Type"),
        source=vocabularies.SpecimenAliquotVocabulary(u"specimen_tube_type"),
        )

    destination = zope.schema.Choice(
        title=_(u"Destination"),
        source=vocabularies.SpecimenAliquotVocabulary(u"specimen_destination"),
        default=u"Richman Lab",
        )
        
class ISpecimenLabel(ILabel):
    """
    A Specimen Label
    """
    pretty_specimen_type = zope.schema.Choice(
        title=_(u"Specimen Type"),
        source=vocabularies.SpecimenAliquotVocabulary(u"specimen_type")
        ) 

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



class ISpecimenSupport(interface.Interface):
    """
    Marker class for items that have specimen associated with them
    """
    def getSpecimen():
        """
        Function that provides specimen associated with the object
        """
    
class IRequestedSpecimen(ISpecimenSupport):
    """
    Marker class for items that require specimen
    """
    
    def getSpecimen():
        """
        Function that provides specimen associated with the object
        """

