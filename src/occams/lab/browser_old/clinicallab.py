
# from occams.lab import MessageFactory as _
# # from occams.lab.browser import crud
# from z3c.form.interfaces import DISPLAY_MODE

# from z3c.form import button, form as z3cform
# from Products.Five.browser import BrowserView

# from plone.z3cform import layout
# from beast.browser.crud import NestedFormView
# from occams.lab.browser.specimen import SpecimenCoreButtons
# from occams.lab.browser.specimen import SpecimenCoreForm
# from occams.lab.browser.specimen import SpecimenForm
# from occams.lab.browser.specimen import SpecimenFilterForm
# from z3c.form import button, field, form as z3cform
# from occams.lab import interfaces
# from datetime import date
# from datetime import timedelta
# from occams.lab import model
# from occams.lab import Session
# SUCCESS_MESSAGE = _(u"Successfully updated")
# PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
# NO_CHANGES = _(u"No changes made.")
# from collective.beaker.interfaces import ISession
# from sqlalchemy import or_
# from avrc.aeh import model as clinical

# class SpecimenPendingButtons(SpecimenCoreButtons):
#     z3cform.extends(SpecimenCoreButtons)

#     @property
#     def prefix(self):
#         return 'specimen-pending.'

#     @button.buttonAndHandler(_('Complete selected'), name='completed')
#     def handleCompleteDraw(self, action):
#         self.saveChanges(action)
#         self.changeState(action, 'complete', 'completed')
#         return self.request.response.redirect(self.action)

#     @button.buttonAndHandler(_('Batch Selected'), name='batched')
#     def handleBatchDraw(self, action):
#         self.saveChanges(action)
#         self.changeState(action, 'batched', 'batched')
#         return self.request.response.redirect(self.action)

#     @button.buttonAndHandler(_('Postpone Selected'), name='postponed')
#     def handlePostponeDraw(self, action):
#         self.saveChanges(action)
#         self.changeState(action, 'postponed', 'postponed')

#         return self.request.response.redirect(self.action)

#     @button.buttonAndHandler(_('Mark Selected Undrawn'), name='rejected')
#     def handleCancelDraw(self, action):
#         self.saveChanges(action)
#         self.changeState(action, 'cancel-draw', 'canceled')
#         return self.request.response.redirect(self.action)

# class ClinicalLabViewForm(SpecimenCoreForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     label = u""
#     description = _(u"")

#     @property
#     def editform_factory(self):
#         return SpecimenPendingButtons

#     @property
#     def display_state(self):
#         return (u"pending-draw",)

#     def get_query(self):

#         #makes testing a LOT easier
#         if hasattr(self, '_v_query'):
#             return self._v_query

#         query = (
#             Session.query(model.Specimen)
#                 .join(model.Patient)
#                 .join(model.Cycle)
#                 .join(model.SpecimenType)
#                 .join(model.SpecimenState)
#             )
#         omitted = getattr(self.context, 'omit_filter', [])
#         browsersession  = ISession(self.request)
#         if 'patient' in browsersession.keys() and 'patient' not in omitted:
#             query = query.filter(or_(
#                                  model.Patient.our == browsersession['patient'],
#                                  model.Patient.legacy_number == browsersession['patient'],
#                                  model.Patient.reference_numbers.any(reference_number=browsersession['patient'])
#                                  )
#                         )
#         if self.display_state:
#             query = query.filter(model.SpecimenState.name.in_(self.display_state))

#         query = query.order_by(model.Specimen.collect_date, model.Patient.our, model.SpecimenType.name)
#         self._v_query = query
#         return self._v_query

# class ClinicalLabView(BrowserView):
#     """
#     Primary view for a research lab object.
#     """
#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = ClinicalLabViewForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

#     # def getFilterInfo(self):
#     #     session = ISession(self.request)
#     #     for key, value in session.items():
#     # def getFilterForm(self):
#     #     context = self.context.aq_inner
#     #     context.omit_filter=['specimen_type',]
#     #     form = SpecimenFilterForm(context, self.request)
#     #     view = NestedFormView(context, self.request)
#     #     view = view.__of__(context)
#     #     view.form_instance = form
#     #     return view

# class SpecimenBatchedButtons(SpecimenCoreButtons):
#     label = _(u"")
#     z3cform.extends(SpecimenCoreButtons)

#     @property
#     def prefix(self):
#         return 'specimen-pending.'

