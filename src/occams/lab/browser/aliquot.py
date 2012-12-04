
from occams.lab import MessageFactory as _
from occams.lab import Session

from z3c.form.interfaces import DISPLAY_MODE

from z3c.form import button, field, form as z3cform
from beast.browser.crud import NestedFormView

from occams.lab import model
from Products.Five.browser import BrowserView
from occams.lab import interfaces
import zope.component
from beast.browser import widgets
from occams.lab.browser import base
from collective.beaker.interfaces import ISession
from AccessControl import getSecurityManager
from occams.datastore import model as dsmodel
import sys
from Products.CMFCore.utils import getToolByName
from sqlalchemy import or_
from avrc.aeh.interfaces import IClinicalObject, IClinicalModel

SUCCESS_MESSAGE = _(u"Successfully updated")
PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
NO_CHANGES = _(u"No changes made.")

class AliquotFilterForm(base.FilterFormCore):
    """
    """
    @property
    def fields(self):
        if hasattr(self.context, 'omit_filter'):
            omitables = self.context.omit_filter
            return field.Fields(interfaces.IAliquotFilterForm).omit(*omitables)
        return field.Fields(interfaces.IAliquotFilterForm)

class AliquotButtonCore(base.CoreButtons):
    label = _(u"")

    @property
    def _stateModel(self):
        return model.AliquotState

    @property
    def _model(self):
        return model.Aliquot

    sampletype=u"aliquot"

    def queueLabels(self, action):
        """
        Place these aliquot in the print queue
        """
        selected = self.selected_items()
        if selected:
            labelsheet = interfaces.ILabelPrinter(self.context.context)
            for id, obj in selected:
                labelsheet.queueLabel(obj)
            self.status = _(u"Your %s have been queued." % self.sampletype)
        else:
            self.status = _(u"Please select %s to queue." % self.sampletype)

class AliquotCoreForm(base.CoreForm):
    """
    Base Crud form for aliquot
    """
    batch_size = 20

    @property
    def edit_schema(self):
        fields = field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('aliquot_id',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title'
                     )
        fields += field.Fields(interfaces.IAliquot).\
            select(
                     'volume',
                     'cell_amount',
                     'store_date',
                     'freezer',
                     'rack',
                     'box',
                     'special_instruction',
                     'notes')
        return fields

    def link(self, item, field):
        if field == 'patient_our':
            try:
                patient = IClinicalObject(item.specimen.patient)
                url = '%s/aliquot' % patient.absolute_url()
                return url
            except KeyError:
                return None
        elif field == 'cycle_title':
            try:
                patient = item.specimen.patient
                # this might be slow, but it's the only fix we have available
                visit_query = (
                    Session.query(model.Visit)
                    .filter(model.Visit.patient == patient)
                    .filter(model.Visit.cycles.any(id=item.specimen.cycle.id))
                    )
                visit_entries = visit_query.all()
                if len(visit_entries) == 1:
                    visit_entry = visit_entries[0]
                    visit = IClinicalObject(visit_entry)
                    url = '%s/aliquot' % visit.absolute_url()
                else:
                    url = None
                return url
            except KeyError:
                return None

    def updateWidgets(self):
        super(AliquotCoreForm, self).updateWidgets()
        if self.update_schema is not None:
            if 'volume' in self.update_schema.keys():
                self.update_schema['volume'].widgetFactory = widgets.AmountFieldWidget
            if 'cell_amount' in self.update_schema.keys():
                self.update_schema['cell_amount'].widgetFactory = widgets.AmountFieldWidget
            if 'freezer' in self.update_schema.keys():
                self.update_schema['freezer'].widgetFactory = widgets.StorageFieldWidget
            if 'rack' in self.update_schema.keys():
                self.update_schema['rack'].widgetFactory = widgets.StorageFieldWidget
            if 'box' in self.update_schema.keys():
                self.update_schema['box'].widgetFactory = widgets.StorageFieldWidget
            if 'thawed_num' in self.update_schema.keys():
                self.update_schema['thawed_num'].widgetFactory = widgets.StorageFieldWidget

    def get_query(self):
        query = (
            Session.query(model.Aliquot)
            .join(model.Aliquot.state)
            .join(model.Aliquot.aliquot_type)
            .join(model.Aliquot.specimen)
            )
        if self.display_state:
            query = query.filter(model.AliquotState.name.in_(self.display_state))
        query = (
                    query
                    .join(model.Aliquot.specimen)
                    .join(model.Specimen.patient)
                    .join(model.Aliquot.aliquot_type)
                    .order_by(model.Patient.id, model.AliquotType.id, model.Aliquot.id)
                    )
        return query


