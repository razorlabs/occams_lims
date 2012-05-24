
from occams.lab import MessageFactory as _, \
                     SCOPED_SESSION_KEY
# from occams.lab.browser import crud

from z3c.form import button, field, form as z3cform
from Products.Five.browser import BrowserView

from z3c.saconfig import named_scoped_session
from occams.lab import interfaces
from occams.lab import model
import zope.schema
from plone.z3cform import layout
from beast.browser import widgets
from zope.app.intid.interfaces import IIntIds
from occams.lab.browser import base
from beast.browser.crud import NestedFormView

SUCCESS_MESSAGE = _(u"Successfully updated")
PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
NO_CHANGES = _(u"No changes made.")

class SpecimenCoreButtons(base.CoreButtons):
    z3cform.extends(base.CoreButtons)

    @property
    def _stateModel(self):
        return model.SpecimenState

    @property 
    def sampletype(self):
        return u'specimen'
        
    @property 
    def _model(self):
        return model.Specimen

    @button.buttonAndHandler(_('Print Selected'), name='printed')
    def handlePrint(self, action):
        self.saveChanges(action)
        self.printLabels(action)
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Save All Changes'), name='updated')
    def handleUpdate(self, action):
        self.saveChanges(action)
        return self.request.response.redirect(self.action)

class SpecimenCoreForm(base.CoreForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """
    @property
    def edit_schema(self):
        fields = field.Fields(interfaces.IViewableSpecimen).\
                    select('patient_our',
                             'patient_initials',
                             'cycle_title',
                             'visit_date', 
                             'tube_type',
                             )
        fields += field.Fields(interfaces.ISpecimen).\
                    select('specimen_type',
                             'tubes', 
                             'collect_date', 
                             'collect_time',
                             'notes'
                             )
        return fields

    def link(self, item, field):
        if field == 'patient_our':
            intids = zope.component.getUtility(IIntIds)
            patient = intids.getObject(item.patient.zid)
            url = '%s/specimen' % patient.absolute_url()
            return url
        elif field == 'visit_date' and getattr(item.visit, 'zid', None):
            intids = zope.component.getUtility(IIntIds)
            visit = intids.getObject(item.visit.zid)
            url = '%s/specimen' % visit.absolute_url()
            return url

    def updateWidgets(self):
        if self.update_schema is not None:
            if 'collect_time' in self.update_schema.keys():
                self.update_schema['collect_time'].widgetFactory = widgets.TimeFieldWidget
            if 'tubes' in self.update_schema.keys():
                self.update_schema['tubes'].widgetFactory = widgets.StorageFieldWidget

    def get_query(self):
        #makes testing a LOT easier
        session = named_scoped_session(SCOPED_SESSION_KEY)
        query = (
            session.query(model.Specimen)
                .join(model.Patient)
                .join(model.Cycle)
                .join(model.Visit)
                .join(model.SpecimenType)
                .join(model.SpecimenState)
                .filter(model.SpecimenState.name.in_(self.display_state))
                .order_by( model.Visit.visit_date.desc(), model.Patient.our, model.SpecimenType.name)
            )
        return query

class SpecimenPendingButtons(SpecimenCoreButtons):
    z3cform.extends(SpecimenCoreButtons)

    @property
    def prefix(self):
        return 'specimen-pending.'

    @button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Batch Selected'), name='batched')
    def handleBatchDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'batched', 'batched')
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Postpone Selected'), name='postponed')
    def handlePostponeDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'postponed', 'postponed')

        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Selected Undrawn'), name='rejected')
    def handleCancelDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'rejected', 'canceled')
        return self.request.response.redirect(self.action)

class ClinicalLabViewForm(SpecimenCoreForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen Pending Draw"
    description = _(u"Specimen pending processing.")

    @property
    def editform_factory(self):
        return SpecimenPendingButtons

    @property
    def display_state(self):
        return (u"pending-draw",)

class ClinicalLabView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = ClinicalLabViewForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

class SpecimenBatchedButtons(SpecimenCoreButtons):
    label = _(u"")
    z3cform.extends(SpecimenCoreButtons)

    @property
    def prefix(self):
        return 'specimen-pending.'

    @button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Draw selected'), name='draw')
    def handleDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'pending-draw', 'pending draw')
        return self.request.response.redirect(self.action)

class ClinicalLabBatchedForm(SpecimenCoreForm):
    """
    Primary view for a clinical lab object.
    """

    @property
    def editform_factory(self):
        return SpecimenBatchedButtons

    @property
    def display_state(self):
        return (u"batched",)

class ClinicalLabBatched(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = ClinicalLabBatchedForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

class SpecimenPostponedButtons(SpecimenCoreButtons):
    label = _(u"")
    z3cform.extends(SpecimenCoreButtons)

    @property
    def prefix(self):
        return 'specimen-pending.'

    @button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Batch Selected'), name='batched')
    def handleBatchDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'batched', 'batched')
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Selected Undrawn'), name='rejected')
    def handleCancelDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'rejected', 'canceled')
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Draw selected'), name='draw')
    def handleDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'pending-draw', 'pending draw')
        return self.request.response.redirect(self.action)

class ClinicalLabPostponedForm(SpecimenCoreForm):
    """
    Primary view for a clinical lab object.
    """
    @property
    def editform_factory(self):
        return SpecimenPostponedButtons

    @property
    def display_state(self):
        return (u"postponed",)

class ClinicalLabPostponed(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = ClinicalLabPostponedForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

class ClinicalLabDoneForm(SpecimenCoreForm):
    """
    Primary view for a clinical lab object.
    """
    @property
    def editform_factory(self):
        return SpecimenPendingButtons

    @property
    def display_state(self):
        return (u"complete","cancel-draw")

ClinicalLabDone = layout.wrap_form(ClinicalLabDoneForm)

