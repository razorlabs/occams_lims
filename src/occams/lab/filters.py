# from Products.Five.browser import BrowserView
# from plone.z3cform import layout
from collective.beaker.interfaces import ISession
from occams.lab import interfaces
from occams.lab import Session
from zope.publisher.interfaces.http import IHTTPRequest
import zope.interface
import zope.component
# from avrc.aeh import interfaces as clinical
from occams.lab import model
from sqlalchemy import or_
import z3c.form
from five import grok


class SpecimenLabFilter(grok.MultiAdapter):
    grok.provides(interfaces.ISpecimenFilter)
    grok.adapts(interfaces.ILab, IHTTPRequest)

    def __init__(self, context, request):
        self.context = context
        browser_session = ISession(request)
        if 'occams.lab.filter' in browser_session:
            self.filter = browser_session['occams.lab.filter']
        else:
            self.filter = {}

    def getQuery(self, default_state=None):
        query = (
            Session.query(model.Specimen)
                .filter(model.Specimen.location.has(name=self.context.location))
            )
        if 'patient' in self.filter:
            query = query.join(model.Patient).filter(or_(
                                 model.Patient.our == self.filter['patient'],
                                 model.Patient.legacy_number == self.filter['patient'],
                                 model.Patient.reference_numbers.any(reference_number = self.filter['patient'])
                                 )
                        )
        if 'specimen_type' in self.filter:
            query = query.filter(model.Specimen.specimen_type.has(name = self.filter['specimen_type']))
        if 'before_date' in self.filter:
            if 'after_date' in self.filter:
                query = query.filter(model.Specimen.collect_date >= self.filter['before_date'])
                query = query.filter(model.Specimen.collect_date <= self.filter['after_date'])
            else:
                query = query.filter(model.Specimen.collect_date == self.filter['before_date'])
        if self.filter.get('show_all', False):
            query = query.join(model.SpecimenState).filter(model.SpecimenState.name.in_(['pending-draw', 'complete', 'cancel-draw']))
        elif default_state:
            query = query.filter(model.Specimen.state.has(name = default_state))
        query = query.order_by(model.Specimen.id.desc())
        return query

    def getFilterFields(self):
        """
        returns the appropriate fields for filtering in the specific context
        """
        return z3c.form.field.Fields(interfaces.ISpecimenFilterForm)

    def getFilterValues(self):
        """
        returns the appropriate filter values for the specific context
        """
        if self.filter:
            fields = self.getFilterFields()
            for name, filter in self.filter.iteritems():
                if name in fields and name != 'show_all':
                    yield(fields[name].field.title, filter)
            if 'show_all' in self.filter and self.filter['show_all']:
                yield (u'Specimen State', u'Pending Draw, Complete, Draw Cancelled')
            else:
                yield(u'Specimen State', u'Pending Draw')
        else:
            yield(u'Specimen State', u'Pending Draw')

    def getCount(self):
        """
        Returns the number of items to be returned
        """
        return self.getQuery().count()

class AliquotLabFilter(grok.MultiAdapter):
    grok.provides(interfaces.IAliquotFilter)
    grok.adapts(interfaces.ILab, IHTTPRequest)

    def __init__(self, context, request):
        self.context = context
        browser_session = ISession(request)
        if 'occams.lab.filter' in browser_session:
            self.filter = browser_session['occams.lab.filter']
        else:
            self.filter = {}

    def getQuery(self):
        query = (
            Session.query(model.Specimen)
                .filter(model.Specimen.location.has(name=self.context.location))
            )
        if 'patient' in self.filter:
            query = query.join(model.Patient).filter(or_(
                                 model.Patient.our == self.filter['patient'],
                                 model.Patient.legacy_number == self.filter['patient'],
                                 model.Patient.reference_numbers.any(reference_number = self.filter['patient'])
                                 )
                        )
        if 'specimen_type' in self.filter:
            query = query.filter(model.Specimen.specimen_type.has(name = self.filter['specimen_type']))
        if 'before_date' in self.filter:
            if 'after_date' in self.filter:
                query = query.filter(model.Specimen.collect_date >= self.filter['before_date'])
                query = query.filter(model.Specimen.collect_date <= self.filter['after_date'])
            else:
                query = query.filter(model.Specimen.collect_date == self.filter['before_date'])
        if self.filter.get('show_all', False):
            query = query.join(model.SpecimenState).filter(model.SpecimenState.name.in_(['pending-draw', 'complete', 'cancel-draw']))
        else:
            query = query.filter(model.Specimen.state.has(name = 'pending-draw'))
        query = query.order_by(model.Specimen.id.desc())
        return query

    def getFilterFields(self):
        """
        returns the appropriate fields for filtering in the specific context
        """
        return z3c.form.field.Fields(interfaces.IAliquotFilterForm)

    def getFilterValues(self):
        """
        returns the appropriate filter values for the specific context
        """
        if self.filter:
            for name, filter in self.filter.iteritems():
                if name in interfaces.IAliquotFilterForm and name != 'show_all':
                    yield(interfaces.IAliquotFilterForm[name].title, filter)
            if 'show_all' in self.filter and self.filter['show_all']:
                yield (u'Specimen State', u'Pending Draw, Complete, Draw Cancelled')
            else:
                yield(u'Specimen State', u'Pending Draw')
        else:
            yield(u'Specimen State', u'Pending Draw')

    def getCount(self):
        """
        Returns the number of items to be returned
        """
        return self.getQuery().count()


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
