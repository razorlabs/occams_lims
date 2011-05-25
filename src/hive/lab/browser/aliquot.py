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

from hive.lab.interfaces.aliquot import IAliquotBlueprint
from hive.lab import MessageFactory as _
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
import datetime
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
from hive.lab.interfaces.aliquot import IAliquotSupport
from hive.lab.interfaces.aliquot import IAliquotFilter

from hive.lab.interfaces.aliquot import IAliquotFilterForm
from hive.lab.interfaces.labels import ILabelPrinter
from hive.lab.browser.clinicallab import SpecimenRequestor
from hive.lab.browser.clinicallab import SpecimenButtonCore
from hive.lab.browser.labels import LabelView
from hive.lab.browser.researchlab import AliquotButtonCore

from hive.lab import utilities as utils

class AliquotFilter(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IAliquotSupport)
    grok.require('zope2.View')
    grok.name('aliquot')
    
    def __init__(self, context, request):
        super(AliquotFilter, self).__init__(context, request)

        self.form_requestor = self.getFormRequestor()
        self.filter_aliquot = self.filterAliquot()
        self.aliquot_que = self.aliquotQue()
        
    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotList(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view
# 
    def filterAliquot(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotFilterForm(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

    def aliquotQue(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = QueView(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

class AliquotCheckList(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IAliquotSupport)
    grok.require('zope2.View')
    grok.name('checklist')

    def __init__(self, context, request):
        super(AliquotCheckList, self).__init__(context, request)
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.aliquot_manager = ds.getAliquotManager()
        self.getaliquot = self.getAliquot()
        
    def getAliquot(self):
        """
        Get me some aliquot
        """
        aliquotlist = []
        kw={}
        kw['state'] = u'hold'
        for aliquot in self.aliquot_manager.filter_aliquot(**kw):
            yield IViewableAliquot(aliquot)





# ------------------------------------------------------------------------------
# Crud Forms
# ------------------------------------------------------------------------------



class AliquotList(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be 
    """
    
    def __init__(self,context, request):
        super(AliquotList, self).__init__(context, request)
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
            select('cell_amount')
            
        self.display2 = field.Fields(IAliquot, mode=DISPLAY_MODE).\
            select('store_date','freezer','rack','box')
    
        self.display3 = field.Fields(IViewableAliquot, mode=DISPLAY_MODE).\
            select('special_instruction')
           
        self.display4 = field.Fields(IAliquot, mode=DISPLAY_MODE).\
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
        return AllAliquotManager

    @property
    def display_state(self):
        return u"checked-in"

    @property
    def action(self):
        raise NotImplementedError

#     def getFilterCookie(self):
#         session_manager = getToolByName(self.context,'session_data_manager')
#         session = session_manager.getSessionData(create=False)

    def get_items(self):
        aliquotlist = []
        sessionkeys = utils.getSession(self.context, self.request)
        kw = IAliquotFilter(self.context).getAliquotFilter(sessionkeys)
        if not sessionkeys.has_key('show_all') or not sessionkeys['show_all']:
            kw['state'] = self.display_state
        aliquot = self.aliquot_manager.filter_aliquot(**kw)

        for aliquotobj in aliquot:
            aliquotlist.append((aliquotobj.dsid, aliquotobj))
        return aliquotlist



class AllAliquotManager(AliquotButtonCore):
    label=_(u"")
    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @button.buttonAndHandler(_('Que & Hold'), name='que')
    def handleQue(self, action):
        self.changeAliquotState(action, 'hold','que')
        self._update_subforms()
        return
# 
#     @button.buttonAndHandler(_('Print Selected'), name='print',)
#     def handlePrint(self, action):
#         self.queLabels(action)
#         return

class AliquotFilterForm(form.Form):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    def __init__(self, context, request):
        super(AliquotFilterForm, self).__init__(context, request)
        self.session = utils.getSession(context, request)
        self.default_kw = IAliquotFilter(context).getAliquotFilter()
    grok.context(IAliquotSupport)
    grok.require('zope2.View')
    ignoreContext = True

    def update(self):
        super(AliquotFilterForm, self).update()
        for key, value in self.session.items():
            if value is None:
                continue
            elif type(value) == datetime.date:
                self.widgets[key].value = (unicode(value.year), unicode(value.month), unicode(value.day))
            else:
                self.widgets[key].value = value

    @property
    def fields(self):
        omitables = self.default_kw.keys()
        if u'subject_zid' in omitables:
            omitables.append(u'patient')
        return field.Fields(IAliquotFilterForm).omit(*omitables)

    @button.buttonAndHandler(u'Filter')
    def handleFilter(self, action):
        data, errors = self.extractData()
        if errors:
            self.status=_(u"Sorry.")
            return
        for key, value in data.items():
            if value is not None:
                self.session[key] = value
            elif self.session.has_key(key):
                del self.session[key]
                    
        return self.request.response.redirect(self.action)
        
    @button.buttonAndHandler(u'Remove Filter')
    def handleClearFilter(self, action):
        data, errors = self.extractData()
        if errors:
            self.status=_(u"Sorry.")
            return
        self.session.clear()
        return self.request.response.redirect(self.action)

# ------------------------------------------------------------------------------
# Que Manager
# ------------------------------------------------------------------------------

class QueManager(AliquotButtonCore):
    """
    """
        
    #editsubform_factory = PreselectedEditSubForm
    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @button.buttonAndHandler(_('Print List'), name='print')
    def handleQue(self, action):
#         self.changeAliquotState(action, 'incorrect','incorrect')
#         self._update_subforms()
        return self.request.response.redirect('%s/%s' %(self.context.context.absolute_url(), 'checklist' ))

    @button.buttonAndHandler(_('Check Out'), name='checkout')
    def handleCheckout(self, action):
        self.changeAliquotState(action, 'pending-checkout','checkout')
        self._update_subforms()
        return
        
    @button.buttonAndHandler(_('Release Hold'), name='release')
    def handleInaccurate(self, action):
        self.changeAliquotState(action, 'checked-in','release')
        self._update_subforms()
        return self.request.response.redirect(self.action)
        
    @button.buttonAndHandler(_('Mark Inaccurate'), name='incorrect')
    def handleInaccurate(self, action):
        self.changeAliquotState(action, 'incorrect','incorrect')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Mark Missing'), name='missing')
    def handleInaccurate(self, action):
        self.changeAliquotState(action, 'missing','missing')
        self._update_subforms()
        return

#     label=_(u"Label Printer")
#     @button.buttonAndHandler(_('Print Selected'), name='print_pdf')
#     def handlePDFPrint(self, action):
#         selected = self.selected_items()
#         if not selected:
#             self.status = _(u"Please select items to Print.")
#             return
#         que = self.context.labeler.getLabelQue()
#         label_list=[]
#         for id, label in selected:
#             label_list.append(label)
#             que.uncatalog_object(str(id))
#         content = self.context.labeler.printLabelSheet(label_list)
# 
#         self.request.RESPONSE.setHeader("Content-type","application/pdf")
#         self.request.RESPONSE.setHeader("Content-disposition",
#                                         "attachment;filename=labels.pdf")
#         self.request.RESPONSE.setHeader("Cache-Control","no-cache")
#         self.request.RESPONSE.write(content)
#         self.status = _(u"You print is on its way. Refresh the page to view only unprinted labels.")
#         return
# 
#     @button.buttonAndHandler(_('Refresh List'), name='refresh')
#     def handleRefresh(self, action):
#         return self.request.response.redirect(self.action)
# 
#     @button.buttonAndHandler(_('Remove Selected'), name='remove')
#     def handleRemove(self, action):
#         selected = self.selected_items()
#         if not selected:
#             self.status = _(u"Please select items to Remove.")
#             return
#         #self.context.labeler
#         for id, label in selected:
#             self.context.labeler.purgeLabel(id)
#         self._update_subforms()

class QueView(crud.CrudForm):
    """
    """

    def __init__(self,context, request):
        super(QueView, self).__init__(context, request)
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
            select('cell_amount')
            
        self.display2 = field.Fields(IAliquot, mode=DISPLAY_MODE).\
            select('store_date','freezer','rack','box')
    
        self.display3 = field.Fields(IViewableAliquot, mode=DISPLAY_MODE).\
            select('special_instruction')
           
        self.display4 = field.Fields(IAliquot, mode=DISPLAY_MODE).\
        select('notes')
    editform_factory =  QueManager
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
        return u"hold"

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
        

        
   