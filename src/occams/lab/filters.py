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
from occams.lab import FILTER_KEY
from sqlalchemy.orm.exc import NoResultFound
from avrc.aeh import interfaces as clinical


class SpecimenLabFilter(grok.MultiAdapter):
    grok.provides(interfaces.ISpecimenFilter)
    grok.adapts(interfaces.ILab, IHTTPRequest)

    def __init__(self, context, request):
        self.context = context
        browser_session = ISession(request)
        if FILTER_KEY in browser_session:
            self.filter = browser_session[FILTER_KEY]
        else:
            self.filter = {}

    def getQuery(self,  default_state=None, omitable=[]):
        if 'patient' in self.filter and 'patient' not in omitable:
            try:
                patient = Session.query(model.Patient).filter_by(our=self.filter['patient']).one()
            except NoResultFound:
                try:
                    patient = (
                           Session.query(model.Patient).filter(or_(
                                        model.Patient.legacy_number == self.filter['patient'],
                                        model.Patient.reference_numbers.any(reference_number = self.filter['patient'])
                                        )
                                )
                           ).one()
                except NoResultFound:
                    # bad patient identifier. return an empty query
                    return Session.query(model.Specimen).filter(model.Specimen.id.in_([]))
        query = (
            Session.query(model.Specimen)
                .filter(or_(
                            model.Specimen.location.has(name=self.context.location),
                            model.Specimen.previous_location.has(name=self.context.location)
                            )
                 )
            )
        if 'patient' in self.filter and 'patient' not in omitable:
            query = query.filter(model.Specimen.patient_id == patient.id)
        if 'specimen_type' in self.filter and 'specimen_type' not in omitable:
            query = query.filter(model.Specimen.specimen_type.has(name = self.filter['specimen_type']))
        if 'after_date' in self.filter and 'after_date' not in omitable:
            if 'before_date' in self.filter and 'before_date' not in omitable:
                query = query.filter(model.Specimen.collect_date >= self.filter['after_date'])
                query = query.filter(model.Specimen.collect_date <= self.filter['before_date'])
            else:
                query = query.filter(model.Specimen.collect_date == self.filter['after_date'])
        if self.filter.get('show_all', False) and 'show_all' not in omitable:
            query = query.join(model.SpecimenState).filter(model.SpecimenState.name.in_(['pending-draw', 'complete', 'cancel-draw', 'prepared']))
        elif default_state:
            query = query.filter(model.Specimen.state.has(name = default_state))
        # query = query.order_by(model.Specimen.id.desc())
        query = query.order_by(model.Specimen.collect_date.desc(), model.Specimen.patient_id, model.Specimen.specimen_type_id, model.Specimen.id)
        return query

    def getFilterFields(self, omitable=[]):
        """
        returns the appropriate fields for filtering in the specific context
        """
        selectable=['patient', 'specimen_type', 'after_date','before_date', 'show_all']
        for omitted in omitable:
            if omitted in selectable:
                selectable.remove(omitted)
        return z3c.form.field.Fields(interfaces.IFilterForm).select(*selectable)

    def getFilterValues(self):
        """
        returns the appropriate filter values for the specific context
        """
        retval = {}
        if self.filter:
            fields = self.getFilterFields()
            for name, filter in self.filter.iteritems():
                if name in fields and name != 'show_all':
                    retval[fields[name].field.title]= filter
            if 'show_all' in self.filter and self.filter['show_all']:
                retval[u'Specimen State'] = u'Showing All Specimen'
        return retval


