from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.ZCatalog.ZCatalog import manage_addZCatalog
from five import grok
from zope.lifecycleevent import IObjectAddedEvent

from occams.lab import MessageFactory as _
from cStringIO import StringIO

from reportlab.graphics.barcode import code39
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from Products.ZCatalog.interfaces import ICatalogBrain

from datetime import date
from occams.lab import interfaces
# ------------------------------------------------------------------------------
# Label Tools Tools|
# --------------
# These classes provide templates for turning records into printable
# labesl
# ------------------------------------------------------------------------------

class LabeledSpecimen(grok.Adapter):
    grok.provides(interfaces.ILabel)
    grok.context(interfaces.ISpecimen)

    @property
    def id(self):
        return self.context.id

    @property
    def patient_title(self):
        return self.context.patient.our

    @property
    def cycle_title(self):
        if self.context.study_cycle_label:
            return self.context.study_cycle_label
        return "%s - %s" %(self.context.cycle.study.short_title, self.context.cycle.week)

    @property
    def sample_date(self):
        if self.context.collect_date:
            return self.context.collect_date.strftime("%m/%d/%Y")
        else:
            return date.today().strftime("%m/%d/%Y")

    @property
    def sample_type(self):
        return self.context.specimen_type.name
        
    @property
    def barcodeline(self):
        return - 1

    @property
    def label_lines(self):
        """
        Generate the lines for a Specimen Label
        """
        line1 = unicode(' '.join([self.context.patient.our , self.sample_date]))
        line2 = unicode(self.cycle_title)
        line3 = unicode(self.sample_type)
        return [line1, line2, line3]

class LabeledAliquot(grok.Adapter):
    grok.provides(interfaces.ILabel)
    grok.context(interfaces.IAliquot)

    @property
    def id(self):
        return self.context.id


    @property
    def patient_title(self):
        return self.context.specimen.patient.our

    @property
    def cycle_title(self):
        if self.context.specimen.study_cycle_label:
            return self.context.specimen.study_cycle_label
        return "%s - %s" %(self.context.specimen.cycle.study.short_title, self.context.specimen.cycle.week)

    @property
    def sample_date(self):
        if self.context.store_date:
            return self.context.store_date.strftime("%m/%d/%Y")
        else:
            return date.today().strftime("%m/%d/%Y")

    @property
    def sample_type(self):
        parts = [self.context.aliquot_type.name,]
        if self.context.cell_amount:
            parts.append("%sx10^6" % self.context.cell_amount)
        elif self.context.volume:
            parts.append("%smL" % self.context.volume)
        if self.context.special_instruction and self.context.special_instruction.name != u'na':
            parts.append(self.context.special_instruction.name)
        return " ".join(parts)

    @property
    def barcodeline(self):
        return 0

    @property
    def label_lines(self):
        """
        Generate the lines for an Aliquot Label
        """
        ## Barcode Line
        line1 = unicode(self.id)
        line2 = unicode('%s OUR# %s ' % (self.id, self.patient_title))
        line3 = unicode(self.sample_date)
        line4 = unicode('%s - %s' %(self.cycle_title, self.sample_type))
        return [line1, line2, line3, line4]


class LabelFromBrain(grok.Adapter):
    grok.provides(interfaces.ILabel)
    grok.context(ICatalogBrain)

    @property
    def id(self):
        return self.context['id']

    @property
    def patient_title(self):
        return self.context['patient_title']

    @property
    def cycle_title(self):
        return self.context['cycle_title']

    @property
    def sample_date(self):
        return self.context['sample_date']

    @property
    def sample_type(self):
        return self.context['sample_type']
        
    @property
    def barcodeline(self):
        return self.context['barcodeline']

    @property
    def label_lines(self):
        return self.context['label_lines']

