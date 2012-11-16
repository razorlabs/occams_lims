
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

# from sqlalchemy.orm import object_session
# from occams.lab import Session
# from avrc.aeh.interfaces import IClinicalObject
# import json

# class CycleByPatientJsonView(BrowserView):
#     """
#     JSON view for form fields
#     """

#     def __call__(self):
#         """
#         Returns a clean copy of the current state of the field.
#         Additionally adds an extra ``view`` field in the JSON object
#         for rendering the field on the client side
#         """
#         our_number = self.request.form['our_number']
#         query = (
#                  Session.query(model.Cycle.name, model.Cycle.title, model.Visit.visit_date)
#                  .join(model.Visit.cycles)
#                  .join(model.Visit.patient)
#                  .filter_by(our=our_number)
#                  .order_by(model.Visit.visit_date.desc())
#             )
#         data=[]
#         for cycle in iter(query):
#             data.append(
#                         dict(
#                         name = cycle[0],
#                         title= cycle[1],
#                         date = cycle[2].isoformat(),
#                         ))
#         self.request.response.setHeader(u'Content-type', u'application/json')
#         return json.dumps(data)



