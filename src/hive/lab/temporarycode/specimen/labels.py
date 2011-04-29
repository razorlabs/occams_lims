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

import datetime, sys

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, mm
from reportlab.graphics.barcode import code39

''' the following dictionary specifies label sheet parameters,
all dimension units are in inches (1 inch = 72 points) '''

global LCRY_1700
global AVERY_5160

LCRY_1700 = {'page_height'    : 11,
                  'page_width'    : 8.5,
                  'top_margin'    : 0.25,
                  'side_margin'    : 0.78,
                  'vert_pitch'    : 0.625,
                  'horz_pitch'    : 1.41,
                  'label_height' : 0.50,
                  'label_width'  : 1.28,
                  'label_round'    : 0.1,
                  'no_across'    : 5,
                  'no_down'        : 17,
                  'font_face'    : 'Helvetica',
                 }

AVERY_5160 =     {'page_height'    : 11,
                  'page_width'    : 8.5,
                  'top_margin'    : 0.5,
                  'side_margin'    : 0.1875,
                  'vert_pitch'    : 1.00,
                  'horz_pitch'    : 2.75,
                  'label_height' : 1.00,
                  'label_width'  : 2.625,
                  'label_round'    : 0.1,
                  'no_across'    : 3,
                  'no_down'        : 10,
                  'font_face'    : 'Helvetica',
                 }


