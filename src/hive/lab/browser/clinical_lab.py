from AccessControl import getSecurityManager
from Products.CMFCore.utils import getToolByName
from avrc.data.store.interfaces import IDataStore
from beast.browser.crud import NestedFormView
from five import grok
from hive.lab import MessageFactory as _, \
                     SCOPED_SESSION_KEY
from hive.lab.browser import crud
from hive.lab.interfaces.aliquot import IAliquotSupport, \
                                        IViewableAliquot, \
                                        IChecklistSupport
from hive.lab.interfaces.lab import IClinicalLab, \
                                    IResearchLab
from hive.lab.interfaces.managers import IAliquotManager, \
                                         ISpecimenManager
from hive.lab.interfaces.specimen import ISpecimenSupport, \
                                         IViewableSpecimen
from plone.directives import dexterity
from z3c.saconfig import named_scoped_session
from AccessControl import getSecurityManager
from Products.statusmessages.interfaces import IStatusMessage
from avrc.data.store.interfaces import IDataStore
from beast.browser import widgets
from datetime import date
from five import grok
from hive.lab import MessageFactory as _, \
                      utilities as utils, \
                     SCOPED_SESSION_KEY
from hive.lab.browser import buttons
from hive.lab.interfaces.aliquot import IAliquot, \
                                        IAliquotGenerator, \
                                        IAliquotSupport, \
                                        IViewableAliquot, \
                                        IAliquotFilterForm, \
                                        IInventoryFilterForm
from hive.lab.interfaces.lab import IFilter, \
                                    IFilterForm, \
                                    IResearchLab
from hive.lab.interfaces.labels import ILabelPrinter, \
                                       ILabel
from hive.lab.interfaces.managers import IAliquotManager, \
                                         ISpecimenManager
from hive.lab.interfaces.specimen import IBlueprintForSpecimen, \
                                         IViewableSpecimen, \
                                         ISpecimen, \
                                         ISpecimenSupport, \
                                         ISpecimenFilterForm
from plone.directives import form
from plone.z3cform.crud import crud
from z3c.form import button, \
                     field, \
                     form as z3cform
from z3c.form.interfaces import DISPLAY_MODE
from z3c.saconfig import named_scoped_session
from zope.app.intid.interfaces import IIntIds
from zope.schema.vocabulary import SimpleTerm, \
                                   SimpleVocabulary
from zope.security import checkPermission
import datetime
import os.path
import zope.component
import zope.interface
import zope.schema
# ------------------------------------------------------------------------------
# Specimen Forms |
# --------------
# These classes provide the various transitions and modifications of the pages
# that support and modify specimen
# ------------------------------------------------------------------------------
class SpecimenPendingForm(SpecimenCoreForm):
    @property
    def editform_factory(self):
        return buttons.SpecimenPendingButtons

    @property
    def display_state(self):
        return u"pending-draw"


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class SpecimenBatchedForm(SpecimenCoreForm):
    @property
    def editform_factory(self):
        return buttons.SpecimenBatchedButtons

    @property
    def display_state(self):
        return u"batched"

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class SpecimenPostponedForm(SpecimenCoreForm):
    @property
    def editform_factory(self):
        return buttons.SpecimenPostponedButtons

    @property
    def display_state(self):
        return u"postponed"


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class SpecimenRecoverForm(SpecimenCoreForm):
    @property
    def view_schema(self):
        fields = field.Fields(IViewableSpecimen).\
        select('state', 'patient_title', 'patient_initials', 'study_week',
       'pretty_type', 'pretty_tube_type')
        fields += field.Fields(ISpecimen).\
        select('tubes', 'date_collected', 'time_collected', 'notes')
        return fields

    @property
    def edit_schema(self):
        return None

    @property
    def editform_factory(self):
        return buttons.SpecimenRecoverButtons

    @property
    def display_state(self):
        return [u'complete', u'rejected']

    def getkwargs(self):
        kw = {'state':self.display_state,
              'before_date':date.today(),
              'after_date':date.today()}
        return kw

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class SpecimenSupportForm(SpecimenCoreForm):
    """
            self.omitables = IFilter(context).getOmittedFields()

    """
    @property
    def view_schema(self):
        fields = field.Fields(IViewableSpecimen).\
        select('state', 'patient_title', 'study_week', 'pretty_type', 'pretty_tube_type')
        fields += field.Fields(ISpecimen).\
            select('tubes', 'date_collected', 'time_collected', 'notes')
        return fields
        
    @property
    def edit_schema(self):
        return None


    @property
    def display_state(self):
        return [u'complete', u'pending-draw', u'batched', u'postponed', u'aliquoted']

  
    @property
    def editform_factory(self):
        return buttons.SpecimenRecoverButtons
 
    def getkwargs(self):
        sessionkeys = ISession(self.request)
        statefilter = False
        if not sessionkeys.has_key('show_all') or not sessionkeys['show_all']:
            statefilter = True
        kw = IFilter(self.context).getFilter(sessionkeys)
        if statefilter:
            kw['state'] = self.display_state
        return kw
 


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class ReadySpecimenForm(SpecimenCoreForm):

    @property
    def view_schema(self):
        fields = field.Fields(IViewableSpecimen, mode=DISPLAY_MODE).\
            select('patient_title', 'study_week', 'pretty_type', 'pretty_tube_type')
        fields += field.Fields(ISpecimen).\
            select('tubes', 'date_collected', 'time_collected', 'notes')            
        return fields

    @property
    def edit_schema(self):
        return None

    @property
    def editform_factory(self):
        return buttons.ReadySpecimenButtons

    @property
    def display_state(self):
        return u"complete"