class AliquotLabFilter(grok.MultiAdapter):
    grok.provides(interfaces.IAliquotFilter)
    grok.adapts(interfaces.ILab, IHTTPRequest)

    def __init__(self, context, request):
        self.context = context
        browser_session = ISession(request)
        if  FILTER_KEY in browser_session:
            self.filter = browser_session[FILTER_KEY]
        else:
            self.filter = {}

    def getQuery(self,  default_state=None, omitable=[]):
        if 'patient' in self.filter and 'patient' not in omitable:
            try:
                patient = Session.query(model.Patient).filter_by(our=self.filter['patient']).one()
            except NoResultFound:
                try:
                    patient = (
                           Session.query(model.Patient).filter(or_(
                                        model.Patient.legacy_number == self.filter['patient'],
                                        model.Patient.reference_numbers.any(reference_number = self.filter['patient'])
                                        )
                                )
                           ).one()
                except NoResultFound:
                    # bad patient identifier. return an empty query
                    return Session.query(model.Aliquot).filter(model.Aliquot.id.in_([]))
        query = (
            Session.query(model.Aliquot)
            .join(model.Aliquot.specimen)
            .join(model.Specimen.patient)
            .filter(or_(
                    model.Aliquot.location.has(name=self.context.location),
                    model.Aliquot.previous_location.has(name=self.context.location)
                    )
                )
            )
        if 'patient' in self.filter and 'patient' not in omitable and patient:
            query = query.filter(model.Specimen.patient_id == patient.id)
        if 'aliquot_type' in self.filter and 'aliquot_type' not in omitable:
            query = query.filter(model.Aliquot.aliquot_type.has(name = self.filter['aliquot_type']))
        if 'after_date' in self.filter and 'after_date' not in omitable:
            if 'before_date' in self.filter and 'before_date' not in omitable:
                query = query.filter(model.Aliquot.store_date >= self.filter['after_date'])
                query = query.filter(model.Aliquot.store_date <= self.filter['before_date'])
            else:
                query = query.filter(model.Aliquot.store_date == self.filter['after_date'])
        if default_state:
            query = query.filter(model.Aliquot.state.has(name = default_state))
        query = query.order_by(model.Specimen.patient_id, model.Aliquot.aliquot_type_id, model.Aliquot.id)
        return query

    def getFilterFields(self, omitable=[]):
        """
        returns the appropriate fields for filtering in the specific context
        """
        selectable=['patient', 'aliquot_type', 'after_date','before_date', 'freezer','rack','box','show_all']
        for omitted in omitable:
            if omitted in selectable:
                selectable.remove(omitted)
        return z3c.form.field.Fields(interfaces.IFilterForm).select(*selectable)

    def getFilterValues(self):
        """
        returns the appropriate filter values for the specific context
        """
        retval = {}
        if self.filter:
            fields = self.getFilterFields()
            for name, filter in self.filter.iteritems():
                if name in fields and name != 'show_all':
                    retval[fields[name].field.title]= filter
            if 'show_all' in self.filter and self.filter['show_all']:
                retval[u'Aliquot State']= u'Showing All Aliquot'
        return retval

class AliquotFilter(grok.MultiAdapter):
    grok.provides(interfaces.IAliquotFilter)
    grok.adapts(interfaces.IAliquotContext, IHTTPRequest)

    def __init__(self, context, request):
        self.context = context
        browser_session = ISession(request)
        if  FILTER_KEY in browser_session:
            self.filter = browser_session[FILTER_KEY]
        else:
            self.filter = {}

    def getQuery(self,  default_state=None, omitable=[]):
        if 'patient' in self.filter and 'patient' not in omitable:
            try:
                patient = Session.query(model.Patient).filter_by(our=self.filter['patient']).one()
            except NoResultFound:
                try:
                    patient = (
                           Session.query(model.Patient).filter(or_(
                                        model.Patient.legacy_number == self.filter['patient'],
                                        model.Patient.reference_numbers.any(reference_number = self.filter['patient'])
                                        )
                                )
                           ).one()
                except NoResultFound:
                    # bad patient identifier. return an empty query
                    return Session.query(model.Aliquot).filter(model.Aliquot.id.in_([]))
        query = (
            Session.query(model.Aliquot)
            .join(model.Aliquot.specimen)
            .filter(model.Aliquot.aliquot_type.has(id = self.context.item.id))
            .filter(or_(
                    model.Aliquot.location.has(name=self.context.location),
                    model.Aliquot.previous_location.has(name=self.context.location)
                    )
                )
            )
        if 'patient' in self.filter and 'patient' not in omitable and patient:
            query = query.filter(model.Specimen.patient_id == patient.id)
        if 'after_date' in self.filter and 'after_date' not in omitable:
            if 'before_date' in self.filter and 'before_date' not in omitable:
                query = query.filter(model.Aliquot.store_date >= self.filter['after_date'])
                query = query.filter(model.Aliquot.store_date <= self.filter['before_date'])
            else:
                query = query.filter(model.Aliquot.store_date == self.filter['after_date'])
        if 'freezer' in self.filter and 'freezer' not in omitable:
            query = query.filter(model.Aliquot.freezer == self.filter['freezer'])
        if 'rack' in self.filter and 'rack' not in omitable:
            query = query.filter(model.Aliquot.rack == self.filter['rack'])
        if 'box' in self.filter and 'box' not in omitable:
            query = query.filter(model.Aliquot.box == self.filter['box'])
        if self.filter.get('show_all', False) and 'show_all' not in omitable:
            query = query.join(model.AliquotState).filter(model.AliquotState.name.in_(['checked-in','missing','pending-checkout', 'checked-out']))
        elif default_state:
            query = query.filter(model.Aliquot.state.has(name = default_state))
        query = query.order_by(model.Specimen.patient_id, model.Aliquot.id)
        return query

    def getFilterFields(self, omitable=[]):
        """
        returns the appropriate fields for filtering in the specific context
        """
        selectable=['patient', 'aliquot_type', 'after_date','before_date', 'freezer','rack','box','show_all']
        for omitted in omitable:
            if omitted in selectable:
                selectable.remove(omitted)
        return z3c.form.field.Fields(interfaces.IFilterForm).select(*selectable)


    def getFilterValues(self):
        """
        returns the appropriate filter values for the specific context
        """
        retval = {}
        if self.filter:
            fields = self.getFilterFields()
            for name, filter in self.filter.iteritems():
                if name in fields and name != 'show_all':
                    retval[fields[name].field.title]= filter
            if 'show_all' in self.filter and self.filter['show_all']:
                retval[u'Aliquot State']= u'Showing All Aliquot'
        return retval


