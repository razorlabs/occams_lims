from datetime import date

import six
from reportlab.graphics.barcode import code39
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


class SPECIMEN_LABEL_SETTINGS:

    page_height = 11.0
    page_width = 8.5

    top_margin = 0.5
    side_margin = 0.187

    vert_pitch = 1.0
    horz_pitch = 2.75

    label_height = 1.0
    label_width = 2.625
    label_round = 0.1

    no_across = 3
    no_down = 10


class ALIQUOT_LABEL_SETTINGS:

    page_height = 11.0
    page_width = 8.5

    top_margin = 0.24
    side_margin = 0.77

    vert_pitch = 0.63
    horz_pitch = 1.4

    label_height = 0.5
    label_width = 1.28

    label_round = 0.1

    no_across = 5
    no_down = 18


class LabeledSpecimen(object):
    """
    Turns a specimen into a printable label
    """

    def __init__(self, context):
        self.context = context

    @property
    def id(self):
        return self.context.id

    @property
    def patient_title(self):
        return self.context.patient.pid

    @property
    def cycle_title(self):
        cycle = self.context.cycle
        study = cycle.study
        return '%s - %s' % (study.short_title, (cycle.week or cycle.title))

    @property
    def sample_date(self):
        if self.context.collect_date:
            return self.context.collect_date.strftime('%m/%d/%Y')
        else:
            return date.today().strftime('%m/%d/%Y')

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
        line1 = six.text_type(
            ' '.join([self.context.patient.pid, self.sample_date]))
        line2 = six.text_type(self.cycle_title)
        line3 = six.text_type(self.sample_type)
        return [line1, line2, line3]


class LabeledAliquot(object):
    """
    Turns an aliquot into a printable label
    """

    def __init__(self, context):
        self.context = context

    @property
    def id(self):
        return self.context.id

    @property
    def patient_title(self):
        return self.context.specimen.patient.pid

    @property
    def cycle_title(self):
        cycle = self.context.specimen.cycle
        return '%s - %s' % (cycle.study.short_title, cycle.week)

    @property
    def sample_date(self):
        return (self.context.store_date or date.today()).strftime('%m/%d/%Y')

    @property
    def sample_type(self):
        parts = [self.context.aliquot_type.name, ]
        # Use the actual amount
        if self.context._cell_amount:
            parts.append('%sx10^6' % self.context._cell_amount)
        elif self.context._volume:
            parts.append('%smL' % self.context._volume)
        if (self.context.special_instruction
                and self.context.special_instruction.name != u'na'):
            parts.append(self.context.special_instruction.name)
        return ' '.join(parts)

    @property
    def barcodeline(self):
        return 0

    @property
    def label_lines(self):
        """
        Generate the lines for an Aliquot Label
        """
        # Barcode Line
        line1 = six.text_type(self.id)
        line2 = six.text_type('%s OUR# %s ' % (self.id, self.patient_title))
        line3 = six.text_type(self.sample_date)
        line4 = six.text_type('%s - %s' % (self.cycle_title, self.sample_type))
        return [line1, line2, line3, line4]


def printLabelSheet(
        stream, lab, labels, settings, startcol=None, startrow=None):
    """
    Create the label page, and output
    """
    labelWriter = LabelGenerator(lab, settings, stream)

    if startcol > 1:
        labelWriter.column = startcol - 2

    if startrow > 1:
        labelWriter.row = startrow - 1

    for label in labels:
        labelWriter.createLabel(label.label_lines, label.barcodeline)

    labelWriter.writeLabels()