#     @button.buttonAndHandler(_('Complete selected'), name='completed')
#     def handleCompleteDraw(self, action):
#         self.saveChanges(action)
#         self.changeState(action, 'complete', 'completed')
#         return self.request.response.redirect(self.action)

#     @button.buttonAndHandler(_('Draw selected'), name='draw')
#     def handleDraw(self, action):
#         self.saveChanges(action)
#         self.changeState(action, 'pending-draw', 'pending draw')
#         return self.request.response.redirect(self.action)

# class ClinicalLabBatchedForm(SpecimenCoreForm):
#     """
#     Primary view for a clinical lab object.
#     """

#     @property
#     def editform_factory(self):
#         return SpecimenBatchedButtons

#     @property
#     def display_state(self):
#         return (u"batched",)

# class ClinicalLabBatched(BrowserView):
#     """
#     Primary view for a research lab object.
#     """
#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = ClinicalLabBatchedForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

# class SpecimenPostponedButtons(SpecimenCoreButtons):
#     label = _(u"")
#     z3cform.extends(SpecimenCoreButtons)

#     @property
#     def prefix(self):
#         return 'specimen-pending.'

#     @button.buttonAndHandler(_('Complete selected'), name='completed')
#     def handleCompleteDraw(self, action):
#         self.saveChanges(action)
#         self.changeState(action, 'complete', 'completed')
#         return self.request.response.redirect(self.action)

#     @button.buttonAndHandler(_('Batch Selected'), name='batched')
#     def handleBatchDraw(self, action):
#         self.saveChanges(action)
#         self.changeState(action, 'batched', 'batched')
#         return self.request.response.redirect(self.action)

#     @button.buttonAndHandler(_('Mark Selected Undrawn'), name='rejected')
#     def handleCancelDraw(self, action):
#         self.saveChanges(action)
#         self.changeState(action, 'cancel-draw', 'canceled')
#         return self.request.response.redirect(self.action)

#     @button.buttonAndHandler(_('Draw selected'), name='draw')
#     def handleDraw(self, action):
#         self.saveChanges(action)
#         self.changeState(action, 'pending-draw', 'pending draw')
#         return self.request.response.redirect(self.action)

# class ClinicalLabPostponedForm(SpecimenCoreForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     @property
#     def editform_factory(self):
#         return SpecimenPostponedButtons

#     @property
#     def display_state(self):
#         return (u"postponed",)

# class ClinicalLabPostponed(BrowserView):
#     """
#     Primary view for a research lab object.
#     """
#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = ClinicalLabPostponedForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view

# class SpecimenRecoverButtons(SpecimenCoreButtons):
#     label = _(u"")

#     @property
#     def prefix(self):
#         return 'specimen-pending.'

#     @button.buttonAndHandler(_('Recover selected'), name='recover')
#     def handleRecoverDraw(self, action):
#         self.changeState(action, 'pending-draw', 'recovered')
#         return self.request.response.redirect(self.action)

# class ClinicalLabDoneForm(SpecimenCoreForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     @property
#     def editform_factory(self):
#         return SpecimenRecoverButtons

#     @property
#     def edit_schema(self):
#         fields = field.Fields(interfaces.ISpecimen, mode=DISPLAY_MODE).\
#             select('state')
#         fields += field.Fields(interfaces.IViewableSpecimen, mode=DISPLAY_MODE).\
#         select( 'patient_our', 'patient_initials', 'cycle_title',
#        'specimen_type_name', 'tube_type')
#         fields += field.Fields(interfaces.ISpecimen, mode=DISPLAY_MODE).\
#         select('tubes', 'collect_date', 'collect_time', 'notes')
#         return fields

#     @property
#     def display_state(self):
#         return (u"complete","cancel-draw", "rejected")

#     def get_query(self):
#         query = super(ClinicalLabDoneForm, self).get_query()
#         yesterday =  date.today() - timedelta(1)
#         query = query.filter(model.Specimen.modify_date >= yesterday)
#         return query

# class ClinicalLabDone(BrowserView):
#     """
#     Primary view for a research lab object.
#     """
#     def getCrudForm(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = ClinicalLabDoneForm(context, self.request)
#         if hasattr(form, 'getCount') and form.getCount() < 1:
#             return None
#         view = NestedFormView(context, self.request)
#         view = view.__of__(context)
#         view.form_instance = form
#         return view
