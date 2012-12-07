
# from occams.lab import MessageFactory as _
# from five import grok
# # from occams.lab.browser import crud
# from z3c.form.interfaces import DISPLAY_MODE

# from z3c.form import button, field, form as z3cform
# from Products.Five.browser import BrowserView

# from occams.lab import interfaces
# from occams.lab import model
# import zope.schema
# from plone.directives import form

# from Products.CMFCore.utils import getToolByName
# from plone.z3cform import layout
# from beast.browser import widgets

# from occams.lab.browser import base
# from beast.browser.crud import NestedFormView
# from Products.statusmessages.interfaces import IStatusMessage
# from sqlalchemy import or_
# from collective.beaker.interfaces import ISession
# from zope.schema.vocabulary import SimpleTerm, \
#                                    SimpleVocabulary
# import os
# from avrc.aeh import model as clinical
# from z3c.form.widget import StaticWidgetAttribute

# from sqlalchemy.orm import object_session
# from occams.lab import Session
# from avrc.aeh.interfaces import IClinicalObject
# import json

# from plone.z3cform.crud import crud
# from occams.lab.browser import labcrud
# import z3c.form

# class AliquotTypeAddForm(crud.AddForm):
#     label = _(u"Add Aliquot Type")


# class AliquotTypeEditForm(crud.EditForm):
#     label = _(u"Aliquot Types")

#     def saveChanges(self, action):
#         """
#         Apply changes to all items on the page
#         """
#         success = _("Your changes have been successfully applied")
#         partly_success = _(u"Some of your changes could not be applied.")
#         status = no_changes = ""
#         for subform in self.subforms:
#             data, errors = subform.extractData()
#             if errors:
#                 if status is no_changes:
#                     status = subform.formErrorsMessage
#                 elif status is success:
#                     status = partly_success
#                 continue
#             del data['select']
#             self.context.before_update(subform.content, data)
#             changes = subform.applyChanges(data)
#             if changes:
#                 if status is no_changes:
#                     status = success
#         Session.flush()
#         self._update_subforms()
#         self.status = status

#     @z3c.form.button.buttonAndHandler(_('Save Changes'), name='save')
#     def handleSaveChanges(self, action):
#         self.saveChanges(action)
#         return self.status

# class AliquotTypeForm(crud.CrudForm):
#     """
#     Primary view for a clinical lab object.
#     """
#     label = _(u"Aliquot Types")
#     description = _(u"")

#     ignoreContext = True

#     addform_factory = AliquotTypeAddForm

#     editform_factory =  AliquotTypeEditForm

#     add_schema = z3c.form.field.Fields(interfaces.IAliquotType).select('title', )
#     update_schema = z3c.form.field.Fields(interfaces.IAliquotType).select('title', )

# #     def link(self, item, field):
# #         if not hasattr(self, '_v_patient_dict'):
# #             self._v_patient_dict={}
# #         if field == 'patient_our' and getattr(item.patient, 'zid', None):
# #             if self._v_patient_dict.has_key(item.patient.id):
# #                 return self._v_patient_dict[item.patient.id]
# #             try:
# #                 patient = clinical.IClinicalObject(item.patient)
# #             except KeyError:
# #                 return None
# #             else:
# #                 self._v_patient_dict[item.patient.id] = '%s/specimen' % patient.absolute_url()
# #                 return self._v_patient_dict[item.patient.id]

#     def get_items(self):
#         """
#         Use a special ``get_item`` method to return a query instead for batching
#         """
#         query = (
#                  Session.query(model.AliquotType)
#                  .filter(model.AliquotType.specimen_type == self.context.item)
#                  .order_by(model.AliquotType.title.asc())
#                  )
#         return [(aliq.id, aliq) for aliq in iter(query)]



# class SpecimenTypeEditForm(z3c.form.form.EditForm):
#     """
#     Form for editing the properties of a specimen
#     """
#     fields = z3c.form.field.Fields(interfaces.ISpecimenType).select('title','tube_type', 'default_tubes')

#     def getContent(self):
#         return self.context.item

# WrappedSpecimenTypeEditForm = layout.wrap_form(SpecimenTypeEditForm)

# class SpecimenView(BrowserView):
#     """
#     View of a specimen type. Allows editing of
#     """
#     @property
#     def edit_specimen_type_form(self):
#         specimen_edit_form = WrappedSpecimenTypeEditForm(self.context, self.request)
#         specimen_edit_form.update()
#         return specimen_edit_form

#     @property
#     def crud_form(self):
#         if not hasattr(self, '_v_crud_form'):
#             self._v_crud_form = AliquotTypeForm(self.context, self.request)
#             self._v_crud_form.update()
#         return self._v_crud_form

#     @property
#     def list_aliquot_types(self):
#         query = (
#             Session.query(model.AliquotType)
#             .filter(model.AliquotType.specimen_type == self.context.item)
#             .order_by(model.AliquotType.title.asc())
#             )
#         for aliquot_type in iter(query):
#             url = "./%s/%s" %(self.context.item.name, aliquot_type.name)
#             yield {'url': url, 'title': aliquot_type.title}


