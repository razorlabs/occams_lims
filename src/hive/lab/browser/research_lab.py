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
# Research Lab Views |
# --------------
# These classes provide the various transitions and modifications of the pages
# that support and modify specimen
# ------------------------------------------------------------------------------

class ResearchLabView(dexterity.DisplayForm):
    """
    Primary view for a research lab object.
    """
    grok.context(IResearchLab)
    grok.require('hive.lab.AliquotSpecimen')
    grok.name('research-view')

    def __init__(self, context, request):
        super(ResearchLabView, self).__init__(context, request)
        self.crudform = self.getCrudForm()
        self.preview = self.getPreview()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.ReadySpecimenForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getPreview(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        dsmanager = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
        kw = {'state':'pending-draw'}
        if dsmanager.count_records() < 1:
            return None
        specimenlist = []
        for specimen in dsmanager.filter_records(**kw):
            vspecimen = IViewableSpecimen(specimen)
            specimendict = {}
            for prop in ['patient_title', 'study_title', 'protocol_title', 'pretty_type', 'pretty_tube_type']:
                specimendict[prop] = getattr(vspecimen, prop)
            for prop in ['tubes', 'date_collected']:
                specimendict[prop] = getattr(specimen, prop)
            specimenlist.append(specimendict)
            
        return specimenlist

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class ResearchLabAliquotReady(dexterity.DisplayForm):
    """
    Primary view for a research lab object.
    """
    grok.context(IResearchLab)
    grok.require('hive.lab.AliquotSpecimen')
    grok.name('ready')

    def __init__(self, context, request):
        super(ResearchLabAliquotReady, self).__init__(context, request)
        self.crudform = self.getCrudForm()
        self.labelqueue = self.getLabelQueue()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotCreator(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getLabelQueue(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.LabelForm(context, self.request)
        if hasattr(form, 'get_items') and not len(form.get_items()):
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class ResearchLabAliquotPrepared(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('hive.lab.ManageAliquot')
    grok.name('prepared')

    def __init__(self, context, request):
        super(ResearchLabAliquotPrepared, self).__init__(context, request)
        self.crudform = self.getCrudForm()
        self.labelqueue = self.getLabelQueue()
        self.filter = self.filterAliquot()
        
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotPreparedForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def filterAliquot(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotFilterForCheckinForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view
        
    def getLabelQueue(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.LabelForm(context, self.request)
        if hasattr(form, 'get_items') and not len(form.get_items()):
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

class ResearchLabAliquotCompleted(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('hive.lab.ManageAliquot')
    grok.name('checkedin')

    def __init__(self, context, request):
        super(ResearchLabAliquotCompleted, self).__init__(context, request)
        self.crudform = self.getCrudForm()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotCompletedForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view


class ResearchLabAliquotEditView(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('hive.lab.ModifyAliquot')
    grok.name('edit-aliquot')

    def __init__(self, context, request):
        super(ResearchLabAliquotEditView, self).__init__(context, request)
        self.crudform = self.getCrudForm()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotEditForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

class ResearchLabAliquotCheckoutView(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('hive.lab.CheckoutAliquot')
    grok.name('checkout')

    def __init__(self, context, request):
        super(ResearchLabAliquotCheckoutView, self).__init__(context, request)
        self.crudform = self.getCrudForm()
        self.formhelper = self.getUpdater()
        self.aliquotqueue = self.aliquotQueue()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotCheckoutForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getUpdater(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotCheckoutUpdate(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def aliquotQueue(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotQueueForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view
        
class ResearchLabAliquotCheckinView(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('hive.lab.CheckinAliquot')
    grok.name('checkin')

    def __init__(self, context, request):
        super(ResearchLabAliquotCheckinView, self).__init__(context, request)

        self.crudform = self.getCrudForm()
        self.filter = self.filterAliquot()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotCheckinForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view
        
    def filterAliquot(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotFilterForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view


class ResearchLabAliquotInventoryView(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('hive.lab.ModifyAliquot')
    grok.name('inventory')

    def __init__(self, context, request):
        super(ResearchLabAliquotInventoryView, self).__init__(context, request)
        self.crudform = self.getCrudForm()
        self.filter = self.filterAliquot()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotInventoryForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def filterAliquot(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotInventoryFilterForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view



# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotCoreForm(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """

    def __init__(self, context, request):
        super(AliquotCoreForm, self).__init__(context, request)
        self.specimen_manager = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
        self.dsmanager = IAliquotManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
        self.update_schema = self.edit_schema

    ignoreContext = True
    addform_factory = crud.NullForm
    batch_size = 25

    @property
    def currentUser(self):
        return getSecurityManager().getUser().getId()
        
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
                intids = zope.component.getUtility(IIntIds)
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

    def getQuery(self):
        kw = self.getkwargs()
        return self.dsmanager.makefilter(**kw)

    def getCount(self):
        kw = self.getkwargs()
        return self.dsmanager.count_records(**kw)
        
    def get_items(self):
        aliquotlist = []
        kw = self.getkwargs()
        aliquot = self.dsmanager.filter_records(**kw)
        for aliquotobj in aliquot:
            aliquotlist.append((aliquotobj.dsid, aliquotobj))
        return aliquotlist

from collective.beaker.interfaces import ISession
class FilterFormCore(form.Form):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    grok.context(zope.interface.Interface)
    grok.require('zope2.View')
    ignoreContext = True
    
    def __init__(self, context, request):
        super(FilterFormCore, self).__init__(context, request)
        self.session = ISession(request)
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
        self.session.save()

        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(u'Remove Filter')
    def handleClearFilter(self, action):
        self.session.clear()
        return self.request.response.redirect(self.action)