# ------------------------------------------------------------------------------
# Aliquot Forms |
# --------------
# These classes provide the various transitions and modifications of the pages
# that support and modify specimen
# ------------------------------------------------------------------------------

class AliquotCreator(AliquotCoreForm):
    """
    The aliquot creator form uses the blueprints associated with specimen in the
    'pending-aliquot' state to create molds, which are used to manufacture
    aliquot for the system
    """
    def __init__(self, context, request):
        super(AliquotCreator, self).__init__(context, request)
        self.specimen_manager = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
    editform_factory = buttons.AliquotCreator

    @property
    def display_state(self):
        return u'pending-aliquot'

    @property
    def view_schema(self):
        return None

    @property
    def edit_schema(self):
        fields = field.Fields(IAliquotGenerator).\
        select('count')
        fields += field.Fields(IViewableAliquot, mode=DISPLAY_MODE).\
            select('patient_title', 'patient_legacy_number', 'study_week', 'pretty_type')
        fields += field.Fields(IAliquot).\
            select('volume', 'cell_amount', 'store_date', 'freezer', 'rack', 'box')
        fields += field.Fields(IViewableAliquot).\
            select('special_instruction')
        fields += field.Fields(IAliquot).\
            select('notes')
        return fields

    def updateWidgets(self):
        self.update_schema['count'].widgetFactory = widgets.StorageFieldWidget
        super(AliquotCreator, self).updateWidgets()

    def getCount(self):
        kw = self.getkwargs()
        return self.specimen_manager.count_records(**kw)

    def get_items(self):
        aliquotlist = []
        count = 100
        kw = {'state':self.display_state}
        for specimenobj in self.specimen_manager.filter_records(**kw):
            blueprint = IBlueprintForSpecimen(specimenobj).getBlueprint(self.context)
            for aliquot in blueprint.createAliquotMold(specimenobj):
                aliquotlist.append((count, aliquot))
                count = count + 1
        return aliquotlist

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotPreparedForm(AliquotCoreForm):
    """
    """
    editform_factory = buttons.AliquotPreparedButtons

    @property
    def display_state(self):
        return u'pending'

    def getkwargs(self):
        sessionkeys = ISession(self.request)
        statefilter = False
        if not sessionkeys.has_key('show_all') or not sessionkeys['show_all']:
            statefilter = True
        kw = IFilter(self.context).getFilter(sessionkeys)
        if statefilter:
            kw['state'] = self.display_state
        return kw

        
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotCompletedForm(AliquotCoreForm):
    """
    """
    @property
    def view_schema(self):
        fields = field.Fields(IViewableAliquot).\
            select('dsid')
        fields += field.Fields(IAliquot).\
            select('state')
        fields += field.Fields(IViewableAliquot).\
            select('patient_title', 'patient_legacy_number', 'study_week', 'pretty_type', 'vol_count')
        fields += field.Fields(IAliquot).\
            select('store_date')
        fields += field.Fields(IViewableAliquot).\
            select('frb', 'special_instruction')
        fields += field.Fields(IAliquot).\
            select('notes')
        return fields
    @property
    def edit_schema(self):
        return None

    editform_factory = buttons.AliquotRecoverButtons

    @property
    def display_state(self):
        return [u'checked-in', u'unused']

    def getkwargs(self):
        kw = {'state':self.display_state,
            'before_date':date.today(),
            'after_date':date.today()}
        return kw

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotEditForm(AliquotCoreForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """
    @property
    def editform_factory(self):
        return buttons.AliquotEditButtons

    @property
    def edit_schema(self):
        fields = field.Fields(IAliquot).\
            select('volume', 'cell_amount', 'store_date', 'freezer', 'rack', 'box', 'thawed_num')
        fields += field.Fields(IViewableAliquot).\
            select('special_instruction')
        fields += field.Fields(IAliquot).\
            select('notes')
        return fields

    @property
    def display_state(self):
        return u"incorrect"

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotInventoryForm(AliquotCoreForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """
    @property
    def editform_factory(self):
        return buttons.AliquotInventoryButtons

    @property
    def view_schema(self):
        fields = field.Fields(IViewableAliquot).\
            select('dsid', 'patient_title', 'patient_legacy_number', 'study_week', 'pretty_type', 'vol_count',)
        fields += field.Fields(IAliquot).\
            select('store_date', 'inventory_date')
        fields += field.Fields(IViewableAliquot).\
            select('frb', 'special_instruction')
        return fields

    @property
    def edit_schema(self):
        fields = field.Fields(IAliquot).\
            select('notes')
        return fields

    @property
    def display_state(self):
        return u"checked-in"

    def getkwargs(self):
        sessionkeys = ISession(self.request)
        statefilter = False
        if not sessionkeys.has_key('show_all') or not sessionkeys['show_all']:
            statefilter = True
        kw={}
        for key in ( 'type','freezer', 'rack', 'box'):
            if sessionkeys.has_key(key):
                kw[key] = sessionkeys[key]
        if sessionkeys.has_key('patient'):
            kw['subject_zid'] = utils.getPatientForFilter(self.context, sessionkeys['patient'])
        if sessionkeys.has_key('inventory_date'):
            kw['inventory_date'] = sessionkeys['inventory_date']
        if statefilter:
            kw['state'] = self.display_state
        return kw

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------   
class AliquotCheckoutForm(AliquotCoreForm):
    """
    """
    editform_factory = buttons.AliquotCheckoutButtons

    @property
    def view_schema(self):
        fields = field.Fields(IViewableAliquot).\
            select('dsid', 'patient_title', 'patient_legacy_number', 'study_week', 'pretty_type', 'vol_count',)
        fields += field.Fields(IAliquot).\
            select('store_date')
        fields += field.Fields(IViewableAliquot).\
            select('frb', 'special_instruction')
        fields += field.Fields(IAliquot).\
            select('notes')
        return fields

    @property
    def edit_schema(self):
        fields = field.Fields(IViewableAliquot).\
            select('sent_date', 'sent_name', 'sent_notes')
        return fields

    @property
    def display_state(self):
        return u"pending-checkout"
        
    def getkwargs(self):
        kw = {'state':self.display_state, 'modify_name':self.currentUser}
        return kw

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------   
class AliquotCheckinForm(AliquotCoreForm):
    """
    """
    editform_factory = buttons.AliquotCheckinButtons

    @property
    def view_schema(self):
        fields = field.Fields(IViewableAliquot).\
            select('dsid', 'patient_title', 'patient_legacy_number', 'study_week', 'pretty_type')
        fields += field.Fields(IAliquot).\
            select('store_date')
        fields += field.Fields(IViewableAliquot).\
            select('special_instruction', 'sent_date', 'sent_name', 'sent_notes')
        return fields

    @property
    def edit_schema(self):
        fields = field.Fields(IViewableAliquot).\
            select('thawed')
        fields += field.Fields(IAliquot).\
            select('freezer', 'rack', 'box', 'notes')
        return fields

    @property
    def display_state(self):
        return u"checked-out"

    def getkwargs(self):
        sessionkeys = ISession(self.request)
        statefilter = False
        if not sessionkeys.has_key('show_all') or not sessionkeys['show_all']:
            statefilter = True
        kw = IFilter(self.context).getFilter(sessionkeys)
        if statefilter:
            kw['state'] = self.display_state
        return kw
 

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------   
class AliquotListForm(AliquotCoreForm):
    """
    Filterable crud form based on session information
    """        

    editform_factory = buttons.AliquotQueueButtons

    @property
    def view_schema(self):
        fields = field.Fields(IViewableAliquot).\
            select('dsid', 'state', 'patient_title', 'patient_legacy_number', 'study_week', 'pretty_type', 'vol_count',
            'frb')
        fields += field.Fields(IAliquot).\
            select('store_date')
        fields += field.Fields(IViewableAliquot).\
            select('thawed_num', 'special_instruction')
        fields += field.Fields(IAliquot).\
            select('notes')
        return fields

    edit_schema = None
    
    @property
    def display_state(self):
        return u"checked-in"

    def getkwargs(self):
        sessionkeys = ISession(self.request)
        statefilter = False
        if not sessionkeys.has_key('show_all') or not sessionkeys['show_all']:
            statefilter = True
        kw = IFilter(self.context).getFilter(sessionkeys)
        if statefilter:
            kw['state'] = self.display_state
        return kw


class AliquotQueueForm(AliquotCoreForm):
    """
    """

    @property
    def view_schema(self):
        fields = field.Fields(IViewableAliquot).\
            select('dsid', 'state', 'patient_title', 'patient_legacy_number', 'study_week', 'pretty_type', 'vol_count')
        fields += field.Fields(IAliquot).\
            select('store_date')
        fields += field.Fields(IViewableAliquot).\
            select('frb')
        fields += field.Fields(IAliquot).\
            select('notes')
        return fields

    edit_schema = None

    editform_factory = buttons.AliquotHoldButtons

    batch_size = 70

    @property
    def display_state(self):
        return u"queued"

    def getkwargs(self):
        kw = {'state':self.display_state, 'modify_name':self.currentUser}
        return kw

# ------------------------------------------------------------------------------
# Aliquot Support Forms |
# --------------
# These classes provide supporting forms that modify the listings of aliquot
# ------------------------------------------------------------------------------
class AliquotCheckoutUpdate(form.Form):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    grok.context(IResearchLab)
    grok.require('zope2.View')

    def __init__(self, context, request):
        super(AliquotCheckoutUpdate, self).__init__(context, request)
        self.dsmanager = IAliquotManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))

    ignoreContext = True

    @property
    def currentUser(self):
        return getSecurityManager().getUser().getId()
        
    @property
    def fields(self):
        selectables = ['sent_date', 'sent_name', 'sent_notes']
        return field.Fields(IAliquot).select(*selectables)

    @button.buttonAndHandler(u'Update All')
    def handleUpdate(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = _(u"Sorry.")
            return
        kw = {}
        kw['state'] = u'pending-checkout'
        aliquot = self.dsmanager.filter_records(**kw)
        for aliquotobj in aliquot:
            updated = False
            for prop, value in data.items():
                if hasattr(aliquotobj, prop) and getattr(aliquotobj, prop) != value:
                    setattr(aliquotobj, prop, value)
                    updated = True

            if updated:
                newaliquot = self.dsmanager.put(aliquotobj, by=self.currentUser)
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(u'Clear All')
    def handleClear(self, action):
        return self.request.response.redirect(self.action)


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------   


class AliquotFilterForm(FilterFormCore):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    grok.context(IAliquotSupport)
    grok.require('zope2.View')

    @property
    def fields(self):
        omitables = self.omitables
        return field.Fields(IAliquotFilterForm).omit(*omitables)

class AliquotInventoryFilterForm(FilterFormCore):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    grok.context(IAliquotSupport)
    grok.require('zope2.View')

    @property
    def fields(self):
        omitables=['after_date','before_date', 'show_all']
        return field.Fields(IInventoryFilterForm).omit(*omitables)

    def updateWidgets(self):
        super(AliquotInventoryFilterForm, self).updateWidgets()
        if 'freezer' in self.widgets.keys():
            self.widgets['freezer'].widgetFactory = widgets.StorageFieldWidget
        if 'rack' in self.widgets.keys():
            self.widgets['rack'].widgetFactory = widgets.StorageFieldWidget
        if 'box' in self.widgets.keys():
            self.widgets['box'].widgetFactory = widgets.StorageFieldWidget


class AliquotFilterForCheckinForm(FilterFormCore):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    grok.context(IAliquotSupport)
    grok.require('zope2.View')

    @property
    def fields(self):
        selectables = ['patient', 'type']
        return field.Fields(IAliquotFilterForm).select(*selectables)


class SpecimenFilterForm(FilterFormCore):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    grok.context(ISpecimenSupport)
    grok.require('zope2.View')

    @property
    def fields(self):
        omitables = self.omitables
        return field.Fields(ISpecimenFilterForm).omit(*omitables)
# ------------------------------------------------------------------------------
# Clinical Lab Views |
# --------------
# These classes provide the various transitions and modifications of the pages
# that support and modify specimen
# ------------------------------------------------------------------------------

class ClinicalLabView(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IClinicalLab)
    grok.require('hive.lab.ManageSpecimen')
    grok.name('clinical-view')

    def __init__(self, context, request):
        super(ClinicalLabView, self).__init__(context, request)
        self.crudform = self.getCrudForm()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.SpecimenPendingForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class ClinicalLabBatched(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IClinicalLab)
    grok.require('hive.lab.ManageSpecimen')
    grok.name('batched')

    def __init__(self, context, request):
        super(ClinicalLabBatched, self).__init__(context, request)
        self.crudform = self.getCrudForm()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.SpecimenBatchedForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class ClinicalLabPostponed(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IClinicalLab)
    grok.require('hive.lab.ManageSpecimen')
    grok.name('postponed')

    def __init__(self, context, request):
        super(ClinicalLabPostponed, self).__init__(context, request)
        self.crudform = self.getCrudForm()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.SpecimenPostponedForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class ClinicalLabCompleted(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IClinicalLab)
    grok.require('hive.lab.ManageSpecimen')
    grok.name('complete')

    def __init__(self, context, request):
        super(ClinicalLabCompleted, self).__init__(context, request)
        self.crudform = self.getCrudForm()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.SpecimenRecoverForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view



class SpecimenCoreForm(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """
    def __init__(self, context, request):
        super(SpecimenCoreForm, self).__init__(context, request)
        self.dsmanager = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
        self.update_schema = self.edit_schema

    @property
    def currentUser(self):
        return getSecurityManager().getUser().getId()

    ignoreContext = True
    addform_factory = crud.NullForm
    batch_size = 25

    @property
    def view_schema(self):
        fields = field.Fields(IViewableSpecimen).\
            select('patient_title', 'patient_initials', 'study_week', 'pretty_type', 'pretty_tube_type')
        return fields

    @property
    def edit_schema(self):
        fields = field.Fields(ISpecimen).\
            select('tubes', 'date_collected', 'time_collected', 'notes')
        return fields
        
    def link(self, item, field):
        if field == 'patient_title':
            visit = item.visit()
            if visit is not None:
                url = '%s/specimen' % visit.absolute_url()
            else:
                intids = zope.component.getUtility(IIntIds)
                patient = intids.getObject(item.subject_zid)
                url = '%s/specimen' % patient.absolute_url()
            return url
                
    @property
    def editform_factory(self):
        raise NotImplementedError

    @property
    def display_state(self):
        raise NotImplementedError

    def updateWidgets(self):
        if self.update_schema is not None:
            if 'time_collected' in self.update_schema.keys():
                self.update_schema['time_collected'].widgetFactory = widgets.TimeFieldWidget
            if 'tubes' in self.update_schema.keys():
                self.update_schema['tubes'].widgetFactory = widgets.StorageFieldWidget

    def getkwargs(self):
        kw = {'state':self.display_state}
        return kw

    def getQuery(self):
        kw = self.getkwargs()
        return self.dsmanager.makefilter(**kw)
    
    def getCount(self):
        kw = self.getkwargs()
        return self.dsmanager.count_records(**kw)
        
    def get_items(self):
        specimenlist = []
        kw = self.getkwargs()
        for specimenobj in self.dsmanager.filter_records(**kw):
            specimenlist.append((specimenobj.dsid, specimenobj))
        return specimenlist