@grok.subscribe(interfaces.ILabelSheet, IObjectAddedEvent)
def handleLabelSheetAdded(sheet, event):
    """ Clinical Lab added event handler.
        This method will be triggered when an Clinical Lab is added to the
        current Site.
    """
    manage_addZCatalog(sheet, 'labels', u'Labels', REQUEST=None)
    zcat = sheet._getOb('labels')
    label_catalog = zcat._catalog
    for field in interfaces.ILabel.names():
        index = FieldIndex(field)
        label_catalog.addIndex(field, index)
        label_catalog.addColumn(field)

'''
v0.1 by SL Kosakovsky Pond (spond@ucsd.edu)

This file generates PDF documents containing
specimen and aliquot labels for the UCSD AEH
data management system.

The program uses ReportLab Toolkit
(http://www.reportlab.com/software/opensource/rl-toolkit/download/)
for document generation.


Usage example can be found in "tester_stdout" at the bottom of the file
(passing a string filepath instead of sys.stdout will spool the result
to a file at that path).
'''

class LabelGenerator(object):
#    def setup(self, settings, filename, doDrawGrid = False):    
    def __init__(self, context, filename=None):
        '''
        set up the default label drawing canvas
        the resulting PDF will be written to 'filename'
        '''

        self.context = context
        #### Remake the variables to Float
        self.page_width = float(self.context.page_width)
        self.page_height = float(self.context.page_height)
        self.page_width = float(self.context.page_width)
        self.top_margin = float(self.context.top_margin)
        self.side_margin = float(self.context.side_margin)
        self.vert_pitch = float(self.context.vert_pitch)
        self.horz_pitch = float(self.context.horz_pitch)
        self.label_height = float(self.context.label_height)
        self.label_width = float(self.context.label_width)
        self.label_round = float(self.context.label_round)
        self.no_across = int(self.context.no_across)
        self.no_down = int(self.context.no_down)
        
        self.font_face = 'Helvetica'
        self.canvas = self.createCanvas(filename)
        
        self.grid = self.drawGrid()
        self.row = 0
        self.column = -1
        self.rows = self.no_down
        self.cols = self.no_across

    def createCanvas(self, filename=None):
        """
        Create the canvas on which to draw labels
        """
        filetitle = '%s labels' % self.context.title
        if filename is None:
            filename = filetitle
        newcanvas = canvas.Canvas(
                        filename,
                        pagesize=(self.page_width * inch,
                                     self.page_height * inch),
                        )
        newcanvas.setTitle(filetitle)
        newcanvas.setAuthor('UCSD BitCore')
        newcanvas.setSubject('Sample and Aliquot labels')
        newcanvas.setLineCap(1) # round
        newcanvas.setLineJoin(0) # mitre
        newcanvas.setLineWidth(0.1) # line width = 0.5 pts
        newcanvas.setFont(self.font_face, 12)
        return newcanvas
        
    def drawGrid (self):
        '''
        compute the grid of printable labels boxes
        return a list of individual label coordinates
        [bottom left x, bottom left y, width, height] in POINTS
        indexed by [column, row]

        if doDraw = True, then the boxes themselves are drawn
        '''
        labelBoxes = []
        current_x = self.side_margin
        for row in range (self.no_across):
            labelBoxes += [[], ]
            current_y = self.page_height - self.top_margin
            for col in range(self.no_down):
                labelBoxes[len(labelBoxes) - 1] += [[inch * current_x,
                                inch * (current_y - self.label_height),
                                inch * self.label_width,
                                inch * self.label_height], ]
                current_y = current_y - self.vert_pitch
            current_x += self.horz_pitch
        return  labelBoxes

    def addBorder(self):
        """
        Add a border to the labels
        """
        for aColumn in self.grid:
            for aBox in aColumn:
                self.canvas.roundRect(aBox[0], aBox[1], aBox[2], aBox[3], self.label_round * inch)
        return self.grid
        
    def getNextBox(self, startcol=None, startrow=None):
        ''' adjust self.row and self.column to the next available label
            make a new page if necessary '''
        if startcol:
            self.column = startcol - 2
        if startrow:
            self.row = startrow - 1
        self.column += 1
        if self.column == self.cols:
            self.column = 0
            self.row += 1
        if self.row == self.rows:
            self.row = 0
            self.canvas.showPage()
        return(self.row, self.column)

    def writeLabels(self):
        '''
        flush the page and save the file
        '''
        self.canvas.showPage()
        self.canvas.save()

    def createLabel(self, labelines, barcodeline=None, startcol=None, startrow=None):
        """
        Take a set of brains from the catalog and create the labels from that
        set of brains
        """
        if barcodeline is None:
            barcodeline = -1
        nextBox = self.getNextBox(startcol, startrow)
        grid_position = self.grid[nextBox[1]][nextBox[0]]
        self.drawABox(grid_position, labelines, barcodeline)


    def drawABox (self, theBox, labelLines, barCodeLine= -1):
        '''
        draw the text contained in the string list (labelLines), one per line
        font size is computed to fit all the lines vertically, and then readjusted
        to fit inside the box horizontally.
        The lines are rendered top to bottom

        theBox = [bottom left x, bottom left y, width, height] in POINTS

        if barCodeLine is in [0, len(labelLines)-1], then this line is rendered as
        a barcode (Code 39)
        '''

        lineCount = len(labelLines)
        if (lineCount): #things to do
            if barCodeLine >= 0 and barCodeLine < lineCount:
                lineCount += 1
            fontSize = theBox[3] / (1 + lineCount)
            #if fontSize < 7:
            #    fontSize = 7

            margin = fontSize
            availableWidth = theBox[2] - margin * 2

            self.canvas.setFontSize (fontSize - 1)
            self.canvas.saveState()
            p = self.canvas.beginPath()
            p.rect(theBox[0], theBox[1], theBox[2], theBox[3])
            #c.clipPath(p,stroke=0)

            current_y = theBox [1] + theBox[3] - fontSize * 1.2

            for lineIDX, aLine in enumerate(labelLines):
                stringWidth = self.canvas.stringWidth (aLine)

                if stringWidth > availableWidth:
                    self.canvas.setFontSize ((fontSize - 1) * availableWidth / stringWidth)

                if lineIDX == barCodeLine:
                    current_y -= fontSize
                    ratio = 2.2
                    elementWidth = 7 + 2.2 * 3;
                    barcode = code39.Standard39(aLine, barWidth=(availableWidth - 3) / elementWidth / (3 + len(aLine)), ratio=ratio,
                                                     barHeight=2 * fontSize, humanReadable=False, quiet=True, lquiet=1.5, rquiet=1.5)

                    barcode.drawOn(self.canvas, theBox[0] + margin, current_y)
                else:
                    self.canvas.drawString (theBox[0] + margin, current_y, aLine)
                current_y -= fontSize
                self.canvas.setFontSize (fontSize - 1)

            self.canvas.restoreState()

class LabelPrinter(grok.Adapter):
    """
    Print a set of labels
    """
    grok.implements(interfaces.ILabelPrinter)
    grok.context(interfaces.ILabelSheet)

    def getLabelQueue(self):
        lab = self.context
        return lab['labels']

    def getLabelBrains(self):
        queue = self.getLabelQueue()
        return queue(sort_on='id', sort_order='ascending')

    def queueLabel(self, labelable, uid=None):
        """
        Add a label to the cue
        """
        label = interfaces.ILabel(labelable)
        queue = self.getLabelQueue()
        if uid is None:
            uid = label.id
        queue.catalog_object(label, uid=str(uid))

    def purgeLabel(self, uid):
        """
        Remove a label from the queue
        """
        queue = self.getLabelQueue()
        queue.uncatalog_object(str(uid))

    def printLabelSheet(self, label_list, startcol=None, startrow=None):
        """
        Create the label page, and output
        """
        stream = StringIO()
        labelWriter = LabelGenerator(self.context, stream)
        for labelable in label_list:
            label = interfaces.ILabel(labelable)
            labelWriter.createLabel(label.label_lines, label.barcodeline, startcol, startrow)
        labelWriter.writeLabels()
        content = stream.getvalue()
        stream.close()
        return content
