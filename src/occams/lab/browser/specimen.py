
from occams.lab import MessageFactory as _, \
                     SCOPED_SESSION_KEY
# from occams.lab.browser import crud
from z3c.form.interfaces import DISPLAY_MODE

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
from avrc.aeh.interfaces import IClinicalMarker

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


    def printLabels(self, action):
        selected = self.selected_items()
        label_list = []
        labelsheet = interfaces.ILabelPrinter(self.context.context)
        for id, item in selected:
            count = item.tubes
            if count is None or count < 1:
                count = 1
            for i in range(count):
                label_list.append(item)
        content = labelsheet.printLabelSheet(label_list)

        self.request.RESPONSE.setHeader("Content-type", "application/pdf")
        self.request.RESPONSE.setHeader("Content-disposition",
                                        "attachment;filename=labels.pdf")
        self.request.RESPONSE.setHeader("Cache-Control", "no-cache")
        self.request.RESPONSE.write(content)
        self.status = _(u"Your print is on its way. Refresh the page to view only unprinted labels.")


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
        fields = field.Fields(interfaces.IViewableSpecimen, mode=DISPLAY_MODE).\
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
                .order_by( model.Visit.visit_date.desc(), model.Patient.our, model.SpecimenType.name)
            )
        if self.display_state:

            query = query.filter(model.SpecimenState.name.in_(self.display_state))
        return query

class SpecimenForm(SpecimenCoreForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen Pending Draw"
    description = _(u"Specimen pending processing.")

    def update(self):
        self.view_schema = field.Fields(interfaces.ISpecimen).select('state') + self.edit_schema
        super(base.CoreForm, self).update()
        # self.update_schema = None

    @property
    def editform_factory(self):
        return SpecimenCoreButtons

    @property
    def display_state(self):
        return None


class SpecimenPatientForm(SpecimenForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen Pending Draw"
    description = _(u"Specimen pending processing.")

    def get_query(self):
        query = super(SpecimenPatientForm, self).get_query()
        patient = IClinicalMarker(self.context).modelObj()
        query = query.filter(model.Specimen.patient == patient)
        return query


class SpecimenPatientView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = SpecimenPatientForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

class SpecimenVisitForm(SpecimenForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen Pending Draw"
    description = _(u"Specimen pending processing.")

    def get_query(self):
        query = super(SpecimenVisitForm, self).get_query()
        visit = IClinicalMarker(self.context).modelObj()
        query = query.filter(model.Specimen.visit == visit).filter(model.Specimen.collect_date == visit.visit_date)
        return query

class SpecimenVisitView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = SpecimenVisitForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view


