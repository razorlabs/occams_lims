from Products.CMFCore.utils import getToolByName
from plone.directives import dexterity
from zope.security import checkPermission
from datetime import date
from five import grok
from zope.component import  getSiteManager
from z3c.form import field
from z3c.form import button
from z3c.form.interfaces import DISPLAY_MODE
from plone.z3cform.crud import crud

from hive.lab import MessageFactory as _

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
        self.aliquot_molder = self.getAliquotRequestor()

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

    def getAliquotRequestor(self):
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

# ------------------------------------------------------------------------------
# Specific Specimen forms
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
        return u"pending-aliquot"
        
    @property
    def action(self):
        return self.context.absolute_url()


class ReadySpecimenManager(SpecimenButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Ready selected'), name='ready')
    def handleCompleteDraw(self, action):
        self.changeState(action, 'prepared-aliquot','ready')
        self._update_subforms()
        return

# ------------------------------------------------------------------------------
# Aliquot Buttons
# ------------------------------------------------------------------------------


class AliquotCreator(crud.EditForm):
    label=_(u"")
    
    def changeSpecimenState(self, action, state, acttitle):
        success = SUCCESS_MESSAGE
        no_changes = NO_CHANGES
#         if self.status != success and self.status != no_changes:
#             self.status = 'Cannot %s draw because: %s' % (acttitle, self.status)
#             return
        selected = self.selected_items()
        if selected:
            sm = getSiteManager(self)
            ds = sm.queryUtility(IDatastore, 'fia')
            specimen_manager = ds.getSpecimenManager()
            for id, specimenobj in selected:
                specimenobj = ISpecimen(specimenobj)
                setattr(specimenobj, 'state', unicode(state))
                newspecimen = specimen_manager.put(specimenobj)
            self.status = _(u"Your specimen have been %sd." % (acttitle))
        else:
            self.status = _(u"Please select specimen to %s."% (acttitle))
             
#     def queLabels(self, action):
#         success = SUCCESS_MESSAGE
#         no_changes = NO_CHANGES
# 
#         selected = self.selected_items()
#         label_que = self.context.context.labels
#         if selected:
#             self.status = _(u"Specimen Being added to que.")      
#         for id, item in selected:
#             count = item.tubes
#             if count is None or count < 1:
#                 count = 1
#             for i in range(count):
#                 label_que.catalog_object(ISpecimenLabel(item), uid="%d-%d" %(id, i))

    @button.buttonAndHandler(_('Create Aliquot'), name='aliquot')
    def handleCreateAliquot(self, action):
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Aliquot.")
            return
        success = _(u"Successfully Aliquoted")
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = _(u"No Aliquot Entered.")
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        aliquot_manager = ds.getAliquotManager()
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
                    
                newaliquot = aliquot_manager.put(blueprint)
            if status is no_changes:
                status = success
        self.status = status
#        self.changeState(action, 'prepared-aliquot','aliquot')
        self._update_subforms()
        return

#     @button.buttonAndHandler(_('Mark Specimen Complete'), name='complete')
#     def handleCompleteSpecimen(self, action):
#         self.changeSpecimenState(action, 'aliquoted','complete')
#         self._update_subforms()
#         return
        
# class SpecimenToAliquotor(crud.CrudForm):
#     ignoreContext=True
#     newmanager = field.Fields(aliquot.IAliquot).select('aliquot_count')
# 
#     newmanager += field.Fields(aliquot.IAliquot, mode=DISPLAY_MODE).\
#                   select('patient_title', 'patient_legacy_number',
#                          'study_title', 'protocol_title', 'aliquot_type')
#                          
#     newmanager += field.Fields(aliquot.IAliquot).\
#                   select('volume', 'cell_amount', 'store_date','freezer',
#                          'rack', 'box', 'notes', 'special_instruction')
# 
#     update_schema = newmanager
#     addform_factory = crud.NullForm
#     editform_factory = SpecimenToAliquotManager
# 
#     batch_size = 0
# 
#     @property
#     def action(self):
#         return self.context.absolute_url() + '@@/specimenlab'
# 
#     def updateWidgets(self):
#         super(SpecimenToAliquotor, self).updateWidgets()
#         self.update_schema['aliquot_count'].widgetFactory = widget.StorageFieldWidget
#         self.update_schema['volume'].widgetFactory = widget.AmountFieldWidget
#         self.update_schema['cell_amount'].widgetFactory = widget.AmountFieldWidget
#         self.update_schema['freezer'].widgetFactory = widget.StorageFieldWidget
#         self.update_schema['rack'].widgetFactory = widget.StorageFieldWidget
#         self.update_schema['box'].widgetFactory = widget.StorageFieldWidget
# 
#     def get_items(self):
#         sm = getSiteManager(self)
#         ds = sm.queryUtility(IDatastore, 'fia')
#         aliquotlist=[]
#         specimen_manager = ds.specimen
#         count = 100
#         for specimenobj in specimen_manager.list_by_state('prepared-aliquot'):
#             for aliquot_obj in IAliquotableSpecimen(specimenobj).aliquot():
#                 newAliquot = aliquot.IAliquot(aliquot_obj)
#                 aliquotlist.append((count, newAliquot))
#                 count = count + 1
#         return aliquotlist
# ------------------------------------------------------------------------------
# Base Form
# ------------------------------------------------------------------------------

class AliquotRequestor(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """
    ignoreContext=True
    addform_factory = crud.NullForm
    editform_factory = AliquotCreator
    batch_size = 10
    
    display0 = field.Fields(IAliquotGenerator).\
        select('count')
        
    display1 = field.Fields(IViewableAliquot, mode=DISPLAY_MODE).\
        select('patient_title', 'patient_legacy_number', 'study_title',
       'protocol_title', 'pretty_aliquot_type')
       
    display2 = field.Fields(IAliquot).\
        select('volume','cell_amount', 'store_date', 'freezer','rack','box')

    display3 = field.Fields(IViewableAliquot).\
        select('special_instruction')
       
    display4 = field.Fields(IAliquot).\
        select('notes')
        
    update_schema = display0 + display1 + display2 + display3 + display4
 
#     @property
#     def editform_factory(self):
#         raise NotImplementedError
# 
#     @property
#     def display_state(self):
#         raise NotImplementedError
#         
#     @property
#     def action(self):
#         raise NotImplementedError

    def updateWidgets(self):
        super(AliquotRequestor, self).updateWidgets()
        self.update_schema['count'].widgetFactory = widgets.StorageFieldWidget
        self.update_schema['volume'].widgetFactory = widgets.AmountFieldWidget
        self.update_schema['cell_amount'].widgetFactory = widgets.AmountFieldWidget
        self.update_schema['freezer'].widgetFactory = widgets.StorageFieldWidget
        self.update_schema['rack'].widgetFactory = widgets.StorageFieldWidget
        self.update_schema['box'].widgetFactory = widgets.StorageFieldWidget
        
    def get_items(self):
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        aliquotlist=[]
        specimen_manager = ds.getSpecimenManager()
        count = 100
        for specimenobj in specimen_manager.list_by_state('prepared-aliquot'):
            blueprint = IBlueprintForSpecimen(specimenobj).getBlueprint(self.context)
            for aliquot in blueprint.createAliquotMold(specimenobj):
                aliquotlist.append((count, aliquot))
                count = count + 1

        return aliquotlist
        

