from Products.CMFCore.utils import getToolByName
from plone.directives import dexterity
from zope.security import checkPermission
from datetime import date
from five import grok
from z3c.form import field
from z3c.form import button
from z3c.form import form as z3cform
from zope import schema
import zope.component
import os.path
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from Products.statusmessages.interfaces import IStatusMessage

from z3c.form.interfaces import DISPLAY_MODE
from plone.z3cform.crud import crud
from zope.component import  getSiteManager
from zope.app.intid.interfaces import IIntIds

from beast.browser import widgets
from beast.browser.crud import NestedFormView, BatchNavigation
from avrc.data.store.interfaces import ISpecimen
from avrc.data.store.interfaces import IDatastore

from hive.lab.interfaces.lab import IClinicalLab
from hive.lab.interfaces.specimen import IViewableSpecimen
from hive.lab.interfaces.specimen import ISpecimenLabel

from hive.lab.interfaces.specimen import IRequestedSpecimen
from hive.lab.interfaces.specimen import ISpecimenSupport

from hive.lab.browser.clinicallab import SpecimenButtonCore
from hive.lab.browser.clinicallab import SpecimenRequestor
from hive.lab import MessageFactory as _

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
SUCCESS_MESSAGE = _(u"Successfully updated")
PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
NO_CHANGES = _(u"No changes made.")

# ------------------------------------------------------------------------------
# Views
# ------------------------------------------------------------------------------

class SpecimenSupport(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(ISpecimenSupport)
    grok.require('zope2.View')
    grok.name('specimen')

    def __init__(self, context, request):
        super(SpecimenSupport, self).__init__(context, request)
        self.specimen_results = self.getFormRequestor()
        self.specimen_requestor = self.requestSpecimen()

    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AllSpecimen(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

    def requestSpecimen(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = SpecimenAddForm(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

# ------------------------------------------------------------------------------
# Specific forms
# ------------------------------------------------------------------------------
class AllSpecimen(SpecimenRequestor):

    display0 = field.Fields(ISpecimen, mode=DISPLAY_MODE).\
        select('state')

    display1 = field.Fields(IViewableSpecimen, mode=DISPLAY_MODE).\
        select('patient_title', 'patient_initials', 'study_title',
       'protocol_title', 'pretty_specimen_type', 'pretty_tube_type')
       
    display2 = field.Fields(ISpecimen, mode=DISPLAY_MODE).\
        select('tubes','date_collected', 'time_collected',  'notes')

    update_schema =  display0 + display1 + display2
    
    @property
    def editform_factory(self):
        return AllSpecimenManager

    @property
    def display_state(self):
        return u"complete"
        
    @property
    def action(self):
        return self.context.absolute_url()
        
    def get_items(self):
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        specimenlist=[]
        intids = zope.component.getUtility(IIntIds)
        subject = self.context.aq_parent
        subject_zid = intids.getId(subject)
        protocols = self.context.cycles
        date_collected = self.context.visit_date
        specimen_manager = ds.getSpecimenManager()
        for protocol in protocols:
            kwargs = {'subject_zid':subject_zid,'protocol_zid':protocol.to_id,'date_collected':date_collected}
            for specimenobj in specimen_manager.filter_specimen(**kwargs):
                specimenlist.append((specimenobj.dsid, specimenobj))        
        return specimenlist

# ------------------------------------------------------------------------------
# Buttons For Specific Forms
# ------------------------------------------------------------------------------

class AllSpecimenManager(SpecimenButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @button.buttonAndHandler(_('Recover selected'), name='recover')
    def handleCompleteDraw(self, action):
        self.changeState(action, 'pending-draw','recover')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Print Selected'), name='print',)
    def handlePrint(self, action):
        self.queLabels(action)
        return
        
# ------------------------------------------------------------------------------
# Specimen Request Form
# ------------------------------------------------------------------------------

class SpecimenAddForm(z3cform.Form):
    label=_(u'Add Specimen')
    ignoreContext=True

    def __init__(self,context,request):
        super(SpecimenAddForm, self).__init__(context,request)
        self.redirect_url = os.path.join(context.absolute_url(), '@@specimen')


    def specimenVocabulary(self):
        context = self.context.aq_inner
        termlist=[]
        intids = zope.component.getUtility(IIntIds)
        subject_zid = intids.getId(context.aq_parent)
        date_collected=context.visit_date
        for cycle in context.cycles:
            cycle_obj = cycle.to_object
            study = cycle_obj.aq_parent
            study_title = study.Title()
            cycle_title = cycle_obj.Title()

            for related_blueprint in study.related_specimen:
                blueprint = related_blueprint.to_object
                term_title = '%s, %s -- %s' % (study_title, cycle_title, blueprint.Title())
                specimen = blueprint.createSpecimen(subject_zid, cycle.to_id, date_collected)
                termlist.append(SimpleTerm(
                                       title=term_title,
                                       token='%s' % term_title,
                                       value=specimen))
                                       
        return SimpleVocabulary(terms=termlist)

    def update(self):
        available_specimen = schema.List(
            title=_(u'Available Specimen'),
            value_type =   schema.Choice(
                           title=_(u'Available Specimen'),
                           description=_(u''),
                           source=self.specimenVocabulary()
                           )
            )
        available_specimen.__name__ = 'available_specimen'
        self.fields += field.Fields(available_specimen)
        super(SpecimenAddForm, self).update()

    @property
    def action(self):
        return self.redirect_url #self.context.absolute_url(self.redirect_url)

    @button.buttonAndHandler(_('Request More Specimen'), name='requestSpecimen')
    def requestSpecimen(self, action):
        sm =  zope.component.getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        specimen_manager = ds.getSpecimenManager() 
        data, errors = self.extractData()
        messages=IStatusMessage(self.request)
        if errors:
            messages.addStatusMessageself(
                _(u'There was an error with your request.'),
                type='error'
                )
            return
        for specimen in data['available_specimen']:
            specimen_manager.put(specimen)

        return self.request.response.redirect(self.redirect_url)