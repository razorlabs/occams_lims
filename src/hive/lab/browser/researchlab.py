from Products.CMFCore.utils import getToolByName
from plone.directives import dexterity
from plone.directives import form

from zope.security import checkPermission
from datetime import date
from five import grok
from zope.component import  getSiteManager
from z3c.form import field
from z3c.form import button
from z3c.form.interfaces import DISPLAY_MODE
from plone.z3cform.crud import crud

from hive.lab import MessageFactory as _
from z3c.form import form as z3cform

from beast.browser import widgets
from beast.browser.crud import NestedFormView, BatchNavigation
from avrc.data.store.interfaces import ISpecimen
from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import IAliquot

from hive.lab.interfaces.lab import IResearchLab
from hive.lab.interfaces.specimen import IViewableSpecimen
from hive.lab.interfaces.specimen import IBlueprintForSpecimen

from hive.lab.interfaces.aliquot import IViewableAliquot
from hive.lab.interfaces.aliquot import IAliquotGenerator
from hive.lab.interfaces.labels import ILabelPrinter
from hive.lab.browser.clinicallab import SpecimenRequestor
from hive.lab.browser.clinicallab import SpecimenButtonCore
from hive.lab.browser.labels import LabelView

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
        self.form_requestor = self.getFormRequestor()
        self.aliquot_molder = self.getSpecimenRequestor()

    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = PendingSpecimen(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

    def getSpecimenRequestor(self):
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

class Ready(dexterity.DisplayForm):
    """
    Primary view for a research lab object.
    """
    grok.context(IResearchLab)
    grok.require('zope2.View')

    def __init__(self, context, request):
        super(Ready, self).__init__(context, request)
        self.form_requestor = self.getFormRequestor()

    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotRequestor(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

class Prepared(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('zope2.View')

    def __init__(self, context, request):
        super(Prepared, self).__init__(context, request)
        self.form_requestor = self.getFormRequestor()
        self.label_requestor = self.getLabelRequestor()

    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotChecker(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view
        
    def getLabelRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = LabelView(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view
        
class Completed(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('zope2.View')

    def __init__(self, context, request):
        super(Completed, self).__init__(context, request)
        self.form_requestor = self.getFormRequestor()

    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = CompletedAliquot(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view


class AliquotEditView(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('zope2.View')
    grok.name('edit-aliquot')
    
    def __init__(self, context, request):
        super(AliquotEditView, self).__init__(context, request)

        self.form_requestor = self.getFormRequestor()

        
    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotEditor(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

class AliquotCheckoutView(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('zope2.View')
    grok.name('checkout-aliquot')
    
    def __init__(self, context, request):
        super(AliquotCheckoutView, self).__init__(context, request)

        self.form_requestor = self.getFormRequestor()
        self.form_updater = self.getUpdater()

        
    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotCheckout(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view



    def getUpdater(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotCheckoutUpdate(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view
        
# ------------------------------------------------------------------------------
# Specific Specimen forms
# ------------------------------------------------------------------------------

class PendingSpecimen(SpecimenRequestor):
    display1 = field.Fields(IViewableSpecimen, mode=DISPLAY_MODE).\
        select('patient_title', 'patient_legacy_number', 'pretty_specimen_type', 'study_title', 'protocol_title',  'pretty_tube_type')
       
    display2 = field.Fields(ISpecimen, mode=DISPLAY_MODE).\
        select('tubes','date_collected', 'time_collected',  'notes')

    update_schema =  display1 + display2
    
    @property
    def editform_factory(self):
        return crud.NullForm

    @property
    def action(self):
        return self.context.absolute_url()

    def get_items(self):
        specimenlist=[]
        for specimenobj in self.specimen_manager.filter_specimen(before_date=date.today(), after_date=date.today()):
            specimenlist.append((specimenobj.dsid, specimenobj))
        return specimenlist


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




class ReadySpecimenManager(SpecimenButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Ready selected'), name='ready')
    def handleCompleteDraw(self, action):
        self.changeState(action, 'pending-aliquot','ready')
        self._update_subforms()
        return


class AliquotCreator(SpecimenButtonCore):
    label=_(u"")
    
    def changeSpecimenState(self, action, state, acttitle):
        success = SUCCESS_MESSAGE
        no_changes = NO_CHANGES

        selected = self.selected_items()
        if selected:

            for id, aliquottemplate in selected:
                specimenobj = self.context.specimen_manager.get(aliquottemplate.specimen_dsid)
                setattr(specimenobj, 'state', unicode(state))
                newspecimen = self.context.specimen_manager.put(specimenobj)
            self.status = _(u"Your specimen have been %sd." % (acttitle))
        else:
            self.status = _(u"Please select specimen to %s."% (acttitle))

    @button.buttonAndHandler(_('Create Aliquot'), name='aliquot')
    def handleCreateAliquot(self, action):
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Aliquot.")
            return
        success = _(u"Successfully Aliquoted")
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = _(u"No Aliquot Entered.")

        for subform in self.subforms:
            data, errors = subform.extractData()
            if not data['select'] or not data['count']:
                continue
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue

            blueprint = subform.content
            count = 0
            aliquotlist=[]

            for prop, value in data.items():
                if prop == 'select':
                    continue
                elif prop == 'count':
                    count = value
                elif hasattr(blueprint, prop):
                    setattr(blueprint, prop, value)
            for i in range(count):
                if hasattr(blueprint, 'dsid'):
                    # the put has updated blueprint. reset it.
                    blueprint.dsid=None
                newaliquot = self.context.aliquot_manager.put(blueprint)
            if status is no_changes:
                status = success
        self.status = status
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Mark Specimen Complete'), name='complete')
    def handleCompleteSpecimen(self, action):
        self.changeSpecimenState(action, 'aliquoted','complete')
        self._update_subforms()
        return
# ------------------------------------------------------------------------------
# Aliquot Buttons
# ------------------------------------------------------------------------------

class AliquotButtonCore(crud.EditForm):
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
        
    def changeAliquotState(self, action, state, acttitle):
        success = SUCCESS_MESSAGE
        no_changes = NO_CHANGES
        
        selected = self.selected_items()
        if selected:
            for id, aliquotobj in selected:
                setattr(aliquotobj, 'state', unicode(state))
                newaliquot = self.context.aliquot_manager.put(aliquotobj)
            self.status = _(u"Your aliquot have been %sd." % (acttitle))
        else:
            self.status = _(u"Please select aliquot to %s."% (acttitle))
             
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
            aliquotobj = subform.content
            updated = False
            for prop, value in data.items():
                if hasattr(aliquotobj, prop) and getattr(aliquotobj, prop) != value:
                    setattr(aliquotobj, prop, value)
                    updated = True
                    if status is no_changes:
                        status = success
            if updated:
                newspecimen = self.context.aliquot_manager.put(aliquotobj)
        self.status = status


    def queLabels(self, action):
        success = SUCCESS_MESSAGE
        no_changes = NO_CHANGES
        selected = self.selected_items()
        if selected:
            labelsheet = ILabelPrinter(self.context.context)
            for id, aliquotobj in selected:
                labelsheet.queLabel(aliquotobj)
            self.status = _(u"Your aliquot have been qued.")
        else:
            self.status = _(u"Please select aliquot to que.")


# ----------------------------------------------

class AliquotVerifier(AliquotButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass
        
    @button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        self._update_subforms()
        return
        
    @button.buttonAndHandler(_('Check In Aliquot'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.queLabels(action)
        self.changeAliquotState(action, 'checked-in', 'Check In')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Print Selected'), name='print')
    def handlePrintAliquot(self, action):
        self.saveChanges(action)
        self.queLabels(action)
        return

    @button.buttonAndHandler(_('Mark Aliquot Unused'), name='unused')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeAliquotState(action, 'unused', 'Unused')
        self._update_subforms()
        return

class AliquotEditManager(AliquotButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass
        
    @button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        self._update_subforms()
        return
        
    @button.buttonAndHandler(_('Check Back In'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeAliquotState(action, 'checked-in', 'Check In')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Check Out'), name='checkout')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeAliquotState(action, 'pending-checkout', 'checkout')
        self._update_subforms()
        return

class AliquotCheckoutManager(AliquotButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @button.buttonAndHandler(_('Complete Check Out'), name='checkout')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeAliquotState(action, 'checked-out', 'checkout')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Return To Hold'), name='hold')
    def handleCheckinAliquot(self, action):
        self.changeAliquotState(action, 'hold', 'Hold')
        self._update_subforms()
        return
        
    @button.buttonAndHandler(_('Check Back In'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.changeAliquotState(action, 'checked-in', 'Check In')
        self._update_subforms()
        return



class AliquotRecoverer(AliquotButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass
        
    @button.buttonAndHandler(_('Recover Aliquot'), name='recover')
    def handleRecoverAliquot(self, action):
        self.changeAliquotState(action, 'pending', 'Recover')
        self._update_subforms()
        return

# ------------------------------------------------------------------------------
# Base Form
# ------------------------------------------------------------------------------

class AliquotRequestorCore(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """
    
    def __init__(self,context, request):
        super(AliquotRequestorCore, self).__init__(context, request)
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.aliquot_manager = ds.getAliquotManager()
        self.display0 = field.Fields(IAliquot, mode=DISPLAY_MODE).\
            select('dsid')
            
        self.display1 = field.Fields(IViewableAliquot, mode=DISPLAY_MODE).\
            select('patient_title', 'patient_legacy_number', 'study_title',
           'protocol_title', 'pretty_aliquot_type')
           
        self.display2 = field.Fields(IAliquot).\
            select('volume','cell_amount', 'store_date', 'freezer','rack','box')
    
        self.display3 = field.Fields(IViewableAliquot).\
            select('special_instruction')

        self.display4 = field.Fields(IAliquot).\
        select('notes')
        
    ignoreContext=True
    addform_factory = crud.NullForm
    batch_size = 20

    @property
    def update_schema(self):
        return self.display0 + self.display1 + self.display2 + self.display3 + self.display4

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
        super(AliquotRequestorCore, self).updateWidgets()
        self.update_schema['volume'].widgetFactory = widgets.AmountFieldWidget
        self.update_schema['cell_amount'].widgetFactory = widgets.AmountFieldWidget
        self.update_schema['freezer'].widgetFactory = widgets.StorageFieldWidget
        self.update_schema['rack'].widgetFactory = widgets.StorageFieldWidget
        self.update_schema['box'].widgetFactory = widgets.StorageFieldWidget


    def get_items(self):
        aliquotlist = []
        session_manager = getToolByName(self.context,'session_data_manager')
        session = session_manager.getSessionData(create=True)
        kw={'state':self.display_state}
        # Figure out from the request which form we are looking to input
        for kword in ['type','before_date', 'after_date', 'our_id']:
            if( self.request.has_key(kword) and self.request[kword] != None) or\
            (session.has_key(kword) and session[kword] != None):
                if self.request.has_key(kword):
                    session[kword] = self.request[kword]
                kw[kword]=session[kword]
                
        aliquot = self.aliquot_manager.filter_aliquot(**kw)

        for aliquotobj in aliquot:
            aliquotlist.append((aliquotobj.dsid, aliquotobj))
        return aliquotlist
        
# ------------------------------------------------------------------------------
# Specific Forms
# ------------------------------------------------------------------------------

class AliquotRequestor(AliquotRequestorCore):
    """
    """
    def __init__(self,context, request):
        super(AliquotRequestor, self).__init__(context, request)
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.specimen_manager = ds.getSpecimenManager()

        self.display0 = field.Fields(IAliquotGenerator).\
        select('count')

    editform_factory = AliquotCreator

    display_state = 'pending-aliquot'


    def updateWidgets(self):
        self.update_schema['count'].widgetFactory = widgets.StorageFieldWidget
        super(AliquotRequestor, self).updateWidgets()


    def get_items(self):
        aliquotlist=[]
        count = 100
        for specimenobj in self.specimen_manager.list_by_state(self.display_state):
            blueprint = IBlueprintForSpecimen(specimenobj).getBlueprint(self.context)
            for aliquot in blueprint.createAliquotMold(specimenobj):
                aliquotlist.append((count, aliquot))
                count = count + 1
        return aliquotlist


class AliquotChecker(AliquotRequestorCore):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """
    editform_factory = AliquotVerifier
    display_state = 'pending'

class CompletedAliquot(AliquotRequestorCore):


    @property
    def update_schema(self):
        manager = self.display0 + self.display1 + self.display2 + self.display3 + self.display4
        for key in manager.keys():
            manager[key].mode=DISPLAY_MODE
        return manager
        
    editform_factory = AliquotRecoverer
    
    @property
    def action(self):
        return self.context.absolute_url()

    def get_items(self):
        aliquoted = []
        aliquotlist = []
        session_manager = getToolByName(self.context,'session_data_manager')
        session = session_manager.getSessionData(create=True)
        kw={'before_date':date.today(),
            'after_date':date.today()}
        # Figure out from the request which form we are looking to input
        for kword in ['type','before_date', 'after_date', 'our_id']:
            if( self.request.has_key(kword) and self.request[kword] != None) or\
            (session.has_key(kword) and session[kword] != None):
                if self.request.has_key(kword):
                    session[kword] = self.request[kword]
                kw[kword]=session[kword]
                
        for state in [u'checked-in', u'unused']:
            kw['state']=state
            aliquots = self.aliquot_manager.filter_aliquot(**kw)
            aliquoted.extend(aliquots)
                
        for aliquotobj in aliquoted:
            aliquotlist.append((aliquotobj.dsid, aliquotobj))
        return aliquotlist




class AliquotEditor(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """
    
    def __init__(self,context, request):
        super(AliquotEditor, self).__init__(context, request)
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.aliquot_manager = ds.getAliquotManager()
        self.display0 = field.Fields(IAliquot, mode=DISPLAY_MODE).\
            select('dsid')
            
        self.display1 = field.Fields(IViewableAliquot, mode=DISPLAY_MODE).\
            select('patient_title', 'patient_legacy_number', 'study_title','pretty_aliquot_type')
            
        self.displayvolume = field.Fields(IAliquot).\
            select('volume')   
            
        self.displaycells = field.Fields(IAliquot).\
            select('cell_amount')
            
        self.display2 = field.Fields(IAliquot).\
            select('store_date','freezer','rack','box')
    
        self.display3 = field.Fields(IViewableAliquot).\
            select('special_instruction')
           
        self.display4 = field.Fields(IAliquot).\
        select('notes')
        
    ignoreContext=True
    addform_factory = crud.NullForm
    batch_size = 20

    @property
    def update_schema(self):
        manager = self.display0 + self.display1
#         if self.context.volume is not None:
        manager += self.displayvolume
#         if self.context.cell_amount is not None:
        manager += self.displaycells
        return  manager + self.display2 + self.display3 + self.display4

    @property
    def editform_factory(self):
        return AliquotEditManager
        
    def updateWidgets(self):
        super(AliquotEditor, self).updateWidgets()
        self.update_schema['volume'].widgetFactory = widgets.AmountFieldWidget
        self.update_schema['cell_amount'].widgetFactory = widgets.AmountFieldWidget
        self.update_schema['freezer'].widgetFactory = widgets.StorageFieldWidget
        self.update_schema['rack'].widgetFactory = widgets.StorageFieldWidget
        self.update_schema['box'].widgetFactory = widgets.StorageFieldWidget
        
    @property
    def display_state(self):
        return u"incorrect"

    @property
    def action(self):
        raise NotImplementedError

#     def getFilterCookie(self):
#         session_manager = getToolByName(self.context,'session_data_manager')
#         session = session_manager.getSessionData(create=False)

    def get_items(self):
        aliquotlist = []
        kw = {}
        kw['state'] = self.display_state
        aliquot = self.aliquot_manager.filter_aliquot(**kw)
        for aliquotobj in aliquot:
            aliquotlist.append((aliquotobj.dsid, aliquotobj))
        return aliquotlist
   
        
        
class AliquotCheckout(crud.CrudForm):
    """
    """

    def __init__(self,context, request):
        super(AliquotCheckout, self).__init__(context, request)
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.aliquot_manager = ds.getAliquotManager()
        self.display0 = field.Fields(IAliquot, mode=DISPLAY_MODE).\
            select('state','dsid')
            
        self.display1 = field.Fields(IViewableAliquot, mode=DISPLAY_MODE).\
            select('patient_title', 'patient_legacy_number', 'study_title','pretty_aliquot_type')
            
        self.displayvolume = field.Fields(IAliquot, mode=DISPLAY_MODE).\
            select('volume')   
            
        self.displaycells = field.Fields(IAliquot, mode=DISPLAY_MODE).\
            select('cell_amount','store_date')
            
        self.display2 = field.Fields(IViewableAliquot).\
            select('sent_date', 'sent_name', 'sent_notes')
    
        self.display3 = field.Fields(IViewableAliquot, mode=DISPLAY_MODE).\
            select('special_instruction')
           
        self.display4 = field.Fields(IAliquot, mode=DISPLAY_MODE).\
        select('notes')
    editform_factory =  AliquotCheckoutManager
    ignoreContext=True
    addform_factory = crud.NullForm
    
    batch_size = 70
    
    @property
    def update_schema(self):
        manager = self.display0 + self.display1
#         if self.context.volume is not None:
        manager += self.displayvolume
#         if self.context.cell_amount is not None:
        manager += self.displaycells
        return  manager + self.display2 + self.display3 + self.display4
 
    @property
    def display_state(self):
        return u"pending-checkout"

    @property
    def action(self):
        raise NotImplementedError

#     def getFilterCookie(self):
#         session_manager = getToolByName(self.context,'session_data_manager')
#         session = session_manager.getSessionData(create=False)

    def get_items(self):
        aliquotlist = []
        kw={}
        kw['state'] = self.display_state
        aliquot = self.aliquot_manager.filter_aliquot(**kw)

        for aliquotobj in aliquot:
            aliquotlist.append((aliquotobj.dsid, aliquotobj))
        return aliquotlist     



class AliquotCheckoutUpdate(form.Form):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    grok.context(IResearchLab)
    grok.require('zope2.View')
    def __init__(self, context, request):
        super(AliquotCheckoutUpdate, self).__init__(context, request)
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.aliquot_manager = ds.getAliquotManager()

    ignoreContext = True

    @property
    def fields(self):
        selectables=['sent_date', 'sent_name', 'sent_notes']
        return field.Fields(IViewableAliquot).select(*selectables)

    @button.buttonAndHandler(u'Update All')
    def handleUpdate(self, action):
        data, errors = self.extractData()
        if errors:
            self.status=_(u"Sorry.")
            return
        kw={}
#         import pdb;pdb.set_trace()
        kw['state'] = u'pending-checkout'
        aliquot = self.aliquot_manager.filter_aliquot(**kw)
        for aliquotobj in aliquot:  
            updated = False
            for prop, value in data.items():
                if hasattr(aliquotobj, prop) and getattr(aliquotobj, prop) != value:
                    setattr(aliquotobj, prop, value)
                    updated = True
                    
            if updated:
                newaliquot = self.aliquot_manager.put(aliquotobj)                    
        return self.request.response.redirect(self.action)
        
    @button.buttonAndHandler(u'Clear All')
    def handleClear(self, action):


        return self.request.response.redirect(self.action)


# -----------------------------------------------------------------------------
# Aliquot Filter
# -----------------------------------------------------------------------------

class AliquotFilter(z3cform.Form):
    """ Form to select a cycle to view. This is to reduce the crazy
        navigation
    """

    ignoreContext=True

    def update(self):
        ournum = schema.TextLine(
            title=_(u"Enter an OUR#"),
            description=_(u"Enter an OUR# and press GO to show aliquots for "
                          u"only this OUR Number"),
            )
        ournum.__name__ = "our"
        self.fields += field.Fields(ournum)
        super(AliquotByOUR, self).update()

    @property
    def action(self):
        """ Rewrite HTTP POST action.
            If the form is rendered embedded on the others pages we
            make sure the form is posted through the same view always,
            instead of making HTTP POST to the page where the form was rendered.
        """
        return os.path.join(self.context.absolute_url(), "@@aliquotlab")

    @button.buttonAndHandler(_('Go'),name='go')
    def goToAliquot(self, action):
        """ Form button hander. """
        data, errors = self.extractData()
        if errors:
            self.status=_(u"Sorry. That our number is not recognized")
            return
        redirect_url = "%s?our=%s" % (self.action, data['our'])
        return self.request.response.redirect(redirect_url)

    @button.buttonAndHandler(_('Show All'),name='showall')
    def getAllAliquot(self, action):
        """ Form button hander. """
        session_manager = getToolByName(self.context,'session_data_manager')
        session = session_manager.getSessionData(create=True)
        session.invalidate()
        return self.request.response.redirect(self.action)