from zope import intid
from zope import component

class AliquotPatientFilter(grok.MultiAdapter):
    grok.provides(interfaces.IAliquotFilter)
    grok.adapts(clinical.IPatient, IHTTPRequest)

    def __init__(self, context, request):
        self.context = context
        browser_session = ISession(request)
        if  FILTER_KEY in browser_session:
            self.filter = browser_session[FILTER_KEY]
        else:
            self.filter = {}

    def getQuery(self,  default_state=None, omitable=[]):
        query = (
            Session.query(model.Aliquot)
            .join(model.Aliquot.specimen)
            .join(model.Specimen.patient)
            .filter(model.Patient.zid == component.getUtility(intid.IIntIds).getId(self.context))
            )
        if 'aliquot_type' in self.filter and 'aliquot_type' not in omitable:
            query = query.filter(model.Aliquot.aliquot_type.has(name = self.filter['aliquot_type']))
        if 'after_date' in self.filter and 'after_date' not in omitable:
            if 'before_date' in self.filter and 'before_date' not in omitable:
                query = query.filter(model.Aliquot.store_date >= self.filter['after_date'])
                query = query.filter(model.Aliquot.store_date <= self.filter['before_date'])
            else:
                query = query.filter(model.Aliquot.store_date == self.filter['after_date'])
        if 'freezer' in self.filter and 'freezer' not in omitable:
            query = query.filter(model.Aliquot.freezer == self.filter['freezer'])
        if 'rack' in self.filter and 'rack' not in omitable:
            query = query.filter(model.Aliquot.rack == self.filter['rack'])
        if 'box' in self.filter and 'box' not in omitable:
            query = query.filter(model.Aliquot.box == self.filter['box'])
        if self.filter.get('show_all', False) and 'show_all' not in omitable:
            query = query.join(model.AliquotState).filter(model.AliquotState.name.in_(['checked-in','missing','pending-checkout', 'checked-out']))
        elif default_state:
            query = query.filter(model.Aliquot.state.has(name = default_state))
        query = query.order_by(model.Aliquot.aliquot_type_id, model.Aliquot.id)
        return query

    def getFilterFields(self, omitable=[]):
        """
        returns the appropriate fields for filtering in the specific context
        """
        selectable=['aliquot_type',  'after_date','before_date','show_all']
        for omitted in omitable:
            if omitted in selectable:
                selectable.remove(omitted)
        return z3c.form.field.Fields(interfaces.IFilterForm).select(*selectable)


    def getFilterValues(self):
        """
        returns the appropriate filter values for the specific context
        """
        retval = {'Patient': self.context.getId()}
        if self.filter:
            fields = self.getFilterFields()
            for name, filter in self.filter.iteritems():
                if name in fields and name != 'show_all':
                    retval[fields[name].field.title]= filter
            if 'show_all' in self.filter and self.filter['show_all']:
                retval[u'Aliquot State']= u'Showing All Aliquot'
        return retval

