""" Custom wigets and overrides. """

import datetime
import re

from zope.schema.interfaces import ITextLine
from zope.schema.interfaces import ITime

from z3c.form import term
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.browser.textarea import TextAreaFieldWidget
from z3c.form.browser.text import TextFieldWidget

from z3c.form.browser import widget
from z3c.form.converter import CalendarDataConverter
from z3c.form.converter import FormatterValidationError
from z3c.form.converter import BaseDataConverter
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import IFormLayer
from z3c.form.interfaces import ITextWidget
from z3c.form.widget import FieldWidget
from z3c.form.widget import Widget

from five import grok

def PolarFieldWidget(field, request):
    """Used by z3c.form"""

    class BoolTerms(term.BoolTerms):
        trueLabel = u"Positive"
        falseLabel = u"Negative"

    widget=RadioFieldWidget(field, request)
    widget.terms=BoolTerms(None, None, None, field, None)
    return widget

def NATFieldWidget(field, request):
    """Used by z3c.form"""

    class BoolTerms(term.BoolTerms):
        trueLabel=u"Preliminary Positive"
        falseLabel=u"Negative"

    widget=RadioFieldWidget(field, request)
    widget.terms=BoolTerms(None, None, None, field, None)
    return widget

def ReactiveFieldWidget(field, request):
    """Used by z3c.form"""

    class BoolTerms(term.BoolTerms):
        trueLabel = u"Positive/Reactive"
        falseLabel = u"Negative/Non-Reactive"

    widget=RadioFieldWidget(field, request)
    widget.terms=BoolTerms(None, None, None, field, None)
    return widget

def YesNoFieldWidget(field, request):
    """Used by z3c.form"""

    class BoolTerms(term.BoolTerms):
        trueLabel = u"Yes"
        falseLabel = u"No"

    widget=RadioFieldWidget(field, request)
    widget.terms=BoolTerms(None, None, None, field, None)
    return widget


def SmallTextAreaFieldWidget(field, request):
    """ Used by z3c.form """
    widget = TextAreaFieldWidget(field, request)
    widget.rows = 5
    return widget

def MediumTextAreaFieldWidget(field, request):
    """ Used by z3c.form """
    widget = TextAreaFieldWidget(field, request)
    widget.rows = 10
    return widget

def LargeTextAreaFieldWidget(field, request):
    """ Used by z3c.form """
    widget = TextAreaFieldWidget(field, request)
    widget.rows = 15
    return widget

# ------------------------------------------------------------------------------
# For lab views
# ------------------------------------------------------------------------------

def StorageFieldWidget(field, request):
    """ Field widget factory.
        Used for rendering input widget for fields that are used for entering
        the storage location (freezer/rack/box) of an aliquot or specimen.
    """
    widget = TextFieldWidget(field, request)
    widget.size = 1
    return widget

def AmountFieldWidget(field, request):
    """ Field widget factory.
        Used for rendering input widget for fields that are used for entering
        the storage location (freezer/rack/box) of an aliquot or specimen.
    """
    widget = TextFieldWidget(field, request)
    widget.size = 10
    return widget

# ------------------------------------------------------------------------------
# Time Widget
# ------------------------------------------------------------------------------

_TIME_REX = re.compile("(\d?\d)\s*:?\s*(\d\d)")

class ITimeWidget(ITextWidget):
    """ Marker interface for our custom time widgets """

class TimeWidget(widget.HTMLTextInputWidget, Widget):
    """ Custom time widget """
    grok.implementsOnly(ITimeWidget)

    klass = u'avrc-aeh-browser-time-widget'
    value = u''
    size = 4

    def update(self):
        super(TimeWidget, self).update()
        widget.addFieldClass(self)

@grok.adapter(ITimeWidget, IFormLayer)
@grok.implementer(IFieldWidget)
def TimeFieldWidget(field, request):
    return FieldWidget(field, TimeWidget(request))

class TimeConverter(CalendarDataConverter, grok.MultiAdapter):
    """ A special data converter for time. Only applies to our custom
        time widget. Processes input values as 24-hour format.
    """
    grok.adapts(ITime, ITimeWidget)
    type = 'time'

    def toWidgetValue(self, value):
        if value is self.field.missing_value:
            return u""
        return u"%02d:%02d" % (value.hour, value.minute)

    def toFieldValue(self, value):
        match = _TIME_REX.search(value)

        if match is None:
            return self.field.missing_value

        hour, minute = match.groups()

        try:
            return datetime.time(int(hour), int(minute))
        except ValueError as err:
            msg = "Invalid time format, must be 24-hour format: %s" % err
            raise FormatterValidationError(msg, value)

# ------------------------------------------------------------------------------
# TextLine Converter
# ------------------------------------------------------------------------------

class DataStripperConverter(BaseDataConverter, grok.MultiAdapter):
    """ Sanitizes user input by stripping trailing and leading whitespace. """
    grok.adapts(ITextLine, ITextWidget)

    def toWidgetValue(self, value):
        if value is self.field.missing_value:
            return u''
        return unicode(value)

    def toFieldValue(self, value):
        if value == u'':
            return self.field.missing_value
        return self.field.fromUnicode(value).strip()
