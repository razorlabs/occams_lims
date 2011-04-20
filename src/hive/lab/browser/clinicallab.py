from Products.CMFCore.utils import getToolByName

from plone.directives import dexterity

from zope.security import checkPermission
from datetime import date

from five import grok

from hive.lab import MessageFactory as _

from hive.lab.browser import widget

# from avrc.aeh.browser.aliquotform import AliquotRequestor
# from avrc.aeh.browser.aliquotform import AliquotByOUR
# from avrc.aeh.browser.clinicallabform import SpecimenRequestor
# from avrc.aeh.browser.form import NestedFormView
# from avrc.aeh.browser.labelprintform import AliquotLabelPrinter
# from avrc.aeh.browser.labelprintform import AliquotLabelRePrinter
# from avrc.aeh.browser.specimenaliquotform import SpecimenToAliquotor
# from avrc.aeh.browser.specimenlabform import SpecimenAliquotor
# from avrc.aeh.content.institute import IInstitute

from hive.lab.browser.utils import NestedFormView

from hive.lab.interfaces import IClinicalLab
from avrc.data.store.interfaces import ISpecimen
from hive.lab.interfaces import IViewableSpecimen


from z3c.form import field
from z3c.form import button
from z3c.form.interfaces import DISPLAY_MODE
from avrc.data.store.interfaces import IDatastore
from zope.component import  getSiteManager

from plone.z3cform.crud import crud

