from Products.CMFCore.utils import getToolByName

from plone.directives import dexterity

from zope.security import checkPermission
from datetime import date

from five import grok

from hive.lab import MessageFactory as _

from beast.browser import widgets

from beast.browser.crud import NestedFormView, BatchNavigation

from hive.lab.interfaces import IResearchLab
from avrc.data.store.interfaces import ISpecimen
from hive.lab.interfaces import IViewableSpecimen


from z3c.form import field
from z3c.form import button
from z3c.form.interfaces import DISPLAY_MODE
from avrc.data.store.interfaces import IDatastore
from zope.component import  getSiteManager

from plone.z3cform.crud import crud
from hive.lab.browser.clinicallab import SpecimenRequestor
from hive.lab.browser.clinicallab import SpecimenButtonCore
# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
SUCCESS_MESSAGE = _(u"Successfully updated")
PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
NO_CHANGES = _(u"No changes made.")


# ------------------------------------------------------------------------------
# Views
# ------------------------------------------------------------------------------

class View(dexterity.DisplayForm):
    """
    Primary view for a research lab object.
    """
    grok.context(IResearchLab)
    grok.require('zope2.View')

    def __init__(self, context, request):
        super(View, self).__init__(context, request)
        self.aliquot_requestor = self.getFormRequestor()

    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = ReadySpecimen(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view
        
# ------------------------------------------------------------------------------
# Base Form
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Specific forms
# ------------------------------------------------------------------------------
class ReadySpecimen(SpecimenRequestor):
    display1 = field.Fields(IViewableSpecimen, mode=DISPLAY_MODE).\
        select('patient_title', 'patient_legacy_number', 'pretty_specimen_type', 'study_title', 'protocol_title',  'pretty_tube_type')
       
    display2 = field.Fields(ISpecimen, mode=DISPLAY_MODE).\
        select('tubes','date_collected', 'time_collected',  'notes')

    update_schema =  display1 + display2
    
    @property
    def editform_factory(self):
        return ReadySpecimenManager

    @property
    def display_state(self):
        return u"complete"
        
    @property
    def action(self):
        return self.context.absolute_url()


# ------------------------------------------------------------------------------
# Button Base Class
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Buttons For Specific Forms
# ------------------------------------------------------------------------------
 
class ReadySpecimenManager(SpecimenButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Ready selected'), name='ready')
    def handleCompleteDraw(self, action):
        self.changeState(action, 'pending-aliquot','ready')
        self._update_subforms()
        return