class labelGenerator:
    ''' this class implements a label generator '''

    def __init__ (self, settings, filename, doDrawGrid = False):
        '''
        set up the default label drawing canvas
        the resulting PDF will be written to 'filename'
        '''
        self.settings = settings
        self.filename = filename

        self.c      = canvas.Canvas(self.filename,
                          pagesize = (self.settings["page_width"] * inch,
                                     self.settings["page_height"] * inch),
                          )

        self.grid   = self.drawGrid (self.settings,doDrawGrid)
        self.row    = 0
        self.column = -1
        self.rows     = self.settings['no_down']
        self.cols   = self.settings['no_across']

    def drawGrid (self, settings, doDraw = False):
        '''
        compute the grid of printable labels boxes
        return a list of individual label coordinates
        [bottom left x, bottom left y, width, height] in POINTS
        indexed by [column, row]

        if doDraw = True, then the boxes themselves are drawn
        '''
        self.c.setTitle       ('AEH labels')
        self.c.setAuthor      ('UCSD BEAST')
        self.c.setSubject  ('Sample and Aliquot labels')
        self.c.setLineCap  (1) # round
        self.c.setLineJoin (0) # mitre
        self.c.setLineWidth(0.1) # line width = 0.5 pts
        self.c.setFont       (settings['font_face'],12)

        labelBoxes = []

        current_x = settings['side_margin']

        for row in range (settings['no_across']):
            labelBoxes += [[],]
            current_y = settings ['page_height'] - settings ['top_margin']
            for col in range (settings['no_down']):
                labelBoxes[len(labelBoxes)-1] += [[inch * current_x,
                                inch * (current_y - settings['label_height']),
                                inch * settings['label_width'],
                                inch * settings['label_height']],]

                current_y = current_y - settings['vert_pitch']

            current_x += settings['horz_pitch']

        if doDraw:
            for aColumn in labelBoxes:
                for aBox in aColumn:
                    self.c.roundRect (aBox[0], aBox[1], aBox[2], aBox[3], settings['label_round']*inch)

        return  labelBoxes

    def getNextBox  (self):
        ''' adjust self.row and self.column to the next available label
            make a new page if necessary '''
        self.column += 1
        if self.column == self.cols:
            self.column = 0
            self.row += 1
        if self.row == self.rows:
            self.row = 0
            self.c.showPage()

        return (self.row,self.column)

    def writeLabels (self):
        '''
        flush the page and save the file
        '''
        self.c.showPage()
        self.c.save()

    def drawASpecimenLabel (self,**kwargs):
        ''' draw a specimen label in the next available box
            processed keyword args

            date (string), default is to print today as mm/dd/yyyy
            PID  (string/number), default is "123-456"
            protocol (string), default is ""
            week (number), default is 0
            study (string), default is ""
            type (string), default is ""
        '''

        if "date" in kwargs:
            date = str(kwargs["date"])
        else:
            date = datetime.date.today().strftime ("%m/%d/%Y")

        if "PID" in kwargs:
            PID = str(kwargs["PID"])
        else:
            PID = "123-456"

        if "protocol" in kwargs:
            protocol = str(kwargs["protocol"])
        else:
            protocol = ""

        if "study" in kwargs:
            study = str(kwargs["study"])
        else:
            study = ""

        if "type" in kwargs:
            type = str(kwargs["type"])
        else:
            type = ""

        if "week" in kwargs:
            week = str(kwargs["week"])
        else:
            week = "0"

        nextBox = self.getNextBox()
        self.drawABox    (self.grid[nextBox[1]][nextBox[0]], [PID + ' ' + date, ' '.join([protocol,study, str(week)]), type], )

    def drawAnAliquotLabel (self,**kwargs):
        ''' draw a specimen label in the next available box
            processed keyword args

            date (string), default is to print today as mm/dd/yyyy
            aliquot  (string), default is "000000"; will also display this is a barcode
            PID (string), default is "123-456"
            type (string), default is ""
        '''

        if "date" in kwargs:
            date = str(kwargs["date"])
        else:
            date = datetime.date.today().strftime ("%m/%d/%Y")

        if "PID" in kwargs:
            PID = str(kwargs["PID"])
        else:
            PID = "123-456"

        if "aliquot" in kwargs:
            aliquot = str(kwargs["aliquot"])
        else:
            aliquot = "000000"

        if "type" in kwargs:
            type = str(kwargs["type"])
        else:
            type = ""

        nextBox = self.getNextBox()
        self.drawABox    (self.grid[nextBox[1]][nextBox[0]], [aliquot, aliquot + ' OUR#' +PID + ' ', date, type], 0)

    def drawABox (self, theBox, labelLines, barCodeLine = -1):
        '''
        draw the text contained in the string list (labelLines), one per line
        font size is computed to fit all the lines vertically, and then readjusted
        to fit inside the box horizontally.
        The lines are rendered top to bottom

        theBox = [bottom left x, bottom left y, width, height] in POINTS

        if barCodeLine is in [0, len(labelLines)-1], then this line is rendered as
        a barcode (Code 39)
        '''

        lineCount = len (labelLines)
        if (lineCount): #things to do

            if barCodeLine >=0 and barCodeLine < lineCount:
                lineCount += 1

            fontSize = theBox[3] / (1+lineCount)
            #if fontSize < 7:
            #    fontSize = 7

            margin         = fontSize
            availableWidth = theBox[2] - margin*2

            self.c.setFontSize (fontSize-1)
            self.c.saveState()
            p = self.c.beginPath()
            p.rect(theBox[0],theBox[1],theBox[2],theBox[3])
            #c.clipPath(p,stroke=0)

            current_y = theBox [1] + theBox[3] - fontSize * 1.2

            for lineIDX, aLine in enumerate(labelLines):
                stringWidth = self.c.stringWidth (aLine)

                if stringWidth > availableWidth:
                    self.c.setFontSize ((fontSize-1)*availableWidth/stringWidth)

                if lineIDX == barCodeLine:
                    current_y         -= fontSize
                    ratio               = 2.2
                    elementWidth    = 7+2.2*3;
                    barcode=code39.Standard39(aLine, barWidth=(availableWidth-3)/elementWidth/(3+len(aLine)), ratio = ratio,
                                                     barHeight=2*fontSize,humanReadable=False,quiet=True,lquiet=1.5,rquiet=1.5)

                    barcode.drawOn(self.c,theBox[0] + margin, current_y)
                else:
                    self.c.drawString (theBox[0] + margin, current_y, aLine)
                current_y -= fontSize
                self.c.setFontSize (fontSize-1)

            self.c.restoreState()


def     tester_stdout ():
    ''' a simple function demonstrating label use '''
    labelWriter = labelGenerator(LCRY_1700,sys.stdout)
    for k in range (10):
        labelWriter.drawASpecimenLabel (PID = '012-345', protocol = 'AEH', week = 0, study = '020', type = 'Anal Swab')
    for k in range (10):
        labelWriter.drawAnAliquotLabel (PID = '222-345', aliquot = '5555555', type = 'PBMC 10x10^6', date = "06/05/2004")
    labelWriter.writeLabels()

def     tester_file ():
    ''' a simple function demonstrating label use '''
    labelWriter = labelGenerator(AVERY_5160,'hello.pdf',True)
    for k in range (10):
        labelWriter.drawASpecimenLabel (PID = '012-345', protocol = 'AEH', week = 0, study = '020', type = 'Anal Swab')
    for k in range (10):
        labelWriter.drawAnAliquotLabel (PID = '222-345', aliquot = '5555555', type = 'PBMC 10x10^6', date = "06/05/2004")
    labelWriter.writeLabels()