class View(dexterity.DisplayForm):
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
        form = SpecimenRequestor(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

class SpecimenRequestor(crud.CrudForm):
    """
    The crud form to apply new specimen
    """
    ignoreContext=True
    newmanager = field.Fields(IViewableSpecimen, mode=DISPLAY_MODE).\
    select('patient_title', 'patient_initials', 'study_title',
           'protocol_title', 'pretty_specimen_type', 'pretty_tube_type')
    newmanager += field.Fields(ISpecimen).\
    select('tubes','date_collected', 'time_collected',  'notes')
    update_schema = newmanager
    addform_factory = crud.NullForm
#__in    editform_factory = SpecimenButtonManager

    batch_size = 30

    @property
    def action(self):
        return self.context.absolute_url()

    def updateWidgets(self):
        super(SpecimenRequestor, self).updateWidgets()
        self.update_schema['time_collected'].widgetFactory = widget.TimeFieldWidget
        self.update_schema['tubes'].widgetFactory = widget.StorageFieldWidget
        self.update_schema['time_collected'].label = _(u"Time Collected")
        self.update_schema['date_collected'].label = _(u"Date Collected")

    def get_items(self):
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        specimenlist=[]
        specimen_manager = ds.getSpecimenManager()
        for specimenobj in specimen_manager.list_by_state(u'pending-draw', before_date=date.today()):
            specimenlist.append((specimenobj.dsid, specimenobj))
        return specimenlist





#### Goes in the button manager

#     def render_batch_navigation(self):
#         navigation = BatchNavigation(self.batch, self.request)
#         def make_link(page):
#             return "%s?%spage=%s" % (self.request.getURL(), self.prefix, page)
#         navigation.make_link = make_link
#         return navigation()


# 
# 
# 
# 
# #----------------------------
# from cStringIO import StringIO
# from datetime import date
# 
# from zope.component import  getSiteManager
# 
# from z3c.form import field
# from z3c.form import button
# from z3c.form.interfaces import DISPLAY_MODE
# 
# from plone.dexterity import content
# from plone.z3cform.crud import crud
# 
# from avrc.aeh import MessageFactory as _
# from avrc.aeh.browser.widget import TimeFieldWidget
# from avrc.aeh.browser.widget import StorageFieldWidget
# from avrc.aeh.specimen import labels
# from avrc.aeh.specimen.specimen import ISpecimen
# 
# from avrc.data.store.interfaces import IDatastore
# from avrc.data.store.interfaces import ISpecimen as IDSSpecimen
# 
# 
# 
# 
# 
# class SpecimenRequestor(crud.CrudForm):
# 
#     ignoreContext=True
#     newmanager = field.Fields(ISpecimen, mode=DISPLAY_MODE).\
#     select('patient_title', 'patient_initials', 'study_title',
#            'protocol_title','specimen_type', 'tube_type')
#     newmanager += field.Fields(ISpecimen).\
#     select('tubes','date_collected', 'time_collected',  'notes')
#     update_schema = newmanager
#     addform_factory = crud.NullForm #wrappableAddForm
#     editform_factory = SpecimenButtonManager
# 
#     batch_size = 30
# 
#     @property
#     def action(self):
#         return self.context.absolute_url() + '@@/clinicallab'
# 
#     def updateWidgets(self):
#         super(SpecimenRequestor, self).updateWidgets()
#         self.update_schema['time_collected'].widgetFactory = TimeFieldWidget
#         self.update_schema['tubes'].widgetFactory = StorageFieldWidget
# 
#     def get_items(self):
#         sm = getSiteManager(self)
#         ds = sm.queryUtility(IDatastore, 'fia')
#         specimenlist=[]
#         specimen_manager = ds.specimen
#         for specimenobj in specimen_manager.list_by_state(u'pending-draw', before_date=date.today()):
#             newSpecimen = ISpecimen(specimenobj)
#             specimenlist.append((specimenobj.dsid, newSpecimen))
#         return specimenlist
# 
# 

# ------------------------------------------------------------------------------
# Clinical View
# ------------------------------------------------------------------------------
# 
# class SpecimenButtonManager(crud.EditForm):
#     label=_(u"")
#     @button.buttonAndHandler(_('Save All Changes'), name='update')
#     def handleUpdate(self, action):
#         success = _(u"Successfully updated")
#         partly_success = _(u"Some of your changes could not be applied.")
#         status = no_changes = _(u"No changes made.")
#         sm = getSiteManager(self)
#         ds = sm.queryUtility(IDatastore, 'fia')
#         specimen_manager = ds.specimen
#         for subform in self.subforms:
#             data, errors = subform.extractData()
#             if errors:
#                 if status is no_changes:
#                     status = subform.formErrorsMessage
#                 elif status is success:
#                     status = partly_success
#                 continue
#             self.context.before_update(subform.content, data)
#             specimenobj = IDSSpecimen(subform.content)
#             updated = False
#             for prop, value in data.items():
#                 if hasattr(specimenobj, prop) and getattr(specimenobj, prop) != value:
#                     setattr(specimenobj, prop, value)
#                     updated = True
#                     if status is no_changes:
#                         status = success
#             if updated:
#                 newspecimen = specimen_manager.put(specimenobj)
#         self.status = status
# 
#     @button.buttonAndHandler(_('Print Selected'), name='print',)
#     def handlePrint(self, action):
#         success = _(u"Successfully updated")
#         no_changes = _(u"No changes made.")
#         self.handleUpdate(self, action)
#         if self.status != success and self.status != no_changes:
#             self.status = 'Cannot print because: %s' % self.status
#             return
#         selected = self.selected_items()
#         if selected:
#             self.status = _(u"Printable PDF on its way.")
#             stream = StringIO()
#             labelWriter = labels.labelGenerator(labels.AVERY_5160, stream)
# 
#             for id, item in selected:
#                 count = item.tubes
# 
#                 if count is None or count < 1:
#                     count = 1
# 
#                 for i in range(count):
#                     labelWriter.drawASpecimenLabel(
#                         date=item.date_collected.strftime("%m/%d/%Y"),
#                         PID=item.patient_title,
#                         week=item.protocol_title,
#                         study=item.study_title,
#                         type=item.specimen_type
#                         )
# 
#             labelWriter.writeLabels()
#             content = stream.getvalue()
#             stream.close()
# 
#             self.request.RESPONSE.setHeader("Content-type","application/pdf")
#             self.request.RESPONSE.setHeader("Content-disposition",
#                                             "attachment;filename=labels.pdf")
#             self.request.RESPONSE.setHeader("Cache-Control","no-cache")
#             self.request.RESPONSE.write(content)
# 
#         else:
#             self.status = _(u"Please select items to Print.")
# 
# 
#     @button.buttonAndHandler(_('Complete selected'), name='complete')
#     def handleCompleteDraw(self, action):
#         success = _(u"Successfully updated")
#         no_changes = _(u"No changes made.")
#         self.handleUpdate(self, action)
#         if self.status != success and self.status != no_changes:
#             self.status = 'Cannot complete draw because: %s' % self.status
#             return
#         selected = self.selected_items()
#         if selected:
#             sm = getSiteManager(self)
#             ds = sm.queryUtility(IDatastore, 'fia')
#             specimen_manager = ds.specimen
#             for id, specimenobj in selected:
#                 specimenobj = IDSSpecimen(specimenobj)
#                 setattr(specimenobj, 'state', unicode('pending-aliquot'))
# 
#                 newspecimen = specimen_manager.put(specimenobj)
#             self.status = _(u"Your specimen have been completed.")
#         else:
#             self.status = _(u"Please select specimen to complete.")
#         self._update_subforms()
#         return
# 
#     @button.buttonAndHandler(_('Mark Selected Undrawn'), name='cancel')
#     def handleCancelDraw(self, action):
#         success = _(u"Successfully updated")
#         no_changes = _(u"No changes made.")
#         self.handleUpdate(self, action)
#         if self.status != success and self.status != no_changes:
#             self.status = 'Cannot cancel draw because: %s' % self.status
#             return
#         selected = self.selected_items()
#         if selected:
#             sm = getSiteManager(self)
#             ds = sm.queryUtility(IDatastore, 'fia')
#             specimen_manager = ds.specimen
#             for id, specimenobj in selected:
#                 specimenobj = IDSSpecimen(specimenobj)
#                 setattr(specimenobj, 'state', unicode('rejected'))
# 
#                 newspecimen = specimen_manager.put(specimenobj)
#             self.status = _(u"Your specimen have been rejected.")
#         else:
#             self.status = _(u"Please select specimen to complete.")
#         self._update_subforms()
#         return
