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
from hive.lab.interfaces.labels import ILabel
from hive.lab import MessageFactory as _



class LabelManager(crud.EditForm):
    """
    """
    def render_batch_navigation(self):
        """
        Render the batch navigation to include the default styles for Plone
        """
        navigation = BatchNavigation(self.batch, self.request)
        def make_link(page):
            return "%s?%spage=%s" % (self.request.getURL(), self.prefix, page)
        navigation.make_link = make_link
        return navigation()
        
    #editsubform_factory = PreselectedEditSubForm
    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass
        
    label=_(u"Label Printer")
    @button.buttonAndHandler(_('Print Selected'), name='print_pdf')
    def handlePDFPrint(self, action):
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Print.")
            return
        que = self.context.labeler.getLabelQue()
        label_list=[]
        for id, label in selected:
            label_list.append(label)
            que.uncatalog_object(str(id))
        content = self.context.labeler.printLabelSheet(label_list)

        self.request.RESPONSE.setHeader("Content-type","application/pdf")
        self.request.RESPONSE.setHeader("Content-disposition",
                                        "attachment;filename=labels.pdf")
        self.request.RESPONSE.setHeader("Cache-Control","no-cache")
        self.request.RESPONSE.write(content)
        self.status = _(u"You print is on its way. Refresh the page to view only unprinted labels.")
        return

    @button.buttonAndHandler(_('Refresh List'), name='refresh')
    def handleRefresh(self, action):
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Remove Selected'), name='remove')
    def handleRemove(self, action):
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Remove.")
            return
        #self.context.labeler
        for id, label in selected:
            self.context.labeler.purgeLabel(id)
        self._update_subforms()

class LabelView(crud.CrudForm):
    """
    """

    def __init__(self,context, request):
        super(LabelView, self).__init__(context, request)
        self.labeler = ILabelPrinter(context)

    editform_factory = LabelManager
    ignoreContext=True
    addform_factory = crud.NullForm
    
    batch_size = 70

    update_schema = field.Fields(ILabel, mode=DISPLAY_MODE).\
        select('dsid', 'patient_title', 'study_title',
       'protocol_title', 'pretty_type','date')
 
    def get_items(self):
        labellist=[]
        for label in self.labeler.getLabelBrains():
            labellist.append((label.getPath(), label))
        return labellist