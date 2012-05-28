
from occams.lab import MessageFactory as _, \
                     SCOPED_SESSION_KEY
from z3c.form.interfaces import DISPLAY_MODE

from z3c.saconfig import named_scoped_session
from z3c.form import button, field, form as z3cform
from beast.browser.crud import NestedFormView

from occams.lab import model
from Products.Five.browser import BrowserView
from datetime import date
from occams.lab import interfaces
from zope.app.intid.interfaces import IIntIds
import zope.component
from beast.browser import widgets
from avrc.aeh.interfaces import IClinicalMarker
from occams.lab.browser import base

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
    Base Crud form for editing specimen. Some specimen will need to be 
    """ 
    @property
    def edit_schema(self):
        fields = field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     )
        fields += field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select('aliquot_type')
        fields += field.Fields(interfaces.IAliquot).\
            select('labbook',
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
            intids = zope.component.getUtility(IIntIds)
            patient = intids.getObject(item.specimen.patient.zid)
            url = '%s/aliquot' % patient.absolute_url()
            return url
        elif field == 'cycle_title' and getattr(item.specimen.visit, 'zid', None):
            intids = zope.component.getUtility(IIntIds)
            visit = intids.getObject(item.specimen.visit.zid)
            url = '%s/aliquot' % visit.absolute_url()
            return url

    def updateWidgets(self):
        super(AliquotCoreForm, self).updateWidgets()
        if self.update_schema is not None:
            if 'labbook' in self.update_schema.keys():
                self.update_schema['labbook'].widgetFactory = widgets.AmountFieldWidget
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
        session = named_scoped_session(SCOPED_SESSION_KEY)
        query = (
            session.query(model.Aliquot)
            .join(model.Aliquot.state)
            .join(model.Aliquot.aliquot_type)
            .join(model.Aliquot.specimen)
            .order_by(model.Aliquot.id.asc())
            )
        if self.display_state:
            query = query.filter(model.AliquotState.name.in_(self.display_state))
        return query


class AliquotForm(AliquotCoreForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen Pending Draw"
    description = _(u"Specimen pending processing.")

    def update(self):
        self.view_schema = field.Fields(interfaces.IAliquot).select('state') + self.edit_schema
        super(base.CoreForm, self).update()

    @property
    def edit_schema(self):
        fields = field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     )
        fields += field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select('aliquot_type')

        fields += field.Fields(interfaces.IAliquot).\
            select('labbook',
                     'store_date',
                     'inventory_date',
                     'location',
                     )
        fields += field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('vol_count', 
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
        return None

class AliquotPatientForm(AliquotForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen Pending Draw"
    description = _(u"Specimen pending processing.")

    def get_query(self):
        query = super(AliquotPatientForm, self).get_query()
        patient = IClinicalMarker(self.context).modelObj()
        query = query.filter(model.Specimen.patient == patient)
        return query


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

class AliquotVisitForm(AliquotForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen Pending Draw"
    description = _(u"Specimen pending processing.")

    def get_query(self):
        query = super(AliquotVisitForm, self).get_query()
        visit = IClinicalMarker(self.context).modelObj()
        query = query.filter(model.Specimen.patient == visit.patient)
        query = query.join(model.Specimen.cycle).filter(model.Cycle.id.in_([cycle.id for cycle in visit.cycles]))
        # query = query.filter(model.Specimen.visit == visit).filter(model.Specimen.collect_date == visit.visit_date)
        return query

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
