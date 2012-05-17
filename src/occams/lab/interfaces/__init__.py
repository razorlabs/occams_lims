import zope.interface
import zope.schema
from occams.datastore.interfaces import ICategory
from occams.datastore.interfaces import IUser
from occams.form.interfaces import IDataBaseItemContext
from occams.datastore.interfaces import IReferenceable
from occams.datastore.interfaces import IDescribeable
from occams.datastore.interfaces import IModifiable
from plone.directives import form

from avrc.aeh.interfaces import IClinicalModel
from avrc.aeh.interfaces import IPatientModel
from avrc.aeh.interfaces import ICycleModel
from avrc.aeh.interfaces import IVisitModel
from occams.lab import MessageFactory as _

class IOccamsVocabulary(IDescribeable, IReferenceable, IModifiable):
    """
    """

class ISpecimenType(IDescribeable, IReferenceable, IClinicalModel, IModifiable):
    """
    """
    tube_type = zope.schema.TextLine(
        title=_(u"Tube Type"),
        description=_(u"The Type of tube used for this specimen type"),
        required=True
        )

    default_tubes = zope.schema.Int(
        title=_(u'Default tubes count'),
        required=False,
        )

    location= zope.schema.Choice(
        title=_(u"Default Location"),
        description=_(u"The location of the specimen"),
        vocabulary="occams.lab.locationvocabulary",
        required=False
        )

class IAliquotType(IDescribeable, IReferenceable, IClinicalModel, IModifiable):
    """
    """
    specimen_type = zope.schema.Object(
        title=_(u"Specimen Type"),
        description=_(u"The Type specimen from which this aliquot type is derived"),
        required=True,
        schema= ISpecimenType
        )

    location= zope.schema.Choice(
        title=_(u"Default Location"),
        description=_(u"The location of the aliquot"),
        vocabulary="occams.lab.locationvocabulary",
        required=False
        )

class ISpecimen(IReferenceable, IModifiable):
    """
    """
    specimen_type = zope.schema.Object(
        title=_(u"Type"),
        description=_(u"The Type specimen"),
        required=True,
        schema= ISpecimenType
        )

    patient = zope.schema.Object(
        title=_(u"Patient"),
        description=_(u"The source patient"),
        required=True,
        schema= IPatientModel
        )

    cycle = zope.schema.Object(
        title=_(u"Cycle"),
        description=_(u"The cycle for which this specimen was collected"),
        required=True,
        schema= ICycleModel
        )

    visit = zope.schema.Object(
        title=_(u"Visit"),
        description=_(u"The visit for which this specimen was collected"),
        required=True,
        schema= IVisitModel
        )

    state = zope.schema.Choice(
        title=_(u'State'),
        vocabulary="occams.lab.specimenstatevocabulary",
        default='pending-draw',
        )

    collect_date = zope.schema.Date(
        title=_(u'Collect Date'),
        required=False,
        )

    collect_date = zope.schema.Time(
        title=_(u'Collect Time'),
        required=False,
        )

    location =  zope.schema.Choice(
        title=_(u"Location"),
        description=_(u"The location of the specimen"),
        vocabulary="occams.lab.locationvocabulary",
        required=False
        )

    tubes = zope.schema.Int(
        title=_(u"Tubes"),
        description=_(u"Number of Tubes drawn"),
        required=False
        )

    notes = zope.schema.Text(
        title=_(u"Notes"),
        description=_("Notes about this specimen"),
        required=False
        )

    study_cycle_label = zope.schema.TextLine(
        title=_(u"Study Cycle Label"),
        description=_(u"The label text for the specimen tube"),
        required=False
        )

