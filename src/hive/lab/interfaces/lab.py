from hive.lab import MessageFactory as _,\
                     vocabularies
from plone.directives import form
import zope.interface
import zope.schema




class IContainsSpecimen(zope.interface.Interface):
    """
    Marker interface for items that contain Specimen Blueprints
    """
    pass


class ILab(form.Schema, IContainsSpecimen):
    """
    An Interface for the Labs
    """
    pass

class IClinicalLab(ILab):
    """
    An Interface for the Labs
    """
    pass

class IResearchLab(ILab):
    """
    An Interface for the Labs
    """
    pass

class IFilter(zope.interface.Interface):

    def getOmittedFields():
        """
        Return a dictionary of keywords to use in filtering available specimen
        """
        
    def getFilter(basekw, states):
        """
        Return a dictionary of keywords to use in filtering available specimen
        """
        
class IFilterForm(form.Schema):
    """
    """
    patient = zope.schema.TextLine(
        title=_(u"Patient id"),
        description=_(u"Patient OUR#, Legacy AEH ID, or Masterbook Number"),
        required=False
        )

    type = zope.schema.Choice(title=u"Type of Sample",
        source=vocabularies.SpecimenAliquotVocabulary(u"aliquot_type"), required=False
        )
        
    after_date = zope.schema.Date(
        title=_(u"Sample Date"),
        description=_(u"Samples on this date. If Limit Date is set as well, will show samples between those dates"),
        required=False

        )

    before_date = zope.schema.Date(
        title=_(u"Sample Limit Date"),
        description=_(u"Samples before this date. Only applies if Sample Date is also set"),
        required=False
        )

    show_all = zope.schema.Bool(
        title=_(u"Show all Samples"),
        description=_(u"Show all samples, including missing, never drawn, checked out, etc"),
        required=False
        )