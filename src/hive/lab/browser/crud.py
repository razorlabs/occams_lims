from Products.statusmessages.interfaces import IStatusMessage
from avrc.data.store.interfaces import IDatastore
from beast.browser import widgets
from datetime import date
from five import grok
from hive.lab import MessageFactory as _,\
                     utilities as utils
from hive.lab.browser import buttons
from hive.lab.interfaces.aliquot import IAliquot,\
                                        IAliquotGenerator,\
                                        IAliquotSupport,\
                                        IViewableAliquot,\
                                        IAliquotFilterForm
from hive.lab.interfaces.lab import IFilter,\
                                    IFilterForm,\
                                    IResearchLab
from hive.lab.interfaces.labels import ILabelPrinter,\
                                       ILabel
from hive.lab.interfaces.managers import IAliquotManager,\
                                         ISpecimenManager
from hive.lab.interfaces.specimen import IBlueprintForSpecimen,\
                                         IViewableSpecimen,\
                                         ISpecimen,\
                                        ISpecimenSupport,\
                                        ISpecimenFilterForm
from plone.directives import form
from plone.z3cform.crud import crud
from z3c.form import button,\
                     field,\
                     form as z3cform
from z3c.form.interfaces import DISPLAY_MODE
from zope.app.intid.interfaces import IIntIds
from zope.component import getSiteManager
from zope.schema.vocabulary import SimpleTerm,\
                                   SimpleVocabulary
import datetime
import os.path
import zope.schema
import zope.component
import zope.interface
from zope.security import checkPermission
from AccessControl import getSecurityManager

# ------------------------------------------------------------------------------
# Base Forms |
# --------------
# These classes provide the various transitions and modifications of the pages
# that support and modify specimen
# ------------------------------------------------------------------------------

