from hive.lab import MessageFactory as _
from plone.directives import form
import zope.interface
import zope.schema





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
    dsid = zope.schema.TextLine(
        title=u"Sample ID",
        readonly=True
        )
    patient_title = zope.schema.TextLine(
        title=u"Patient OUR#",
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
 
    date = zope.schema.TextLine(
        title=u"Date",
        readonly=True
        )
        
    pretty_type = zope.schema.TextLine(
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
