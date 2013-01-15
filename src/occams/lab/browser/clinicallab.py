from Products.Five.browser import BrowserView
from collective.beaker.interfaces import ISession
import z3c.form
from beast.browser import widgets

from plone.z3cform.crud import crud

import  zope.component
from occams.lab import interfaces
from occams.lab import Session
from occams.lab import model
from occams.lab import MessageFactory as _
from occams.lab.browser import common
import json

from Products.statusmessages.interfaces import IStatusMessage

SPECIMEN_LABEL_QUEUE = 'specimen_label_queue'

# Override the choices in the addSpcimen view to not display a default value even though the fields are required.
overrideCycleChoicePrompt = z3c.form.widget.StaticWidgetAttribute(value=True, field=interfaces.IAddableSpecimen['specimen_cycle'])
overrideTypeChoicePrompt = z3c.form.widget.StaticWidgetAttribute(value=True, field=interfaces.IAddableSpecimen['specimen_type'])

class SpecimenFilterForm(common.LabFilterForm):
    """
    Specimen Filter form. This form presents itself as an overlay on the Primary
    Clinical Lab view as a way to filter specimen.
    """

    label = u"Filter Specimen"

    @property
    def fields(self):
        specimenfilter =  zope.component.getMultiAdapter((self.context, self.request), interfaces.ISpecimenFilter)
        omitable = []
        if 'omit' in self.request:
            if type(self.request['omit']) == list:
                omitable = self.request['omit']
            else:
                omitable =  [self.request['omit'],]
        return specimenfilter.getFilterFields(omitable=omitable)

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




class SpecimenLabelForm(z3c.form.form.Form):
    """
    Specimen Filter form. This form presents itself as an overlay on the Primary
    Clinical Lab view as a way to filter specimen.
    """
    # label = u"Label Aliquot"
    description = _(u"Please enter the starting column and row for a partially used. ")

    def specimen_for_labels(self):
        printablespecimen = []
        browser_session = ISession(self.request)
        if SPECIMEN_LABEL_QUEUE in browser_session:
            specimenQ = (
                Session.query(model.Specimen)
                .filter(model.Specimen.id.in_(browser_session[SPECIMEN_LABEL_QUEUE]))
                .order_by(model.Specimen.patient_id, model.Specimen.specimen_type_id, model.Specimen.id)
                )
            for specimen in iter(specimenQ):
                count = specimen.tubes
                if count:
                    for i in range(count):
                        printablespecimen.append(specimen)
        return printablespecimen

    @property
    def label(self):
        label_length = len(self.specimen_for_labels())
        return u"Print Specimen Labels for %d Specimen" % label_length

    fields = z3c.form.field.Fields(interfaces.ILabelPrinter)

    @z3c.form.button.buttonAndHandler(_('Print Specimen Labels'), name='print')
    def handlePrintSpecimen(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = 'Please correct the indicated errors'
            return
        printablespecimen = self.specimen_for_labels()
        content = interfaces.ISpecimenLabelPrinter(self.context).printLabelSheet(printablespecimen, data['startcol'], data['startrow'])
        browser_session = ISession(self.request)
        browser_session[SPECIMEN_LABEL_QUEUE] = set()
        browser_session.save()
        self.request.RESPONSE.setHeader("Content-type", "application/pdf")
        self.request.RESPONSE.setHeader("Content-disposition",
                                        "attachment;filename=labels.pdf")
        self.request.RESPONSE.setHeader("Cache-Control", "no-cache")
        self.request.RESPONSE.write(content)
        self.status = _(u"You print is on its way")
        return

    @z3c.form.button.buttonAndHandler(u'Clear Label Queue')
    def handleClearFilter(self, action):
        browser_session = ISession(self.request)
        browser_session[SPECIMEN_LABEL_QUEUE] = set()
        browser_session.save()
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_(u"Your Queue has been cleared"), type=u'info')
        return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())


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
        specimen = self.content
        if 'location' in self.widgets and specimen.location.name == context.location and not specimen.previous_location:
            self.widgets['location'].value = [context.processing_location]
        browser_session = ISession(self.request)
        if SPECIMEN_LABEL_QUEUE in browser_session \
                and 'label_queue' in self.widgets \
                and self.content.id in browser_session[SPECIMEN_LABEL_QUEUE]:
            self.widgets['label_queue'].value = specimen.tubes and specimen.tubes or 0

