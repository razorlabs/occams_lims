from Products.Five.browser import BrowserView
from collective.beaker.interfaces import ISession
import z3c.form
import datetime
from beast.browser import widgets
from sqlalchemy import or_
from Products.statusmessages.interfaces import IStatusMessage

from plone.z3cform.crud import crud
from occams.datastore.batch import SqlBatch
from avrc.aeh import interfaces as clinical
import os

from occams.lab import interfaces
from occams.lab import Session
from occams.lab import model
from occams.lab import MessageFactory as _
from beast.browser.crud import BatchNavigation
import sys
import json

# Override the choices in the addSpcimen view to not display a default value even though the fields are required.
overrideCycleChoicePrompt = z3c.form.widget.StaticWidgetAttribute(value=True, field=interfaces.IAddableSpecimen['specimen_cycle'])
overrideTypeChoicePrompt = z3c.form.widget.StaticWidgetAttribute(value=True, field=interfaces.IAddableSpecimen['specimen_type'])

class AddSpecimen(z3c.form.form.Form):
    """
    Overlay Specimen Add Form
    """
    label = _(u"Add More Specimen")
    description= _(u"Please enter the patient our number, protocol cycle, and specimen type.")
    ignoreContext = True

    fields = z3c.form.field.Fields(interfaces.IAddableSpecimen)

    def updateWidgets(self):
        """
        Apply The information in the browser request (from filtering) as values to this form
        """
        z3c.form.form.Form.updateWidgets(self)
        browser_session = ISession(self.request)
        if browser_session.has_key('patient'):
            self.widgets['specimen_patient_our'].value = browser_session['patient']

    @z3c.form.button.buttonAndHandler(_('Request More Specimen'), name='requestSpecimen')
    def requestSpecimen(self, action):
        data, errors = self.extractData()
        messages = IStatusMessage(self.request)
        if errors:
            messages.addStatusMessage(
                _(u'There was an error with your request.'),
                type=u'error'
                )
            return
        drawstate = Session.query(model.SpecimenState).filter_by(name=u'pending-draw').one()
        patient = Session.query(model.Patient).filter_by(our=data['specimen_patient_our']).one()
        visit_query = (
            Session.query(model.Visit)
            .filter(model.Visit.patient_id == patient.id)
            .filter(model.Visit.cycles.any(id = data['specimen_cycle'].id)))
        visit = visit_query.one()
        newSpecimen = model.Specimen(
                patient = patient,
                cycle = data['specimen_cycle'],
                specimen_type = data['specimen_type'],
                state=drawstate,
                collect_date = visit.visit_date,
                location = patient.site.lab_location,
                tubes = data['specimen_type'].default_tubes
            )
        Session.add(newSpecimen)
        Session.flush()
        messages.addStatusMessage(_(u"Specimen added for %s" % data['specimen_patient_our']), type=u'info')
        return  self.request.response.redirect(self.context.absolute_url())

    @z3c.form.button.buttonAndHandler(_('Cancel'), name='cancel')
    def cancel(self, action):
        return

class CycleByPatientJsonView(BrowserView):
    """
    JSON view for filtering the cycle list by patient for adding specimen
    """

    def __call__(self):
        """
        Return a clean list of available cycles filtered by patient
        """
        our_number = self.request.form['our_number']
        query = (
                 Session.query(model.Cycle.name, model.Cycle.title, model.Visit.visit_date)
                 .join(model.Visit.cycles)
                 .filter(model.Visit.patient.has(our=our_number))
                 .order_by(model.Visit.visit_date.desc())
            )
        data=[]
        for cycle in iter(query):
            data.append(
                        dict(
                        name = cycle[0],
                        title= cycle[1],
                        date = cycle[2].isoformat(),
                        ))
        self.request.response.setHeader(u'Content-type', u'application/json')
        return json.dumps(data)

