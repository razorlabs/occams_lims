# from AccessControl import getSecurityManager
# from Products.CMFCore.utils import getToolByName
# from beast.browser.crud import NestedFormView
# from five import grok
# from occams.lab import MessageFactory as _, \
#                      SCOPED_SESSION_KEY
# from occams.lab.browser import crud
# from occams.lab.interfaces.aliquot import IAliquotSupport, \
#                                         IViewableAliquot, \
#                                         IChecklistSupport
# from occams.lab.interfaces.lab import IClinicalLab, \
#                                     IResearchLab
# from occams.lab.interfaces.managers import IAliquotManager, \
#                                          ISpecimenManager
# from occams.lab.interfaces.specimen import ISpecimenSupport, \
#                                          IViewableSpecimen
# from plone.directives import dexterity
# from z3c.saconfig import named_scoped_session
# import z3c.form
# # ------------------------------------------------------------------------------
# # Clinical Lab Views |
# # --------------
# # These classes provide the various transitions and modifications of the pages
# # that support and modify specimen
# # ------------------------------------------------------------------------------

# # class ClinicalLabView(z3c.form.form.Form):
# #     """
# #     Primary view for a clinical lab object.
# #     """
# #     grok.context(IClinicalLab)
# #     grok.require('occams.lab.ManageSpecimen')
# #     grok.name('clinical-view')

# #     def __init__(self, context, request):
# #         super(ClinicalLabView, self).__init__(context, request)

# #     def update(self):
# #         self.crudform = self.getCrudForm()
# #         super(ClinicalLabView, self).update()

# #     def getCrudForm(self):
# #         """
# #         Create a form instance.
# #         @return: z3c.form wrapped for Plone 3 view
# #         """
# #         context = self.context.aq_inner
# #         form = crud.SpecimenPendingForm(context, self.request)
# #         if hasattr(form, 'getCount') and form.getCount() < 1:
# #             return None
# #         view = NestedFormView(context, self.request)
# #         view = view.__of__(context)
# #         view.form_instance = form
# #         return view

# # ------------------------------------------------------------------------------
# # ------------------------------------------------------------------------------
# class ClinicalLabBatched(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IClinicalLab)
#     grok.require('occams.lab.ManageSpecimen')
#     grok.name('batched')

#     def __init__(self, context, request):
#         super(ClinicalLabBatched, self).__init__(context, request)
#         self.crudform = self.getCrudForm()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.SpecimenBatchedForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

# # ------------------------------------------------------------------------------
# # ------------------------------------------------------------------------------
# class ClinicalLabPostponed(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IClinicalLab)
#     grok.require('occams.lab.ManageSpecimen')
#     grok.name('postponed')

#     def __init__(self, context, request):
#         super(ClinicalLabPostponed, self).__init__(context, request)
#         self.crudform = self.getCrudForm()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.SpecimenPostponedForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

# # ------------------------------------------------------------------------------
# # ------------------------------------------------------------------------------
# class ClinicalLabCompleted(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IClinicalLab)
#     grok.require('occams.lab.ManageSpecimen')
#     grok.name('complete')

#     def __init__(self, context, request):
#         super(ClinicalLabCompleted, self).__init__(context, request)
#         self.crudform = self.getCrudForm()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.SpecimenRecoverForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

# # ------------------------------------------------------------------------------
# # Research Lab Views |
# # --------------
# # These classes provide the various transitions and modifications of the pages
# # that support and modify specimen
# # ------------------------------------------------------------------------------

# class ResearchLabView(dexterity.DisplayForm):
#     """
#     Primary view for a research lab object.
#     """
#     grok.context(IResearchLab)
#     grok.require('occams.lab.AliquotSpecimen')
#     grok.name('research-view')