class SpecimenCoreForm(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """
    def __init__(self, context, request):
        super(SpecimenCoreForm, self).__init__(context, request)
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.dsmanager = ISpecimenManager(ds)
        self.currentUser = getSecurityManager().getUser().getId()
        self.update_schema = self.edit_schema

    ignoreContext = True
    addform_factory = crud.NullForm
    batch_size = 25

    @property
    def view_schema(self):
        fields = field.Fields(IViewableSpecimen).\
            select('patient_title', 'patient_initials', 'study_title', 'protocol_title', 'pretty_type', 'pretty_tube_type')
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

    def get_items(self):
        specimenlist = []
        kw = self.getkwargs()
        for specimenobj in self.dsmanager.filter_records(**kw):
            specimenlist.append((specimenobj.dsid, specimenobj))
        return specimenlist

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotCoreForm(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """

    def __init__(self, context, request):
        super(AliquotCoreForm, self).__init__(context, request)
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.specimen_manager = ISpecimenManager(ds)
        self.dsmanager = IAliquotManager(ds)
        self.update_schema = self.edit_schema
        self.currentUser = getSecurityManager().getUser().getId()


    ignoreContext = True
    addform_factory = crud.NullForm
    batch_size = 25

    @property
    def view_schema(self):
        fields = field.Fields(IViewableAliquot, mode=DISPLAY_MODE).\
            select('dsid', 'patient_title', 'patient_legacy_number', 'study_week', 'pretty_type')
        return fields

    @property
    def edit_schema(self):
        fields = field.Fields(IAliquot).\
            select('volume', 'cell_amount', 'store_date', 'freezer', 'rack', 'box')
        fields += field.Fields(IViewableAliquot).\
            select('special_instruction')
        fields += field.Fields(IAliquot).\
            select('notes')
        return fields

    def link(self, item, field):
        if field == 'patient_title':
            intids = zope.component.getUtility(IIntIds)
            specimen = self.specimen_manager.get(item.specimen_dsid)
            patient = intids.getObject(specimen.subject_zid)
            return '%s/aliquot' % patient.absolute_url()

        elif field == 'study_week':
            specimen = self.specimen_manager.get(item.specimen_dsid)
            visit = specimen.visit()
            if visit is not None:
                url = '%s/aliquot' % visit.absolute_url()
            else:
                patient = intids.getObject(specimen.subject_zid)
                url = '%s/aliquot' % patient.absolute_url()
            return url
            
    @property
    def editform_factory(self):
        raise NotImplementedError

    @property
    def display_state(self):
        raise NotImplementedError

    def updateWidgets(self):
        super(AliquotCoreForm, self).updateWidgets()
        if self.update_schema is not None:
            if 'volume' in self.update_schema.keys():
                self.update_schema['volume'].widgetFactory = widgets.AmountFieldWidget
            if 'cell_amount' in self.update_schema.keys():
                self.update_schema['cell_amount'].widgetFactory = widgets.AmountFieldWidget
            if 'freezer' in self.update_schema.keys():
                self.update_schema['freezer'].widgetFactory = widgets.StorageFieldWidget
            if 'rack' in self.update_schema.keys():
                self.update_schema['rack'].widgetFactory = widgets.StorageFieldWidget
            if 'box' in self.update_schema.keys():
                self.update_schema['box'].widgetFactory = widgets.StorageFieldWidget
            if 'thawed_num' in self.update_schema.keys():
                self.update_schema['thawed_num'].widgetFactory = widgets.StorageFieldWidget

    def getkwargs(self):
        kw = {'state':self.display_state}
        return kw

    def get_items(self):
        aliquotlist = []
        kw = self.getkwargs()
        aliquot = self.dsmanager.filter_records(**kw)
        for aliquotobj in aliquot:
            aliquotlist.append((aliquotobj.dsid, aliquotobj))
        return aliquotlist

class FilterFormCore(form.Form):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    grok.context(zope.interface.Interface)
    grok.require('zope2.View')
    ignoreContext = True
    
    def __init__(self, context, request):
        super(FilterFormCore, self).__init__(context, request)
        self.session = utils.getSession(context, request)
        self.default_kw = IFilter(context).getFilter()
        self.omitables = IFilter(context).getOmittedFields()

    def update(self):
        super(FilterFormCore, self).update()
        for key, value in self.session.items():
            if value is None or key not in self.fields.keys():
                continue
            elif type(value) == datetime.date:
                self.widgets[key].value = (unicode(value.year), unicode(value.month), unicode(value.day))
            else:
                self.widgets[key].value = value
    @property
    def fields(self):
        omitables = self.omitables
        return field.Fields(IFilterForm).omit(*omitables)

    @button.buttonAndHandler(u'Filter')
    def handleFilter(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = _(u"Sorry.")
            return
        for key, value in data.items():
            if value is not None:
                self.session[key] = value
            elif self.session.has_key(key):
                del self.session[key]

        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(u'Remove Filter')
    def handleClearFilter(self, action):
        self.session.clear()
        return self.request.response.redirect(self.action)
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
        select('state', 'patient_title', 'patient_initials', 'study_title',
       'protocol_title', 'pretty_type', 'pretty_tube_type')
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
        select('state', 'patient_title', 'study_title', 'protocol_title', 'pretty_type', 'pretty_tube_type')
        fields += field.Fields(ISpecimen).\
            select('tubes', 'date_collected', 'time_collected', 'notes')
        return fields
        
    @property
    def edit_schema(self):
        return None
        
    @property
    def editform_factory(self):
        return buttons.SpecimenRecoverButtons
 
    def getkwargs(self):
        sessionkeys = utils.getSession(self.context, self.request)
        kw = IFilter(self.context).getFilter(sessionkeys)
        return kw

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class ReadySpecimenForm(SpecimenCoreForm):

    @property
    def view_schema(self):
        fields = field.Fields(IViewableSpecimen, mode=DISPLAY_MODE).\
            select('patient_title', 'study_title', 'protocol_title', 'pretty_type', 'pretty_tube_type')
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
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.specimen_manager = ISpecimenManager(ds)

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
            select('patient_title', 'patient_legacy_number', 'study_title', 'protocol_title', 'pretty_type')
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
        sessionkeys = utils.getSession(self.context, self.request)
        kw = IFilter(self.context).getFilter(sessionkeys)
        if not sessionkeys.has_key('show_all') or not sessionkeys['show_all']:
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
            select('dsid', 'patient_title', 'patient_legacy_number', 'study_week', 'pretty_type', 'vol_count')
        fields += field.Fields(IAliquot).\
            select('store_date')
        fields += field.Fields(IViewableAliquot).\
            select('frb','special_instruction')
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
            select('volume', 'cell_amount', 'store_date', 'freezer', 'rack', 'box','thawed_num')
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
class AliquotCheckoutForm(AliquotCoreForm):
    """
    """
    editform_factory = buttons.AliquotCheckoutButtons

    @property
    def view_schema(self):
        fields = field.Fields(IViewableAliquot).\
            select('dsid', 'patient_title', 'patient_legacy_number', 'study_week', 'pretty_type', 'vol_count',)
        fields += field.Fields(IAliquot).\
            select( 'store_date')
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
            select( 'store_date')
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

#     def updateWidgets(self):
#         super(AliquotCheckinForm, self).updateWidgets()
#         if self.update_schema is not None:
#             if 'thawed' in self.update_schema.keys():
#                 self.update_schema['thawed'].widgetFactory = widgets.YesNoFieldWidget

    @property
    def display_state(self):
        return u"checked-out"

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
            select('dsid', 'state','patient_title', 'patient_legacy_number', 'study_week', 'pretty_type', 'vol_count',
            'frb')
        fields += field.Fields(IAliquot).\
            select('thawed_num', 'store_date')
        fields += field.Fields(IViewableAliquot).\
            select('special_instruction')
        fields += field.Fields(IAliquot).\
            select('notes')
        return fields

    edit_schema = None
    
    @property
    def display_state(self):
        return u"checked-in"

    def getkwargs(self):
        sessionkeys = utils.getSession(self.context, self.request)
        kw = IFilter(self.context).getFilter(sessionkeys)
        if not sessionkeys.has_key('show_all') or not sessionkeys['show_all']:
            kw['state'] = self.display_state
        return kw

## have this produce a count of available, order by patient uid, with the 
## Entry box for the count wanted to place on hold

    def get_items(self):
        aliquotlist = []
        kw = self.getkwargs()
        aliquot = self.dsmanager.filter_records(**kw)
        for aliquotobj in aliquot:
            aliquotlist.append((aliquotobj.dsid, aliquotobj))
        return aliquotlist


class AliquotQueueForm(AliquotCoreForm):
    """
    """
    @property
    def view_schema(self):
        fields = field.Fields(IViewableAliquot).\
            select('dsid', 'state', 'patient_title', 'patient_legacy_number', 'study_week', 'pretty_type', 'vol_count')
        fields += field.Fields(IAliquot).\
            select( 'store_date')
        fields += field.Fields(IViewableAliquot).\
            select('frb', 'special_instruction')
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
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.dsmanager = IAliquotManager(ds)
        self.currentUser = getSecurityManager().getUser().getId()

    ignoreContext = True

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
        omitables.append('show_all')
        return field.Fields(ISpecimenFilterForm).omit(*omitables)
        
# ------------------------------------------------------------------------------
# Form for requesting aditional specimen for a particular visit.
# ------------------------------------------------------------------------------

class SpecimenAddForm(z3cform.Form):
    label = _(u'Add Specimen')
    ignoreContext = True

    def __init__(self, context, request):
        super(SpecimenAddForm, self).__init__(context, request)
        self.redirect_url = os.path.join(context.absolute_url(), '@@specimen')
        self.currentUser = getSecurityManager().getUser().getId()

    def specimenVocabulary(self):
        context = self.context.aq_inner
        termlist = []
        intids = zope.component.getUtility(IIntIds)
        subject_zid = intids.getId(context.aq_parent)
        date_collected = context.visit_date
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
        available_specimen = zope.schema.List(
            title=_(u'Available Specimen'),
            value_type=zope.schema.Choice(
                           title=_(u'Available Specimen'),
                           description=_(u''),
                           source=self.specimenVocabulary()
                           )
            )
        available_specimen.__name__ = 'available_specimen'
        self.fields += field.Fields(available_specimen)
        super(SpecimenAddForm, self).update()

    @button.buttonAndHandler(_('Request More Specimen'), name='requestSpecimen',
    condition=lambda self: checkPermission('hive.lab.RequestSpecimen', self.context))
    def requestSpecimen(self, action):
        sm = zope.component.getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        specimen_manager = ISpecimenManager(ds)
        data, errors = self.extractData()
        messages = IStatusMessage(self.request)
        if errors:
            messages.addStatusMessage(
                _(u'There was an error with your request.'),
                type='error'
                )
            return
        for specimen in data['available_specimen']:
            specimen_manager.put(specimen, by=self.currentUser)

        return self.request.response.redirect(self.redirect_url)

# ------------------------------------------------------------------------------
# Label Queue Listing
# ------------------------------------------------------------------------------
class LabelForm(crud.CrudForm):
    """
    """
    def __init__(self, context, request):
        super(LabelForm, self).__init__(context, request)
        self.labeler = ILabelPrinter(context)

    editform_factory = buttons.LabelButtons
    ignoreContext = True
    addform_factory = crud.NullForm

    batch_size = 80

    view_schema = field.Fields(ILabel).\
        select('dsid', 'patient_title', 'study_title',
       'protocol_title', 'pretty_type', 'date')

    def get_items(self):
        labellist = []
        for label in self.labeler.getLabelBrains():
            labellist.append((label.getPath(), label))
        return labellist
