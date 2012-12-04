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
import  zope.component
from occams.lab import interfaces
from occams.lab import Session
from occams.lab import model
from occams.lab import MessageFactory as _
from occams.lab.browser import labcrud
import json

# Override the choices in the addSpcimen view to not display a default value even though the fields are required.
overrideCycleChoicePrompt = z3c.form.widget.StaticWidgetAttribute(value=True, field=interfaces.IAddableSpecimen['specimen_cycle'])
overrideTypeChoicePrompt = z3c.form.widget.StaticWidgetAttribute(value=True, field=interfaces.IAddableSpecimen['specimen_type'])


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

    @property
    def fields(self):
        specimenfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        return specimenfilter.getFilterFields()

    def updateWidgets(self):
        """
        Apply The information in the browser request as values to this form
        """
        z3c.form.form.Form.updateWidgets(self)
        browser_session = ISession(self.request)
        if 'occams.lab.filter' in browser_session:
            specimenfilter = browser_session['occams.lab.filter']
            for key, widget in self.widgets.items():
                if key in specimenfilter:
                    value = specimenfilter[key]
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
        data, errors = self.extractData()
        messages = IStatusMessage(self.request)
        if errors:
            messages.addStatusMessage(
                _(u'There was an error with your request.'),
                type=u'error'
                )
            return
        browser_session = ISession(self.request)
        browser_session['occams.lab.filter'] = {}
        for key, value in data.items():
            if value is not None:
                if getattr(value, 'name', False):
                    browser_session['occams.lab.filter'][key] = value.name
                else:
                    browser_session['occams.lab.filter'][key] = value
        browser_session.save()
        messages.addStatusMessage(_(u"Your Filter has been applied"), type=u'info')
        return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())

    @z3c.form.button.buttonAndHandler(u'Remove Filter')
    def handleClearFilter(self, action):
        browser_session = ISession(self.request)
        browser_session['occams.lab.filter'] = {}
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_(u"Your Filter has been cleared"), type=u'info')
        return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())

# from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
class AddSpecimenForm(z3c.form.form.AddForm):
    """
    Specimen Add Form
    """
    label = _(u"Add More Specimen")
    description= _(u"Please enter the patient our number, protocol cycle, and specimen type.")
    ignoreContext = True
    # template = ViewPageTemplateFile('clinicallab_templates/addspecimen.pt')
    fields = z3c.form.field.Fields(interfaces.IAddableSpecimen)

    def updateWidgets(self):
        """
        Apply The information in the browser request (from filtering) as values to this form
        """
        z3c.form.form.Form.updateWidgets(self)
        browser_session = ISession(self.request)
        if 'occams.lab.filter' in browser_session and 'patient' in browser_session['occams.lab.filter']:
            self.widgets['specimen_patient_our'].value = browser_session['occams.lab.filter']['patient']

    @z3c.form.button.buttonAndHandler(_('Request More Specimen'), name='requestSpecimen')
    def requestSpecimen(self, action):
        data, errors = self.extractData()
        if errors:
            self.status =  _(u'There was an error with your request.')
            return
        drawstate = Session.query(model.SpecimenState).filter_by(name=u'pending-draw').one()
        patient = Session.query(model.Patient).filter_by(our=data['specimen_patient_our']).one()
        location = Session.query(model.Location).filter_by(name = self.context.location).one()
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
                location = location,
                tubes = data['specimen_type'].default_tubes
            )
        Session.add(newSpecimen)
        Session.flush()
        self.status = _(u"Specimen added for %s" % data['specimen_patient_our'])
        return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())

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

class ClinicalLabSubForm(crud.EditSubForm):
    """
    Individual row sub forms for the specimen crud form.
    """
    def updateWidgets(self):
        """
        Set the default processing location based on the property of the Clinical Lab of that same name
        """
        super(ClinicalLabSubForm, self).updateWidgets()
        context = self.context.context.context
        if 'processing_location' in self.widgets and not self.widgets['processing_location'].value :
            self.widgets['processing_location'].value = [context.processing_location]

class ClinicalLabEditForm(labcrud.OccamsCrudEditForm):
    label = _(u"Specimen to be processed")

    editsubform_factory = ClinicalLabSubForm

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


    @z3c.form.button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @z3c.form.button.buttonAndHandler(_('Print Selected'), name='printed')
    def handlePrint(self, action):
        self.saveChanges(action)
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
    label = _(u"Specimen for Processing")
    description = _(u"")

    ignoreContext = True
    batch_size = 10

    addform_factory = crud.NullForm

    editform_factory =  ClinicalLabEditForm

    add_schema = z3c.form.field.Fields(interfaces.IAddableSpecimen)

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
        self.query = self._getQuery()
        self.count = self.query.count()
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

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        if getattr(self, '_v_sqlBatch', None) is None:
            self._v_sqlBatch = SqlBatch(self.query)
        return self._v_sqlBatch

    def _getQuery(self):
        if hasattr(self, '_v_query'):
            return self._v_query
        specimenfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        self._v_query = specimenfilter.getQuery(default_state='pending-draw')
        return self._v_query

class ClinicalLabView(BrowserView):
    """
    Primary view for a clinical lab object.
    """

    def current_filter(self):
        specimenfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        return specimenfilter.getFilterValues()

    @property
    def entry_count(self):
        specimenfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        return specimenfilter.getCount()

    @property
    def crud_form(self):
        if not hasattr(self, '_v_crud_form'):
            self._v_crud_form = ClinicalLabViewForm(self.context, self.request)
            self._v_crud_form.update()
        return self._v_crud_form