#     def __init__(self, context, request):
#         super(ResearchLabView, self).__init__(context, request)
#         self.crudform = self.getCrudForm()
#         self.preview = self.getPreview()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.ReadySpecimenForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def getPreview(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         dsmanager = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
#         kw = {'state':'pending-draw'}
#         if dsmanager.count_records() < 1:
#             return None
#         specimenlist = []
#         for specimen in dsmanager.filter_records(**kw):
#             vspecimen = IViewableSpecimen(specimen)
#             specimendict = {}
#             for prop in ['patient_title', 'study_title', 'protocol_title', 'pretty_type', 'pretty_tube_type']:
#                 specimendict[prop] = getattr(vspecimen, prop)
#             for prop in ['tubes', 'date_collected']:
#                 specimendict[prop] = getattr(specimen, prop)
#             specimenlist.append(specimendict)

#         return specimenlist

# # ------------------------------------------------------------------------------
# # ------------------------------------------------------------------------------
# class ResearchLabAliquotReady(dexterity.DisplayForm):
#     """
#     Primary view for a research lab object.
#     """
#     grok.context(IResearchLab)
#     grok.require('occams.lab.AliquotSpecimen')
#     grok.name('ready')

#     def __init__(self, context, request):
#         super(ResearchLabAliquotReady, self).__init__(context, request)
#         self.crudform = self.getCrudForm()
#         self.labelqueue = self.getLabelQueue()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotCreator(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def getLabelQueue(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.LabelForm(context, self.request)
#         if hasattr(form, 'get_items') and not len(form.get_items()):
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

# # ------------------------------------------------------------------------------
# # ------------------------------------------------------------------------------
# class ResearchLabAliquotPrepared(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IResearchLab)
#     grok.require('occams.lab.ManageAliquot')
#     grok.name('prepared')

#     def __init__(self, context, request):
#         super(ResearchLabAliquotPrepared, self).__init__(context, request)
#         self.crudform = self.getCrudForm()
#         self.labelqueue = self.getLabelQueue()
#         self.filter = self.filterAliquot()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotPreparedForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def filterAliquot(self):
#         """ Create a form instance.
#             Returns:
#                 z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotFilterForCheckinForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def getLabelQueue(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.LabelForm(context, self.request)
#         if hasattr(form, 'get_items') and not len(form.get_items()):
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

# class ResearchLabAliquotCompleted(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IResearchLab)
#     grok.require('occams.lab.ManageAliquot')
#     grok.name('checkedin')

#     def __init__(self, context, request):
#         super(ResearchLabAliquotCompleted, self).__init__(context, request)
#         self.crudform = self.getCrudForm()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotCompletedForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view


# class ResearchLabAliquotEditView(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IResearchLab)
#     grok.require('occams.lab.ModifyAliquot')
#     grok.name('edit-aliquot')

#     def __init__(self, context, request):
#         super(ResearchLabAliquotEditView, self).__init__(context, request)
#         self.crudform = self.getCrudForm()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotEditForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

# class ResearchLabAliquotCheckoutView(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IResearchLab)
#     grok.require('occams.lab.CheckoutAliquot')
#     grok.name('checkout')

#     def __init__(self, context, request):
#         super(ResearchLabAliquotCheckoutView, self).__init__(context, request)
#         self.crudform = self.getCrudForm()
#         self.formhelper = self.getUpdater()
#         self.aliquotqueue = self.aliquotQueue()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotCheckoutForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def getUpdater(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotCheckoutUpdate(context, self.request)
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def aliquotQueue(self):
#         """ Create a form instance.
#             Returns:
#                 z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotQueueForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

# class ResearchLabAliquotCheckinView(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IResearchLab)
#     grok.require('occams.lab.CheckinAliquot')
#     grok.name('checkin')

#     def __init__(self, context, request):
#         super(ResearchLabAliquotCheckinView, self).__init__(context, request)

#         self.crudform = self.getCrudForm()
#         self.filter = self.filterAliquot()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotCheckinForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def filterAliquot(self):
#         """ Create a form instance.
#             Returns:
#                 z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotFilterForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view