class IAliquot(IReferenceable, IModifiable):
    """
    """

    specimen = zope.schema.Object(
        title=_(u"Specimen"),
        description=_(u"The specimen from which this aliquot came."),
        required=True,
        schema= ISpecimen
        )

    aliquot_type = zope.schema.Object(
        title=_(u"Type"),
        description=_(u"The type of aliquot"),
        required=True,
        schema= IAliquotType
        )

    state = zope.schema.Choice(
        title=_(u'State'),
        vocabulary="occams.lab.aliquotstatevocabulary",
        default='pending',
        )

    labbook = zope.schema.TextLine(
        title=_(u"Lab Book"),
        description=_(u"The Lab Book number"),
        required=False
        )

    volume =  zope.schema.Float(
        title=_(u"Volume"),
        description=_(u"Volume of a liquid aliquot"),
        required=False
        )

    cell_amount =  zope.schema.Float(
        title=_(u"Cell Count"),
        description=_(u"Cell count of an aliquot"),
        required=False
        )

    store_date = zope.schema.Date(
        title=_(u"Storage Date"),
        description=_(u"Date aliquot was stored"),
        required=False
        )

    freezer = zope.schema.TextLine(
        title=_(u"Freezer"),
        description=_(u"The Freezer Location"),
        required=False
        )
    rack = zope.schema.TextLine(
        title=_(u"Rack"),
        description=_(u"The Rack Location"),
        required=False
        )

    box = zope.schema.TextLine(
        title=_(u"Box"),
        description=_(u"The Box Location"),
        required=False
        )

    location =  zope.schema.Choice(
        title=_(u"Location"),
        description=_(u"The location of the specimen"),
        vocabulary="occams.lab.locationvocabulary",
        required=False
        )

    thawed_num = zope.schema.Int(
        title=_(u"Thawed"),
        description=_(u"Number of times thawed"),
        default=0
        )

    inventory_date =  zope.schema.Date(
        title=_(u'Inventory Date'),
        description=_(u"Date last inventoried"),
        required=False,
        )

    sent_date =  zope.schema.Date(
        title=_(u'Sent Date'),
        description=_(u"Date sent for analysis."),
        required=False,
        )

    sent_name = zope.schema.TextLine(
        title=_(u"Sent Name"),
        description=_(u"The name of the aliquot's receiver."),
        required=False,
        )

    sent_notes = zope.schema.Text(
        title=_(u"Sent Notes"),
        description=_("Notes about this aliquot's destination"),
        required=False
        )

    notes =zope.schema.Text(
        title=_(u"Notes"),
        description=_("Notes about this aliquot"),
        required=False
        )

    special_instruction = zope.schema.Choice(
        title=_(u"Special Instructions"),
        description=_(u"Special Instructions for the aliquot"),
        vocabulary="occams.lab.specialinstructionvocabulary",
        required=False
        )

class IContainsSpecimen(zope.interface.Interface):
    """
    Marker interface for items that contain Specimen Blueprints
    """

class IChecklistSupport(zope.interface.Interface):
    """
    Marker interface to search for aliquot associated with a specific item
    """

class ILab(form.Schema, IContainsSpecimen):
    """
    An Interface for the Labs
    """

class IClinicalLab(ILab):
    """
    An Interface for the Labs
    """

class IResearchLab(ILab, IChecklistSupport):
    """
    An Interface for the Labs
    """

class ISpecimenContext(zope.interface.Interface):
    """
    A wrapper context for DataStore entries so they are traversable.
    This allows a wrapped entry to comply with the Acquisition machinery
    in Plone.
    """

    title = zope.schema.TextLine(
        title=u"Title",
        description=u"",
        required=False
        )

    item = zope.schema.Object(
        title=_(u'The specimen type this context wraps'),
        schema=ISpecimenType,
        readonly=True
        )

class IAliquotContext(zope.interface.Interface):
    """
    A wrapper context for DataStore entries so they are traversable.
    This allows a wrapped entry to comply with the Acquisition machinery
    in Plone.
    """

    title = zope.schema.TextLine(
        title=u"Title",
        description=u"",
        required=False
        )

    item = zope.schema.Object(
        title=_(u'The specimen type this context wraps'),
        schema=IAliquotType,
        readonly=True
        )
