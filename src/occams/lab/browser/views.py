# from AccessControl import getSecurityManager
# from Products.CMFCore.utils import getToolByName
# from beast.browser.crud import NestedFormView
# from five import grok
# from occams.lab import MessageFactory as _, \
#                      SCOPED_SESSION_KEY
# from occams.lab.browser import crud

# from plone.directives import dexterity
# from z3c.saconfig import named_scoped_session
# from occams.lab import interfaces


# # ------------------------------------------------------------------------------
# # Clinical Lab Views |
# # --------------
# # These classes provide the various transitions and modifications of the pages
# # that support and modify specimen
# # ------------------------------------------------------------------------------

# # # ------------------------------------------------------------------------------
# # # ------------------------------------------------------------------------------

# # # ------------------------------------------------------------------------------
# # # ------------------------------------------------------------------------------

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
#     grok.context(interfaces.IResearchLab)
#     grok.require('hive.lab.AliquotSpecimen')
#     grok.name('research-view')

#     def update(self):
#         self.crudform = self.getCrudForm()
#         self.preview = self.getPreview()
#         super(ResearchLabView, self).update()

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
#         return []
#     #     session = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
#     #     kw = {'state':'pending-draw'}
#     #     if dsmanager.count_records() < 1:
#     #         return None
#     #     specimenlist = []
#     #     for specimen in dsmanager.filter_records(**kw):
#     #         vspecimen = IViewableSpecimen(specimen)
#     #         specimendict = {}
#     #         for prop in ['patient_title', 'study_title', 'protocol_title', 'pretty_type', 'pretty_tube_type']:
#     #             specimendict[prop] = getattr(vspecimen, prop)
#     #         for prop in ['tubes', 'date_collected']:
#     #             specimendict[prop] = getattr(specimen, prop)
#     #         specimenlist.append(specimendict)
            
#     #     return specimenlist

# # ------------------------------------------------------------------------------
# # ------------------------------------------------------------------------------
# class ResearchLabAliquotReady(dexterity.DisplayForm):
#     """
#     Primary view for a research lab object.
#     """
#     grok.context(interfaces.IResearchLab)
#     grok.require('hive.lab.AliquotSpecimen')
#     grok.name('ready')

#     def update(self):
#         self.crudform = self.getCrudForm()
#         self.labelqueue = self.getLabelQueue()
#         super(ResearchLabAliquotReady, self).update()

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
#     grok.context(interfaces.IResearchLab)
#     grok.require('hive.lab.ManageAliquot')
#     grok.name('prepared')

#     def update(self):
#         self.crudform = self.getCrudForm()
#         self.labelqueue = self.getLabelQueue()
#         self.filter = self.filterAliquot()
#         super(ResearchLabAliquotPrepared, self).update()
        
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
#     grok.context(interfaces.IResearchLab)
#     grok.require('hive.lab.ManageAliquot')
#     grok.name('checkedin')

#     def updaet(self):
#         self.crudform = self.getCrudForm()
#         super(ResearchLabAliquotCompleted, self).update()

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
#     grok.context(interfaces.IResearchLab)
#     grok.require('hive.lab.ModifyAliquot')
#     grok.name('edit-aliquot')

#     def update(self):
#         self.crudform = self.getCrudForm()
#         super(ResearchLabAliquotEditView, self).update()

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
#     grok.context(interfaces.IResearchLab)
#     grok.require('hive.lab.CheckoutAliquot')
#     grok.name('checkout')

#     def update(self):
#         self.crudform = self.getCrudForm()
#         self.formhelper = self.getUpdater()
#         self.aliquotqueue = self.aliquotQueue()
#         super(ResearchLabAliquotCheckoutView, self).update()

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
#     grok.context(interfaces.IResearchLab)
#     grok.require('hive.lab.CheckinAliquot')
#     grok.name('checkin')

#     def update(self):
#         self.crudform = self.getCrudForm()
#         self.filter = self.filterAliquot()
#         super(ResearchLabAliquotCheckinView, self).update()

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
#     grok.context(interfaces.IResearchLab)
#     grok.require('hive.lab.ModifyAliquot')
#     grok.name('inventory')

#     def update(self):
#         self.crudform = self.getCrudForm()
#         self.filter = self.filterAliquot()
#         super(ResearchLabAliquotInventoryView, self).update()

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
#     grok.context(interfaces.IAliquotSupport)
#     grok.require('hive.lab.ViewAliquot')
#     grok.name('aliquot')

#     def updaet(self):
#         self.crudform = self.getCrudForm()
#         self.filter = self.filterAliquot()
#         self.aliquotqueue = self.aliquotQueue()
#         self.lab_url = self.labUrl()
#         super(AliquotList, self).update()

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
#         #TODO: Fix me
#         # url = './'
#         # catalog = getToolByName(self.context, 'portal_catalog')
#         # brains = catalog.search({'portal_type':'hive.lab.researchlab'})
#         # if len(brains):
#         #     url = brains[0].getURL()
#         return None
        
# # ------------------------------------------------------------------------------
# # ------------------------------------------------------------------------------
# class AliquotCheckList(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(interfaces.IChecklistSupport)
#     grok.require('hive.lab.ViewAliquot')
#     grok.name('checklist')

#     def update(self):
#         #self.dsmanager = IAliquotManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
#         self.getaliquot = self.getAliquot()
#         self.currentUser = getSecurityManager().getUser().getId()
#         super(AliquotCheckList, self).update()

#     def getAliquot(self):
#         """
#         Get me some aliquot
#         """
#         kw = {}
#         kw['state'] = u'queued'
#         kw['modify-name'] = self.currentUser
#         for aliquot in []: # self.dsmanager.filter_records(**kw):
#             yield IViewableAliquot(aliquot)


# class AliquotReceipt(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(interfaces.IResearchLab)
#     grok.require('hive.lab.ViewAliquot')
#     grok.name('receipt')

#     def update(self):
#         # self.dsmanager = IAliquotManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
#         self.getaliquot = self.getAliquot()
#         self.currentUser = getSecurityManager().getUser().getId()
#         super(AliquotReceipt, self).update()
        
#     def getAliquot(self):
#         """
#         Get me some aliquot
#         """
#         kw = {}
#         kw['state'] = u'pending-checkout'
#         kw['modify-name'] = self.currentUser
#         return []
#         # for aliquot in self.dsmanager.filter_records(**kw):

#             # yield IViewableAliquot(aliquot)

# # ------------------------------------------------------------------------------
# # ------------------------------------------------------------------------------

# class SpecimenSupport(dexterity.DisplayForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     grok.context(interfaces.ISpecimenSupport)
#     grok.require('hive.lab.ViewSpecimen')
#     grok.name('specimen')

#     def update(self):
#         self.crudform = self.getCrudForm()
#         self.filter = self.filterSpecimen()
#         self.requestmore = self.requestSpecimen()
#         super(SpecimenSupport, self).update()

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