class ClinicalLabEditForm(common.OccamsCrudEditForm):
    label = _(u"Specimen to be processed")

    editsubform_factory = ClinicalLabSubForm

    def changeState(self, action, state, acttitle):
        """
        Using the passed state, change the selected items to that state
        """
        selected = self.selected_items()
        if selected:
            number_specimen = len(selected)
            state = Session.query(model.SpecimenState).filter_by(name=state).one()
            for id, data in selected:
                obj = Session.query(model.Specimen).filter_by(id=id).one()
                obj.state = state
            Session.flush()
            self._update_subforms()
            self.status = _(u"%d Specimen have been changed to the status of %s." % (number_specimen, acttitle))
        else:
            self.status = _(u"Please select Specimen")

    @z3c.form.button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @z3c.form.button.buttonAndHandler(_('Save All Changes'), name='updated')
    def handleUpdate(self, action):
        self.saveChanges(action)
        return self.status

    @z3c.form.button.buttonAndHandler(_('Toggle Print Queue'), name='queueprint')
    def handlePrintSpecimen(self, action):
        self.saveChanges(action)
        selected = self.selected_items()
        if selected:
            browser_session = ISession(self.request)
            if SPECIMEN_LABEL_QUEUE in browser_session:
                label_queue = browser_session[SPECIMEN_LABEL_QUEUE]
            else:
                browser_session[SPECIMEN_LABEL_QUEUE] = label_queue = set()
            alquot_number = len(selected)
            for id, data in selected:
                if id in label_queue:
                    label_queue.discard(id)
                else:
                    label_queue.add(id)
            browser_session.save()
            self._update_subforms()
            self.status = _(u"Specimen print queue is changed." )
        else:
            self.status = _(u"Please select Specimen")
        return self.request.response.redirect(self.action)

    def labelsinqueue(self):
        browser_session = ISession(self.request)
        if SPECIMEN_LABEL_QUEUE in browser_session:
            return len(browser_session[SPECIMEN_LABEL_QUEUE])
        return False

    @z3c.form.button.buttonAndHandler(_('Print Labels'), name='print', condition=labelsinqueue)
    def handlePrintLabels(self, action):
        pass

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

    @z3c.form.button.buttonAndHandler(_('Add Specimen'), name='addspecimen')
    def handleAddSpecimen(self, action):
        # trigger a javascript overlay that will allow adding of specimen
        pass


class ClinicalLabViewForm(common.OccamsCrudForm):
    """
    Primary view for a clinical lab object.
    """
    label = _(u"Specimen for Processing")

    batch_size = 10

    editform_factory =  ClinicalLabEditForm

    @property
    def edit_schema(self):
        fields = z3c.form.field.Fields(interfaces.ISpecimen, mode=z3c.form.interfaces.DISPLAY_MODE).\
                    select('state',
                            )
        fields += z3c.form.field.Fields(interfaces.IViewableSpecimen, mode=z3c.form.interfaces.DISPLAY_MODE).\
                    select('label_queue',
                             'patient_our',
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
                             'location',
                             'notes'
                             )
        return fields

    def updateWidgets(self):
        if self.update_schema is not None:
            if 'collect_time' in self.update_schema.keys():
                self.update_schema['collect_time'].widgetFactory = widgets.TimeFieldWidget
            if 'tubes' in self.update_schema.keys():
                self.update_schema['tubes'].widgetFactory = widgets.StorageFieldWidget


    # def before_update(self, content, data):
    #     location = Session.query(model.Location).filter_by(name = self.context.location).one()
    #     data['previous_location'] = location

    def _getQuery(self):
        # multiadapter defined in filters.py
        specimenfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        return specimenfilter.getQuery(default_state='pending-draw')

class ClinicalLabView(common.OccamsLabView):
    """
    Primary view for a clinical lab object.
    """

    instructions = [
        {'title':'Select All',
        'description': 'Select or deselect all items displayed on the current page.'},
        {'title':'Toggle Print Queue',
        'description': 'Saves all changes, and then adds the selected specimen to the print queue'},
        {'title':'Print Labels',
        'description': 'Prints labels for the specimen in the print queue'},
        {'title':'Save All Changes',
        'description': 'Saves all of the changes entered to the database. This applies ' \
        'to all specimen, not just selected specimen.'},
        {'title':'Complete Selected',
        'description': 'Saves all changes entered to the database (for all specimen). Then ' \
        'marks the selected specimen as complete. If the location you\'ve entered for the items ' \
        'is the current lab, you will find them in <a href="./batched">batched</a>'},
        {'title':'Mark Selected Undrawn',
        'description': 'Mark the selected specimen as undrawn.'},
        {'title':'Add Specimen',
        'description': 'Adds a new specimen. This action DOES NOT save current changes.'},
        ]

    def current_filter(self):
        specimenfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        filter =  specimenfilter.getFilterValues()
        if 'Specimen State' not in filter:
            filter['Specimen State'] = u"Pending Draw"
        return filter.iteritems()

    def has_filter(self):
        filter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        filter =  filter.getFilterValues()
        if filter:
            return True
        return False

    @property
    def entry_count(self):
        if not hasattr(self, '_v_crud_form'):
            self._v_crud_form = ClinicalLabViewForm(self.context, self.request)
            self._v_crud_form.update()
        return self._v_crud_form.count

    @property
    def crud_form(self):
        if not hasattr(self, '_v_crud_form'):
            self._v_crud_form = ClinicalLabViewForm(self.context, self.request)
            self._v_crud_form.update()
        return self._v_crud_form
