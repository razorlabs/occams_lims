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
#         try:
#             cooklist=[]
#             testcookie = self.context.REQUEST['testcookie']
#             import pdb;pdb.set_trace()
#             items = testcookie.strip('{}"').split(',')
#             for kv in items:
#                 cooklist.append(kv.split(':'))
#             self.testcookie=cooklist
#         except:
#             self.testcookie = 'no cookie'
        
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

#     @property
#     def editform_factory(self):
#         raise NotImplementedError

    @property
    def display_state(self):
        return u"checked-in"

    @property
    def action(self):
        raise NotImplementedError

    def getFilterCookie(self):
        session_manager = getToolByName(self.context,'session_data_manager')
        session = session_manager.getSessionData(create=False)
        

    def get_items(self):
        aliquotlist = []
        kw = IAliquotFilter(self.context).getAliquotFilter()
        kw['state'] = self.display_state
        session_manager = getToolByName(self.context,'session_data_manager')
        session = session_manager.getSessionData(create=True)
#         
#         kw={'state':self.display_state}
#         # Figure out from the request which form we are looking to input
#         for kword in ['type','before_date', 'after_date', 'our_id']:
#             if( self.request.has_key(kword) and self.request[kword] != None) or\
#             (session.has_key(kword) and session[kword] != None):
#                 if self.request.has_key(kword):
#                     session[kword] = self.request[kword]
#                 kw[kword]=session[kword]
        # kw={'type':self.type}
        aliquot = self.aliquot_manager.filter_aliquot(**kw)

        for aliquotobj in aliquot:
            aliquotlist.append((aliquotobj.dsid, aliquotobj))
        return aliquotlist


#from zope.publisher.interfaces.browser import IBrowserView
class AliquotFilterForm(form.Form):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    grok.context(IAliquotSupport)
    grok.require('zope2.View')
    ignoreContext = True
    
    fields = field.Fields(IAliquotFilterForm)
    
    @button.buttonAndHandler(u'Filter')
    def handleFilter(self, action):
        data, errors = self.extractData()
        if errors:
            self.status=_(u"Sorry.")
            return
        self.request.RESPONSE.appendCookie('testcookie',data['patient'])
        
        
        
        
        
        
        
        
        
        
        
        
        