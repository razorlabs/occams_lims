# from Products.Five.browser import BrowserView
# from plone.z3cform import layout
# from collective.beaker.interfaces import ISession
# from occams.lab import interfaces

# from zope.publisher.interfaces import IHTTPRequest
# import zope.interface
# import zope.component
# from avrc.aeh import interfaces as clinical

# class SpecimenVisitFilter(object):
#     """
#     """
#     zope.component.adapts(clinical.IVisit, IHTTPRequest)
#     zope.interface.implements(interfaces.ISpecimenFilter)

#     def __init__(self, context, request):
#         self.context = context
#         self.browser_session = ISession(request)

#     def patient(self):

#     after_date = zope.schema.Date(
#         title=_(u"Sample Date"),
#         description=_(u"Samples on this date. If Limit Date is set as well, will show samples between those dates"),
#         required=False

#         )

#     before_date = zope.schema.Date(
#         title=_(u"Sample Limit Date"),
#         description=_(u"Samples before this date. Only applies if Sample Date is also set"),
#         required=False
#         )

#     show_all = zope.schema.Bool(
#         title=_(u"Show all Samples"),
#         description=_(u"Show all samples, including missing, never drawn, checked out, etc"),
#         required=False
#         )

# class ISpecimenFilterForm(IFilterForm):
#     """
#     """
#     specimen_type = zope.schema.Choice(
#         title=u"Type of Sample",
#         vocabulary='occams.lab.specimentypevocabulary',
#         required=False
#         )

#     state = zope.schema.List(
#         title=_(u'State'),
#         description = _(u""),
#         value_type = zope.schema.Choice(
#             title=u"state choice",
#             vocabulary="occams.lab.specimenstatevocabulary",
#             )
#         )