class AliquotVisitFilter(grok.MultiAdapter):
    grok.provides(interfaces.IAliquotFilter)
    grok.adapts(clinical.IVisit, IHTTPRequest)

    def __init__(self, context, request):
        self.context = context
        browser_session = ISession(request)
        if  FILTER_KEY in browser_session:
            self.filter = browser_session[FILTER_KEY]
        else:
            self.filter = {}

    def getQuery(self,  default_state=None, omitable=[]):
        visit = zope.component.getMultiAdapter((self.context, Session), clinical.IClinicalModel)
        query = (
            Session.query(model.Aliquot)
            .join(model.Aliquot.specimen)
            .filter(model.Specimen.patient_id == visit.patient.id)
            .filter(model.Specimen.cycle_id.in_([cycle.id for cycle in visit.cycles]))
            )
        if 'aliquot_type' in self.filter and 'aliquot_type' not in omitable:
            query = query.filter(model.Aliquot.aliquot_type.has(name = self.filter['aliquot_type']))
        if 'after_date' in self.filter and 'after_date' not in omitable:
            if 'before_date' in self.filter and 'before_date' not in omitable:
                query = query.filter(model.Aliquot.store_date >= self.filter['after_date'])
                query = query.filter(model.Aliquot.store_date <= self.filter['before_date'])
            else:
                query = query.filter(model.Aliquot.store_date == self.filter['after_date'])
        if 'freezer' in self.filter and 'freezer' not in omitable:
            query = query.filter(model.Aliquot.freezer == self.filter['freezer'])
        if 'rack' in self.filter and 'rack' not in omitable:
            query = query.filter(model.Aliquot.rack == self.filter['rack'])
        if 'box' in self.filter and 'box' not in omitable:
            query = query.filter(model.Aliquot.box == self.filter['box'])
        if self.filter.get('show_all', False) and 'show_all' not in omitable:
            query = query.join(model.AliquotState).filter(model.AliquotState.name.in_(['checked-in','missing','pending-checkout', 'checked-out']))
        elif default_state:
            query = query.filter(model.Aliquot.state.has(name = default_state))
        query = query.order_by(model.Aliquot.aliquot_type_id, model.Aliquot.id)
        return query

    def getFilterFields(self, omitable=[]):
        """
        returns the appropriate fields for filtering in the specific context
        """
        selectable=['aliquot_type', 'show_all']
        for omitted in omitable:
            if omitted in selectable:
                selectable.remove(omitted)
        return z3c.form.field.Fields(interfaces.IFilterForm).select(*selectable)


    def getFilterValues(self):
        """
        returns the appropriate filter values for the specific context
        """
        cycletext = ''
        for cycle in self.context.cycles:
            cycletext += '%s, ' % cycle.title
        retval = {'Patient': self.context.aq_parent.getId(), 'Cycles': cycletext}
        if self.filter:
            fields = self.getFilterFields()
            for name, filter in self.filter.iteritems():
                if name in fields and name != 'show_all':
                    retval[fields[name].field.title]= filter
            if 'show_all' in self.filter and self.filter['show_all']:
                retval[u'Aliquot State']= u'Showing All Aliquot'
        return retval







class SpecimenVisitFilter(grok.MultiAdapter):
    grok.provides(interfaces.ISpecimenFilter)
    grok.adapts(clinical.IVisit, IHTTPRequest)

    def __init__(self, context, request):
        self.context = context
        browser_session = ISession(request)
        if  FILTER_KEY in browser_session:
            self.filter = browser_session[FILTER_KEY]
        else:
            self.filter = {}

    def getQuery(self,  default_state=None, omitable=[]):
        visit = zope.component.getMultiAdapter((self.context, Session), clinical.IClinicalModel)
        query = (
            Session.query(model.Specimen)
            .filter(model.Specimen.patient_id == visit.patient.id)
            .filter(model.Specimen.cycle_id.in_([cycle.id for cycle in visit.cycles]))
            )
        query = query.order_by(model.Specimen.specimen_type_id, model.Specimen.id.desc())
        return query

    def getFilterFields(self, omitable=[]):
        """
        returns the appropriate fields for filtering in the specific context
        """
        selectable=['specimen_type', 'show_all']
        for omitted in omitable:
            if omitted in selectable:
                selectable.remove(omitted)
        return z3c.form.field.Fields(interfaces.IFilterForm).select(*selectable)


    def getFilterValues(self):
        """
        returns the appropriate filter values for the specific context
        """
        cycletext = ''
        for cycle in self.context.cycles:
            cycletext += '%s, ' % cycle.title
        retval = {'Patient': self.context.aq_parent.getId(), 'Cycles': cycletext}
        if self.filter:
            fields = self.getFilterFields()
            for name, filter in self.filter.iteritems():
                if name in fields and name != 'show_all':
                    retval[fields[name].field.title]= filter
            if 'show_all' in self.filter and self.filter['show_all']:
                retval[u'Aliquot State']= u'Showing All Aliquot'
        return retval



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