# class ResearchLabAliquotInventoryView(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IResearchLab)
#     grok.require('occams.lab.ModifyAliquot')
#     grok.name('inventory')

#     def __init__(self, context, request):
#         super(ResearchLabAliquotInventoryView, self).__init__(context, request)
#         self.crudform = self.getCrudForm()
#         self.filter = self.filterAliquot()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotInventoryForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def filterAliquot(self):
#         """ Create a form instance.
#             Returns:
#                 z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotInventoryFilterForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

# # ------------------------------------------------------------------------------
# # Crud Forms
# # ------------------------------------------------------------------------------

# class AliquotList(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IAliquotSupport)
#     grok.require('occams.lab.ViewAliquot')
#     grok.name('aliquot')

#     def __init__(self, context, request):
#         super(AliquotList, self).__init__(context, request)

#         self.crudform = self.getCrudForm()
#         self.filter = self.filterAliquot()
#         self.aliquotqueue = self.aliquotQueue()
#         self.lab_url = self.labUrl()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotListForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view
# #
#     def filterAliquot(self):
#         """ Create a form instance.
#             Returns:
#                 z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotFilterForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def aliquotQueue(self):
#         """ Create a form instance.
#             Returns:
#                 z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.AliquotQueueForm(context, self.request)
#         if hasattr(form, 'get_items') and not len(form.get_items()):
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def labUrl(self):
#         url = './'
#         catalog = getToolByName(self.context, 'portal_catalog')
#         brains = catalog.search({'portal_type':'occams.lab.researchlab'})
#         if len(brains):
#             url = brains[0].getURL()
#         return url

# # ------------------------------------------------------------------------------
# # ------------------------------------------------------------------------------
# class AliquotCheckList(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IChecklistSupport)
#     grok.require('occams.lab.ViewAliquot')
#     grok.name('checklist')

#     def __init__(self, context, request):
#         super(AliquotCheckList, self).__init__(context, request)
#         self.dsmanager = IAliquotManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
#         self.getaliquot = self.getAliquot()
#         self.currentUser = getSecurityManager().getUser().getId()

#     def getAliquot(self):
#         """
#         Get me some aliquot
#         """
#         kw = {}
#         kw['state'] = u'queued'
#         kw['modify-name'] = self.currentUser
#         for aliquot in self.dsmanager.filter_records(**kw):
#             yield IViewableAliquot(aliquot)


# class AliquotReceipt(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(IResearchLab)
#     grok.require('occams.lab.ViewAliquot')
#     grok.name('receipt')

#     def __init__(self, context, request):
#         super(AliquotReceipt, self).__init__(context, request)
#         self.dsmanager = IAliquotManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
#         self.getaliquot = self.getAliquot()
#         self.currentUser = getSecurityManager().getUser().getId()

#     def getAliquot(self):
#         """
#         Get me some aliquot
#         """

#         kw = {}
#         kw['state'] = u'pending-checkout'
#         kw['modify-name'] = self.currentUser
#         for aliquot in self.dsmanager.filter_records(**kw):
#             yield IViewableAliquot(aliquot)

# # ------------------------------------------------------------------------------
# # ------------------------------------------------------------------------------

# class SpecimenSupport(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(ISpecimenSupport)
#     grok.require('occams.lab.ViewSpecimen')
#     grok.name('specimen')

#     def __init__(self, context, request):
#         super(SpecimenSupport, self).__init__(context, request)
#         self.crudform = self.getCrudForm()
#         self.filter = self.filterSpecimen()
#         self.requestmore = self.requestSpecimen()

#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.SpecimenSupportForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def canRequestSpecimen(self):
#         return hasattr(self.context, 'visit_date')

#     def filterSpecimen(self):
#         """ Create a form instance.
#             Returns:
#                 z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = crud.SpecimenFilterForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     def requestSpecimen(self):
#         """ Create a form instance.
#             Returns:
#                 z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         if not self.canRequestSpecimen():
#             return None
#         form = crud.SpecimenAddForm(context, self.request)
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