class SpecimenFilterForm(z3c.form.form.Form):
    """
    Specimen Filter form. This form presents itself as an overlay on the Primary
    Clinical Lab view as a way to filter specimen.
    """
    ignoreContext = True
    label = u"Filter Specimen"
    description = _(u"Please enter filter criteria. You may filter by any or all options. "
                           u" Specimen are, by default, filtered by state (pending-draw). "
                           u"The filter will persist while you are logged in. ")
    fields = z3c.form.field.Fields(interfaces.ISpecimenFilterForm)

    def updateWidgets(self):
        """
        Apply The information in the browser request as values to this form
        """
        z3c.form.form.Form.updateWidgets(self)
        browser_session = ISession(self.request)
        for key, widget in self.widgets.items():
            if key in browser_session:
                value = browser_session[key]
                if type(value) == datetime.date:
                    widget.value = (unicode(value.year), unicode(value.month), unicode(value.day))
                elif type(value) == bool and value:
                    widget.value = ['selected']
                elif hasattr(widget, 'terms'):
                    widget.value = [value]
                else:
                    widget.value = value
                widget.update()

    @z3c.form.button.buttonAndHandler(u'Filter')
    def handleFilter(self, action):
        session = ISession(self.request)
        data, errors = self.extractData()
        messages = IStatusMessage(self.request)
        if errors:
            messages.addStatusMessage(
                _(u'There was an error with your request.'),
                type=u'error'
                )
            return
        for key, value in data.items():
            if value is not None:
                if getattr(value, 'name', False):
                    session[key] = value.name
                else:
                    session[key] = value
            elif session.has_key(key):
                del session[key]
        session.save()
        messages.addStatusMessage(_(u"Your Filter has been applied"), type=u'info')
        return self.request.response.redirect(self.context.absolute_url())

    @z3c.form.button.buttonAndHandler(u'Remove Filter')
    def handleClearFilter(self, action):
        session = ISession(self.request)
        session.clear()
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_(u"Your Filter has been cleared"), type=u'info')
        return self.request.response.redirect(self.context.absolute_url())

class SpecimenSubForm(crud.EditSubForm):
    """
    Individual row sub forms for the specimen crud form.
    """
    def updateWidgets(self):
        """
        Set the default processing location based on the property of the Clinical Lab of that same name
        """
        super(SpecimenSubForm, self).updateWidgets()
        context = self.context.context.context
        if 'processing_location' in self.widgets and not self.widgets['processing_location'].value :
            self.widgets['processing_location'].value = [context.processing_location]

class ClinicalLabEditForm(crud.EditForm):
    label = _(u"Specimen to be processed")

    editsubform_factory = SpecimenSubForm

    @property
    def action(self):
        return "%s?%spage=%s" % (self.request.getURL(), self.prefix, self._page())
    def render_batch_navigation(self):
        """
        Render the batch navigation to include the default styles for Plone
        """
        navigation = BatchNavigation(self.batch, self.request)
        def make_link(page):
            return "%s?%spage=%s" % (self.request.getURL(), self.prefix, page)
        navigation.make_link = make_link
        return navigation()

    @property
    def batch(self):
        query = self.context.query
        batch_size = self.context.batch_size or sys.maxint
        page = self._page()
        # When working with a batch, sometimes the size is reduced to a point
        # that there aren't enough entries for the page. To prevent an IndexError,
        # reduce the page size
        query_size = query.count()
        while (page * batch_size >= query_size and page > 0):
            page = page - 1
        batch = SqlBatch(query, start=page * batch_size, size=batch_size)
        return batch

    def saveChanges(self, action):
        """
        Apply changes to all items on the page
        """
        success = _("Your changes have been successfully applied")
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = ""
        # messages = IStatusMessage(self.request)
        for subform in self.subforms:
            data, errors = subform.extractData()
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            del data['select']
            # self.context.before_update(subform.content, data)
            changes = subform.applyChanges(data)
            if changes:
                if status is no_changes:
                    status = success
        Session.flush()
        self._update_subforms()
        # if status == partly_success:
        #     messages.addStatusMessage(status, type=u'error')
        # else:
        #     messages.addStatusMessage(status, type=u'info')
        self.status = status

    def changeState(self, action, state, acttitle):
        """
        Using the passed state, change the selected items to that state
        """
        selected = self.selected_items()
        # messages = IStatusMessage(self.request)
        if selected:
            number_specimen = len(selected)
            state = Session.query(model.SpecimenState).filter_by(name=state).one()
            for id, data in selected:
                obj = Session.query(model.Specimen).filter_by(id=id).one()
                obj.state = state
            Session.flush()
            self._update_subforms()
            self.status = _(u"%d Specimen have been changed to the status of %s." % (number_specimen, acttitle))
            # messages.addStatusMessage(status, type=u'info')
        else:
            self.status = _(u"Please select Specimen")
            # messages.addStatusMessage(status, type=u'error')


    def printLabels(self, action):
        selected = self.selected_items()
        label_list = []
        labelsheet = interfaces.ILabelPrinter(self.context.context)
        for id, item in selected:
            count = item.tubes
            if count:
                for i in range(count):
                    label_list.append(item)
        content = labelsheet.printLabelSheet(label_list)

        self.request.RESPONSE.setHeader("Content-type", "application/pdf")
        self.request.RESPONSE.setHeader("Content-disposition",
                                        "attachment;filename=labels.pdf")
        self.request.RESPONSE.setHeader("Cache-Control", "no-cache")
        self.request.RESPONSE.write(content)
        self.status = _(u"Your print is on its way")
        return self.status

    @z3c.form.button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @z3c.form.button.buttonAndHandler(_('Print Selected'), name='printed')
    def handlePrint(self, action):
        self.saveChanges(action)
        self.printLabels(action)
        return self.status

    @z3c.form.button.buttonAndHandler(_('Save All Changes'), name='updated')
    def handleUpdate(self, action):
        self.saveChanges(action)
        return self.status

    @z3c.form.button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        self._update_subforms()
        return self.status

    @z3c.form.button.buttonAndHandler(_('Mark Selected Undrawn'), name='cancel-draw')
    def handleCancelDraw(self, action):
        """
        Mark the selected specimen as cancelled. This is used for reporting purposes
        """
        self.saveChanges(action)
        self.changeState(action, 'cancel-draw', 'canceled')
        return self.status

