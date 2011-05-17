from Products.CMFCore.utils import getToolByName
from plone.directives import dexterity
from zope.security import checkPermission
from datetime import date
from five import grok
from z3c.form import field
from z3c.form import button
from z3c.form.interfaces import DISPLAY_MODE
from plone.z3cform.crud import crud
from zope.component import  getSiteManager

from beast.browser import widgets
from beast.browser.crud import NestedFormView, BatchNavigation
from avrc.data.store.interfaces import ISpecimen
from avrc.data.store.interfaces import IDatastore

from hive.lab.interfaces.lab import IClinicalLab
from hive.lab.interfaces.specimen import IViewableSpecimen
from hive.lab.interfaces.specimen import ISpecimenLabel
from hive.lab.interfaces.labels import ILabelPrinter
from hive.lab.browser.labels import LabelView
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

class View(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IClinicalLab)
    grok.require('zope2.View')

    def __init__(self, context, request):
        super(View, self).__init__(context, request)
        self.specimen_requestor = self.getFormRequestor()

    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = NewSpecimen(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view


        
class Batched(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IClinicalLab)
    grok.require('zope2.View')

    def __init__(self, context, request):
        super(Batched, self).__init__(context, request)
        self.specimen_requestor = self.getFormRequestor()

    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = BatchedSpecimen(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

class Postponed(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IClinicalLab)
    grok.require('zope2.View')

    def __init__(self, context, request):
        super(Postponed, self).__init__(context, request)
        self.specimen_requestor = self.getFormRequestor()

    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = PostponedSpecimen(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

class Completed(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IClinicalLab)
    grok.require('zope2.View')

    def __init__(self, context, request):
        super(Completed, self).__init__(context, request)
        self.specimen_requestor = self.getFormRequestor()

    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = CompletedSpecimen(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view
 
# ------------------------------------------------------------------------------
# Base Form
# ------------------------------------------------------------------------------

class SpecimenRequestor(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """
    
    def __init__(self,context, request):
        super(SpecimenRequestor, self).__init__(context, request)
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.specimen_manager = ds.getSpecimenManager()
        
    ignoreContext=True
    addform_factory = crud.NullForm
    
    batch_size = 10

    display1 = field.Fields(IViewableSpecimen, mode=DISPLAY_MODE).\
        select('patient_title', 'patient_initials', 'study_title',
       'protocol_title', 'pretty_specimen_type', 'pretty_tube_type')
       
    display2 = field.Fields(ISpecimen).\
        select('tubes','date_collected', 'time_collected',  'notes')

    update_schema =  display1 + display2
 
    @property
    def editform_factory(self):
        raise NotImplementedError

    @property
    def display_state(self):
        raise NotImplementedError
        
    @property
    def action(self):
        raise NotImplementedError

    def updateWidgets(self):
        super(SpecimenRequestor, self).updateWidgets()
        self.update_schema['time_collected'].widgetFactory = widgets.TimeFieldWidget
        self.update_schema['tubes'].widgetFactory = widgets.StorageFieldWidget
        

    def get_items(self):
        specimenlist=[]
        for specimenobj in self.specimen_manager.list_by_state(self.display_state, before_date=date.today()):
            specimenlist.append((specimenobj.dsid, specimenobj))
        return specimenlist


# ------------------------------------------------------------------------------
# Button Base Class
# ------------------------------------------------------------------------------
# 
class SpecimenButtonCore(crud.EditForm):
    label=_(u"")
            
    def render_batch_navigation(self):
        """
        Render the batch navigation to include the default styles for Plone
        """
        navigation = BatchNavigation(self.batch, self.request)
        def make_link(page):
            return "%s?%spage=%s" % (self.request.getURL(), self.prefix, page)
        navigation.make_link = make_link
        return navigation()

    def changeState(self, action, state, acttitle):
        success = SUCCESS_MESSAGE
        no_changes = NO_CHANGES

        selected = self.selected_items()
        if selected:
            for id, specimenobj in selected:
                setattr(specimenobj, 'state', unicode(state))
                newspecimen = self.context.specimen_manager.put(specimenobj)
            self.status = _(u"Your specimen have been %sd." % (acttitle))
        else:
            self.status = _(u"Please select specimen to %s."% (acttitle))

    def saveChanges(self, action):
        success = SUCCESS_MESSAGE
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = NO_CHANGES
        for subform in self.subforms:
            data, errors = subform.extractData()
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            self.context.before_update(subform.content, data)
            specimenobj = ISpecimen(subform.content)
            updated = False
            for prop, value in data.items():
                if hasattr(specimenobj, prop) and getattr(specimenobj, prop) != value:
                    setattr(specimenobj, prop, value)
                    updated = True
                    if status is no_changes:
                        status = success
            if updated:
                newspecimen = self.context.specimen_manager.put(specimenobj)
        self.status = status
            
    def printLabels(self, action):
        success = SUCCESS_MESSAGE
        no_changes = NO_CHANGES
        selected = self.selected_items()
        label_list=[]
        labelsheet = ILabelPrinter(self.context.context)
        for id, item in selected:
            count = item.tubes
            if count is None or count < 1:
                count = 1
            for i in range(count):
                label_list.append(item)
        content = labelsheet.printLabelSheet(label_list)

        self.request.RESPONSE.setHeader("Content-type","application/pdf")
        self.request.RESPONSE.setHeader("Content-disposition",
                                        "attachment;filename=labels.pdf")
        self.request.RESPONSE.setHeader("Cache-Control","no-cache")
        self.request.RESPONSE.write(content)
        self.status = _(u"You print is on its way. Refresh the page to view only unprinted labels.")


# ------------------------------------------------------------------------------
# Specific forms
# ------------------------------------------------------------------------------
class NewSpecimen(SpecimenRequestor):
    @property
    def editform_factory(self):
        return NewSpecimenManager

    @property
    def display_state(self):
        return u"pending-draw"
        
    @property
    def action(self):
        return self.context.absolute_url()


class NewSpecimenManager(SpecimenButtonCore):
    label=_(u"")
        
    @button.buttonAndHandler(_('Save All Changes'), name='update')
    def handleUpdate(self, action):
        self.saveChanges(action)
        self._update_subforms()
        return
        
    @button.buttonAndHandler(_('Print Selected'), name='print')
    def handlePrint(self, action):
        self.saveChanges(action)
        self.printLabels(action)
        return
        
    @button.buttonAndHandler(_('Complete selected'), name='complete')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete','complete')
        self.printLabels(action)
        self._update_subforms()
        return
        
    @button.buttonAndHandler(_('Batch Selected'), name='batched')
    def handleBatchDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'batched','batch')
        self._update_subforms()
        return
        
    @button.buttonAndHandler(_('Postpone Selected'), name='postponed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'postponed','postpone')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Mark Selected Undrawn'), name='cancel')
    def handleCancelDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'rejected','reject')
        self._update_subforms()
        return

# ------------------------------------------------------------------------------

class BatchedSpecimen(SpecimenRequestor):
    @property
    def editform_factory(self):
        return BatchedSpecimenManager

    @property
    def display_state(self):
        return u"batched"
        
    @property
    def action(self):
        return self.context.absolute_url()

class BatchedSpecimenManager(SpecimenButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Save All Changes'), name='update')
    def handleUpdate(self, action):
        self.saveChanges(action)
        return
        
    @button.buttonAndHandler(_('Print Selected'), name='print',)
    def handlePrint(self, action):
        self.saveChanges(action)
        self.queLabels(action)
        return
        
    @button.buttonAndHandler(_('Complete selected'), name='complete')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete','complete')
        self.queLabels(action)
        self._update_subforms()
        return 

# ------------------------------------------------------------------------------
   
class PostponedSpecimen(SpecimenRequestor):
    @property
    def editform_factory(self):
        return PostponedSpecimenManager

    @property
    def display_state(self):
        return u"postponed"
        
    @property
    def action(self):
        return self.context.absolute_url()

class PostponedSpecimenManager(SpecimenButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Save All Changes'), name='update')
    def handleUpdate(self, action):
        self.saveChanges(action)
        return
        
    @button.buttonAndHandler(_('Print Selected'), name='print',)
    def handlePrint(self, action):
        self.saveChanges(action)
        self.queLabels(action)
        self._update_subforms()
        return
        
    @button.buttonAndHandler(_('Complete selected'), name='complete')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete','complete')
        self.queLabels(action)
        self._update_subforms()
        return
        
    @button.buttonAndHandler(_('Batch Selected'), name='batched')
    def handleBatchDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'batched','batch')
        self.queLabels(action)
        self._update_subforms()
        return
        
    @button.buttonAndHandler(_('Mark Selected Undrawn'), name='cancel')
    def handleCancelDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'rejected','reject')
        self._update_subforms()
        return

# ------------------------------------------------------------------------------

class CompletedSpecimen(SpecimenRequestor):

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
        return CompletedSpecimenManager

    @property
    def display_state(self):
        return u"pending-aliquot"
        
    @property
    def action(self):
        return self.context.absolute_url()

    def get_items(self):
        specimenlist=[]
        for state in [u'complete', u'rejected']:
            for specimenobj in self.specimen_manager.list_by_state(state, before_date=date.today(), after_date=date.today()):
                specimenlist.append((specimenobj.dsid, specimenobj))
        return specimenlist
        
class CompletedSpecimenManager(SpecimenButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Recover selected'), name='recover')
    def handleCompleteDraw(self, action):
        self.changeState(action, 'pending-draw','recover')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Print Selected'), name='print',)
    def handlePrint(self, action):
        self.queLabels(action)
        return