class AliquotLimitForm(AliquotCoreForm):

    def get_query(self):
        query = (
            Session.query(model.Aliquot)
            .select_from(model.Aliquot)
            .join(model.Aliquot.state)
            .join(model.Aliquot.aliquot_type)
            .join(model.Aliquot.specimen)
            .join(model.Specimen.patient)
            )
        browsersession  = ISession(self.request)
        omitted = getattr(self.context, 'omit_filter', [])

        if 'patient' in browsersession.keys() and 'patient' not in omitted:
            query = query.filter(or_(
                                 model.Patient.our == browsersession['patient'],
                                 model.Patient.legacy_number == browsersession['patient'],
                                 model.Patient.reference_numbers.any(reference_number = browsersession['patient'])
                                 )
                        )
        if 'aliquot_type' in browsersession.keys() and 'aliquot_type' not in omitted:
            query = query.filter(model.AliquotType.name == browsersession['aliquot_type'])
        if 'after_date' in browsersession.keys() and 'after_date' not in omitted:
            if 'before_date' in browsersession.keys() and 'before_date' not in omitted:
                query = query.filter(model.Aliquot.store_date >= browsersession['after_date'])
                query = query.filter(model.Aliquot.store_date <= browsersession['before_date'])
            else:
                query = query.filter(model.Aliquot.store_date == browsersession['after_date'])

        if self.display_state and not browsersession.get('show_all', False):
            query = query.filter(model.AliquotState.name.in_(self.display_state))
        query = (
                    query
                    .order_by(model.Patient.id, model.AliquotType.id, model.Aliquot.id)
                    )
        return query

class AliquotForm(AliquotLimitForm):
    """
    Primary view for a clinical lab object.
    """
    label = u""
    description = _(u"")

    def update(self):
        self.view_schema = self.edit_schema
        super(base.CoreForm, self).update()

    @property
    def edit_schema(self):
        fields = field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('aliquot_id',
                     'state_title',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title'
                     )

        fields += field.Fields(interfaces.IAliquot).\
            select(
                     'store_date',
                     'inventory_date',
                     )
        fields += field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select(
                    'location_title',
                     'vol_count',
                     'frb',
                     'thawed_num',
                     )

        fields += field.Fields(interfaces.IAliquot).\
            select( 'special_instruction',
                      'notes',
                     )
        return fields

    @property
    def editform_factory(self):
        return AliquotButtonCore

    @property
    def display_state(self):
        return ('checked-in',)



class AliquotListButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-queue.'

    @button.buttonAndHandler(_('Add to Queue'), name='queue')
    def handleQueue(self, action):
        self.changeState(action, 'queued', 'Queued')

        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Inaccurate'), name='incorrect')
    def handleInaccurate(self, action):
        self.changeState(action, 'incorrect', 'incorrect')

        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Hold'), name='hold')
    def handleRecoverAliquot(self, action):
        self.changeState(action, 'hold', 'Held')

        return self.request.response.redirect(self.action)

class AliquotHoldButtons(AliquotButtonCore):
    """
    """
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-hold.'

    @button.buttonAndHandler(_('Print List'), name='print')
    def handleQueue(self, action):
        return self.request.response.redirect('%s/%s' % (self.context.context.absolute_url(), 'checklist'))

    @button.buttonAndHandler(_('Check Out'), name='checkout')
    def handleCheckout(self, action):
        self.changeState(action, 'pending-checkout', 'Checked Out')

        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Release From Queue'), name='release')
    def handleRelease(self, action):
        self.changeState(action, 'checked-in', 'Released')

        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Inaccurate'), name='incorrect')
    def handleInaccurate(self, action):
        self.changeState(action, 'incorrect', 'incorrect')
        #
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Missing'), name='missing')
    def handleMissing(self, action):
        self.changeState(action, 'missing', 'Missing')

        return self.request.response.redirect(self.action)

class AliquotQueueForm(AliquotCoreForm):
    """
    """

    @property
    def view_schema(self):
        fields = field.Fields(interfaces.IViewableAliquot).\
            select('state_title',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title',
                     'vol_count',
                     )
        fields += field.Fields(interfaces.IAliquot).\
            select('store_date')
        fields += field.Fields(interfaces.IViewableAliquot).\
            select('frb')
        fields += field.Fields(interfaces.IAliquot).\
            select('notes')
        return fields

    edit_schema = None

    editform_factory = AliquotHoldButtons

    batch_size = 70

    @property
    def display_state(self):
        return (u"queued",)

    def get_query(self):
        current_user = Session.query(dsmodel.User).filter_by(key = getSecurityManager().getUser().getId()).one()
        query = super(AliquotQueueForm, self).get_query()
        query = query.filter(model.Aliquot.modify_user_id == current_user.id)
        query = (
                    query
                    .join(model.Aliquot.specimen)
                    .join(model.Specimen.patient)
                    .join(model.Aliquot.aliquot_type)
                    .order_by(model.Patient.id, model.AliquotType.id, model.Aliquot.id)
                    )
        return query