class ClinicalLabViewForm(crud.CrudForm):
    """
    Primary view for a clinical lab object.
    """
    label = u"Specimen for Processing"
    description = _(u"")

    ignoreContext = True
    batch_size = 10

    addform_factory = crud.NullForm

    @property
    def editform_factory(self):
        return ClinicalLabEditForm

    @property
    def edit_schema(self):
        fields = z3c.form.field.Fields(interfaces.ISpecimen, mode=z3c.form.interfaces.DISPLAY_MODE).\
                    select('state',
                            )
        fields += z3c.form.field.Fields(interfaces.IViewableSpecimen, mode=z3c.form.interfaces.DISPLAY_MODE).\
                    select('patient_our',
                             'patient_initials',
                             'cycle_title',
                             'visit_date',
                             'tube_type',
                             )
        fields += z3c.form.field.Fields(interfaces.ISpecimen).\
                    select('specimen_type',
                             'tubes',
                             'collect_date',
                             'collect_time',
                             'processing_location',
                             'notes'
                             )
        return fields

    def update(self):
        self.update_schema = self.edit_schema
        self.query = self.getQuery()
        super(ClinicalLabViewForm, self).update()

    def updateWidgets(self):
        if self.update_schema is not None:
            if 'collect_time' in self.update_schema.keys():
                self.update_schema['collect_time'].widgetFactory = widgets.TimeFieldWidget
            if 'tubes' in self.update_schema.keys():
                self.update_schema['tubes'].widgetFactory = widgets.StorageFieldWidget

    def link(self, item, field):
        if not hasattr(self, '_v_patient_dict'):
            self._v_patient_dict={}
        if field == 'patient_our' and getattr(item.patient, 'zid', None):
            if self._v_patient_dict.has_key(item.patient.id):
                return self._v_patient_dict[item.patient.id]
            try:
                patient = clinical.IClinicalObject(item.patient)
            except KeyError:
                return None
            else:
                self._v_patient_dict[item.patient.id] = '%s/specimen' % patient.absolute_url()
                return self._v_patient_dict[item.patient.id]

    def getCount(self):
        return self.query.count()

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        if getattr(self, '_sqlBatch', None) is None:
            self._sqlBatch = SqlBatch(self.query)
        return self._sqlBatch

    def getQuery(self):
        if hasattr(self, '_v_query'):
            return self._v_query
        browsersession  = ISession(self.request)
        query = (
            Session.query(model.Specimen)
                .filter(model.Specimen.location.has(name=self.context.location))
            )
        if 'patient' in browsersession:
            query = query.join(model.Patient).filter(or_(
                                 model.Patient.our == browsersession['patient'],
                                 model.Patient.legacy_number == browsersession['patient'],
                                 model.Patient.reference_numbers.any(reference_number = browsersession['patient'])
                                 )
                        )
        if 'specimen_type' in browsersession:
            query = query.filter(model.Specimen.specimen_type.has(name = browsersession['specimen_type']))
        if 'before_date' in browsersession:
            if 'after_date' in browsersession:
                query = query.filter(model.Specimen.collect_date >= browsersession['before_date'])
                query = query.filter(model.Specimen.collect_date <= browsersession['after_date'])
            else:
                query = query.filter(model.Specimen.collect_date == browsersession['before_date'])
        if browsersession.get('show_all', False):
            query = query.join(model.SpecimenState).filter(model.SpecimenState.name.in_(['pending-draw', 'complete', 'cancel-draw']))
        else:
            query = query.filter(model.Specimen.state.has(name = 'pending-draw'))
        query = query.order_by(model.Specimen.id.desc())
        self._v_query = query
        return self._v_query

class ClinicalLabView(BrowserView):
    """
    Primary view for a clinical lab object.
    """

    def __init__(self, context, request):
        super(BrowserView, self).__init__(context, request)
        self.crud_form = ClinicalLabViewForm(context, request)
        self.crud_form.update()

    def currentFilter(self):
        browser_session = ISession(self.request)
        for name, description in interfaces.ISpecimenFilterForm.namesAndDescriptions():
            if name in browser_session:
                yield (description.title, browser_session[name])

    @property
    def entry_count(self):
        return self.crud_form.getCount()

    @property
    def crudForm(self):
        return self.crud_form