class LabelGenerator(object):
    """
    v0.1 by SL Kosakovsky Pond (spond@ucsd.edu)

    This file generates PDF documents containing
    specimen and aliquot labels for the UCSD AEH
    data management system.

    The program uses ReportLab Toolkit
    (http://www.reportlab.com/software/opensource/rl-toolkit/download/)
    for document generation.


    Usage example can be found in 'tester_stdout' at the bottom of the file
    (passing a string filepath instead of sys.stdout will spool the result
    to a file at that path).
    """

    def __init__(self, context, settings, filename=None):
        """
        set up the default label drawing canvas
        the resulting PDF will be written to 'filename'
        """

        self.context = context

        self.page_width = float(settings.page_width)
        self.page_height = float(settings.page_height)
        self.page_width = float(settings.page_width)
        self.top_margin = float(settings.top_margin)
        self.side_margin = float(settings.side_margin)
        self.vert_pitch = float(settings.vert_pitch)
        self.horz_pitch = float(settings.horz_pitch)
        self.label_height = float(settings.label_height)
        self.label_width = float(settings.label_width)
        self.label_round = float(settings.label_round)
        self.no_across = int(settings.no_across)
        self.no_down = int(settings.no_down)

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
        newcanvas.setLineCap(1)  # round
        newcanvas.setLineJoin(0)  # mitre
        newcanvas.setLineWidth(0.1)  # line width = 0.5 pts
        newcanvas.setFont(self.font_face, 12)
        return newcanvas

    def drawGrid(self):
        """
        compute the grid of printable labels boxes
        return a list of individual label coordinates
        [bottom left x, bottom left y, width, height] in POINTS
        indexed by [column, row]

        if doDraw = True, then the boxes themselves are drawn
        """
        labelBoxes = []
        current_x = self.side_margin
        for row in range(self.no_across):
            labelBoxes += [[], ]
            current_y = self.page_height - self.top_margin
            for col in range(self.no_down):
                labelBoxes[len(labelBoxes) - 1] += [[
                    inch * current_x,
                    inch * (current_y - self.label_height),
                    inch * self.label_width,
                    inch * self.label_height], ]
                current_y = current_y - self.vert_pitch
            current_x += self.horz_pitch
        return labelBoxes

    def addBorder(self):
        """
        Add a border to the labels
        """
        for aColumn in self.grid:
            for aBox in aColumn:
                self.canvas.roundRect(
                    aBox[0],
                    aBox[1],
                    aBox[2],
                    aBox[3],
                    self.label_round * inch)
        return self.grid

    def getNextBox(self, startcol=None, startrow=None):
        """ adjust self.row and self.column to the next available label
            make a new page if necessary """
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
        """
        flush the page and save the file
        """
        self.canvas.showPage()
        self.canvas.save()

    def createLabel(
            self, labelines, barcodeline=None, startcol=None, startrow=None):
        """
        Take a set of brains from the catalog and create the labels from that
        set of brains
        """
        if barcodeline is None:
            barcodeline = -1
        nextBox = self.getNextBox(startcol, startrow)
        grid_position = self.grid[nextBox[1]][nextBox[0]]
        self.drawABox(grid_position, labelines, barcodeline)

    def drawABox(self, theBox, labelLines, barCodeLine=-1):
        """
        draw the text contained in the string list (labelLines), one per line
        font size is computed to fit all the lines vertically, and then
        readjusted to fit inside the box horizontally.
        The lines are rendered top to bottom

        theBox = [bottom left x, bottom left y, width, height] in POINTS

        if barCodeLine is in [0, len(labelLines)-1], then this line is rendered
        as a barcode (Code 39)
        """

        lineCount = len(labelLines)
        if (lineCount):  # things to do
            if barCodeLine >= 0 and barCodeLine < lineCount:
                lineCount += 1
            fontSize = theBox[3] / (1 + lineCount)

            margin = fontSize
            availableWidth = theBox[2] - margin * 2

            self.canvas.setFontSize(fontSize - 1)
            self.canvas.saveState()
            p = self.canvas.beginPath()
            p.rect(theBox[0], theBox[1], theBox[2], theBox[3])

            current_y = theBox[1] + theBox[3] - fontSize * 1.2

            for lineIDX, aLine in enumerate(labelLines):
                stringWidth = self.canvas.stringWidth(aLine)

                if stringWidth > availableWidth:
                    self.canvas.setFontSize(
                        (fontSize - 1) * availableWidth / stringWidth)

                if lineIDX == barCodeLine:
                    current_y -= fontSize
                    ratio = 2.2
                    elementWidth = 7 + 2.2 * 3
                    barcode = code39.Standard39(
                        aLine,
                        barWidth=(
                            (availableWidth - 3) /
                            elementWidth /
                            (3 + len(aLine))),
                        ratio=ratio,
                        barHeight=2 * fontSize,
                        humanReadable=False,
                        quiet=True,
                        lquiet=1.5,
                        rquiet=1.5)

                    barcode.drawOn(self.canvas, theBox[0] + margin, current_y)
                else:
                    self.canvas.drawString(
                        theBox[0] + margin, current_y, aLine)
                current_y -= fontSize
                self.canvas.setFontSize(fontSize - 1)

            self.canvas.restoreState()