class AliquotTypeForm(AliquotForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen Pending Draw"
    description = _(u"Specimen pending processing.")

    def get_query(self):
        query = super(AliquotTypeForm, self).get_query()
        query = query.filter(model.Aliquot.aliquot_type_id == self.context.item.id)
        return query

    @property
    def editform_factory(self):
        return AliquotListButtons

class AliquotView(BrowserView):
    """
    Primary view for a research lab object.
    """

    def getFilterForm(self):
        context = self.context.aq_inner
        context.omit_filter=['aliquot_type']
        form = AliquotFilterForm(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotTypeForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def labUrl(self):
        #TODO: make this site specific
        url = './'
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.search({'portal_type':'occams.lab.researchlab'})
        if len(brains):
            url = brains[0].getURL()
        return url

    def getQueueForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotQueueForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

class AliquotPatientForm(AliquotForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen Pending Draw"
    description = _(u"Specimen pending processing.")

    def get_query(self):
        query = super(AliquotPatientForm, self).get_query()
        patient = zope.component.getMultiAdapter((self.context, Session), IClinicalModel)
        query = query.filter(model.Specimen.patient == patient)
        return query

    @property
    def editform_factory(self):
        return AliquotListButtons

class AliquotPatientView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getFilterForm(self):
        context = self.context.aq_inner
        context.omit_filter=['patient',]
        form = AliquotFilterForm(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotPatientForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getQueueForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotQueueForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def labUrl(self):
        #TODO: Make this site specific
        url = './'
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.search({'portal_type':'occams.lab.researchlab'})
        if len(brains):
            url = brains[0].getURL()
        return url

class AliquotVisitForm(AliquotForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen Pending Draw"
    description = _(u"Specimen pending processing.")

    def get_query(self):
        query = super(AliquotVisitForm, self).get_query()
        visit = zope.component.getMultiAdapter((self.context, Session), IClinicalModel)
        query = query.filter(model.Specimen.patient == visit.patient)
        query = query.join(model.Specimen.cycle).filter(model.Cycle.id.in_([cycle.id for cycle in visit.cycles]))
        return query

    @property
    def editform_factory(self):
        return AliquotListButtons

class AliquotVisitView(BrowserView):
    """
    Primary view for a research lab object.
    """

    def getFilterForm(self):
        context = self.context.aq_inner
        context.omit_filter=['patient', 'before_date', 'after_date']
        form = AliquotFilterForm(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotVisitForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view


    def getQueueForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotQueueForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def labUrl(self):
        #TODO: Make site specific
        url = './'
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.search({'portal_type':'occams.lab.researchlab'})
        if len(brains):
            url = brains[0].getURL()
        return url

class AliquotChecklist(BrowserView):
    """
    """
    def getQueueItems(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotQueueForm(context, self.request)
        form.batch_size = sys.maxint

        for aliquot in iter(form.get_query()):
            viewableAliquot=interfaces.IViewableAliquot(aliquot)
            ret = {}
            ret['id'] = aliquot.id
            ret['patient_our'] = viewableAliquot.patient_our
            ret['patient_legacy_number'] = viewableAliquot.patient_legacy_number
            ret['cycle_title'] = viewableAliquot.cycle_title
            ret['store_date'] = aliquot.store_date
            ret['aliquot_type_title'] = viewableAliquot.aliquot_type_title
            ret['vol_count'] = viewableAliquot.vol_count
            ret['frb'] = viewableAliquot.frb

            yield ret

    def labUrl(self):
        #TODO: Make site specific
        url = './'
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.search({'portal_type':'occams.lab.researchlab'})
        if len(brains):
            url = brains[0].getURL()
        return url

class AliquotReciept(BrowserView):
    """
    """
    def getQueueItems(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotQueueForm(context, self.request)
        form.batch_size = sys.maxint

        for aliquot in iter(form.get_query()):
            viewableAliquot=interfaces.IViewableAliquot(aliquot)
            ret = {}
            ret['id'] = aliquot.id
            ret['patient_our'] = viewableAliquot.patient_our
            ret['patient_legacy_number'] = viewableAliquot.patient_legacy_number
            ret['cycle_title'] = viewableAliquot.cycle_title
            ret['store_date'] = aliquot.store_date
            ret['aliquot_type_title'] = viewableAliquot.aliquot_type_title
            ret['vol_count'] = viewableAliquot.vol_count
            ret['special_instruction_title'] = aliquot.special_instruction.title
            ret['notes'] = aliquot.notes
            ret['sent_notes'] = aliquot.sent_notes


            yield ret

    def labUrl(self):
        url = './'
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.search({'portal_type':'occams.lab.researchlab'})
        if len(brains):
            url = brains[0].getURL()
        return url

