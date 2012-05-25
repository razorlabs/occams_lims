import zope.interface
import zope.schema
from occams.datastore.interfaces import ICategory
from occams.datastore.interfaces import IUser
from occams.form.interfaces import IDataBaseItemContext
from occams.datastore.interfaces import IReferenceable
from occams.datastore.interfaces import IDescribeable
from occams.datastore.interfaces import IModifiable
from plone.directives import form

from avrc.aeh.interfaces import IPatientModel
from avrc.aeh.interfaces import ICycleModel
from avrc.aeh.interfaces import IVisitModel
from occams.lab import MessageFactory as _

class IOccamsVocabulary(IDescribeable, IReferenceable, IModifiable):
    """
    """

class ISpecimenType(IDescribeable, IReferenceable, IModifiable):
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

    location_id = zope.schema.Choice(
        title=_(u"Default Location"),
        description=_(u"The location of the specimen"),
        vocabulary="occams.lab.locationvocabulary",
        required=False
        )

class IAliquotType(IDescribeable, IReferenceable, IModifiable):
    """
    """
    specimen_type = zope.schema.Object(
        title=_(u"Specimen Type"),
        description=_(u"The Type specimen from which this aliquot type is derived"),
        required=True,
        schema= ISpecimenType
        )

    location_id = zope.schema.Choice(
        title=_(u"Default Location"),
        description=_(u"The location of the aliquot"),
        vocabulary="occams.lab.locationvocabulary",
        required=False
        )

class ISpecimen(IReferenceable, IModifiable):
    """
    """
    specimen_type = zope.schema.Choice(
        title=_(u"Type"),
        description=_(u"The Type specimen"),
        readonly=True,
        vocabulary="occams.lab.specimentypevocabulary",
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
        )

    collect_date = zope.schema.Date(
        title=_(u'Collect Date'),
        required=False,
        )

    collect_time = zope.schema.Time(
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

class IViewableSpecimen(form.Schema):
    """
    """

    patient_our = zope.schema.TextLine(
        title=_(u"Patient OUR#"),
        description=_(u"The source patient our #"),
        readonly=True
        )

    patient_initials = zope.schema.TextLine(
        title=_(u"Patient Initials"),
        description=_(u"The source patient initials"),
        readonly=True
        )

    cycle_title = zope.schema.TextLine(
        title=_(u"Study/Cycle"),
        description=_(u"The cycle for which this specimen was collected"),
        readonly=True
        )

    visit_zid = zope.schema.Int(
        title=_(u"Visit Id"),
        description=_(u"The visit for which this specimen was collected"),
        readonly=True,
        )

    visit_date = zope.schema.Date(
        title=_(u"Visit Date"),
        description=_(u"The visit for which this specimen was collected"),
        readonly=True,
        )

    specimen_type_name = zope.schema.TextLine(
        title=_(u"Type name"),
        description=_(u"The Type specimen name"),
        readonly=True,
        )

    collect_date = zope.schema.Date(
        title=_(u'Collect Date'),
        required=False,
        )

    collect_time = zope.schema.Time(
        title=_(u'Collect Time'),
        required=False,
        )

    tube_type = zope.schema.TextLine(
        title=_(u"Tube Type"),
        description=_(u""),
        readonly=True
        )
    
    tubes = zope.schema.TextLine(
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

    aliquot_type = zope.schema.Choice(
        title=_(u'Type'),
        description=_(u"The type of aliquot"),
        required=True,
        vocabulary="occams.lab.aliquottypevocabulary",
        )

    state = zope.schema.Choice(
        title=_(u'State'),
        vocabulary="occams.lab.aliquotstatevocabulary",
        default='pending-draw',
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

class IAliquotGenerator(form.Schema):
    """
    Count for number of aliquot duplicates to create
    """
    count = zope.schema.Int(
        title=_(u'Count'),
        description=_(u'Number of aliquot to generate from the specimen'),
        required=False
        )

class IViewableAliquot(form.Schema):
    """
    """

    patient_our = zope.schema.TextLine(
        title=_(u"Patient OUR#"),
        description=_(u"The source patient our #"),
        readonly=True
        )

    patient_legacy_number = zope.schema.TextLine(
        title=_(u"Patient Legacy #"),
        description=_(u"The source patient legacy #"),
        readonly=True
        ) 

    cycle_title = zope.schema.TextLine(
        title=_(u"Study/Cycle"),
        description=_(u"The cycle for which this specimen was collected"),
        readonly=True
        )
    
    vol_count = zope.schema.TextLine(
        title=_(u'Volume / Cell Count'),
        readonly=True,
        )

    frb = zope.schema.TextLine(
        title=_(u'Freezer / Rack / Box'),
        readonly=True,
        )
    thawed_num = zope.schema.Int(
        title=_(u'Thawed'),
        required=False
        )


class ILabelSheet(form.Schema):
    """
        info for building a pdf of labels
    """
    form.fieldset('label-sheet', label=u"Label Sheet",
                  fields=['page_height',
                  'page_width',
                  'top_margin',
                  'side_margin',
                  'vert_pitch',
                  'horz_pitch',
                  'label_height',
                  'label_width',
                  'label_round',
                  'no_across',
                  'no_down'])
                  
    page_height = zope.schema.Float(
        title=_(u"Page Height"),
        required=True
        )
        
    page_width = zope.schema.Float(
        title=_(u"Page Width"),
        required=True
        )

    top_margin = zope.schema.Float(
        title=_(u"Top Margin"),
        required=True
        )
    side_margin = zope.schema.Float(
        title=_(u"Side Margin"),
        required=True
        )
    vert_pitch = zope.schema.Float(
        title=_(u"Vertical Pitch"),
        required=True
        )
        
    horz_pitch = zope.schema.Float(
        title=_(u"Horizontal Pitch"),
        required=True
        )
    label_height = zope.schema.Float(
        title=_(u"Label Height"),
        required=True
        )
    label_width = zope.schema.Float(
        title=_(u"Label Width"),
        required=True
        )
        
    label_round = zope.schema.Float(
        title=_(u"Label Round"),
        required=True
        )

    no_across = zope.schema.Int(
        title=_(u"Number Across"),
        required=True
        )

    no_down = zope.schema.Int(
        title=_(u"Number Down"),
        required=True
        )

zope.interface.alsoProvides(ILabelSheet, form.IFormFieldProvider)

class ILabel(zope.interface.Interface):
    """
    Class that supports transforming an object into a label.
    """
    id = zope.schema.TextLine(
        title=u"Sample ID",
        readonly=True
        )

    patient_title = zope.schema.TextLine(
        title=u"Patient OUR#",
        readonly=True
        )

    cycle_title = zope.schema.TextLine(
        title=u"Study/Cycle",
        readonly=True
        )

    sample_date = zope.schema.TextLine(
        title=u"Date",
        readonly=True
        )
        
    sample_type = zope.schema.TextLine(
        title=u"Sample Type",
        readonly=True
        )

    barcodeline = zope.schema.Int(
        title=u"Barcode Line",
        readonly=True
        )

    label_lines = zope.schema.List(
        title=u"Label Lines",
        value_type=zope.schema.TextLine(),
        readonly=True
        )


class ILabelPrinter(zope.interface.Interface):
    """
    parts needed for label printing to work
    """
    
    def getLabelQueue():
        """
        """
        pass
    
    def queueLabel(labelable):
        """
        Add a label to the cue
        """
        pass
        
    def printLabelSheet(label_list, startcol=None, startrow=None):
        """
        Create the label page, and output
        """
        pass


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
