from Products.Five.browser import BrowserView
from collective.beaker.interfaces import ISession
import z3c.form
import datetime
from beast.browser import widgets
from sqlalchemy import or_
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form.interfaces import DISPLAY_MODE

from plone.z3cform.crud import crud
from occams.datastore.batch import SqlBatch
from avrc.aeh import interfaces as clinical
import os
from occams.form.traversal import closest
from beast.browser.crud import BatchNavigation

from occams.lab import interfaces
from occams.lab import Session
from occams.lab import model
from occams.lab.browser import common
from occams.lab import MessageFactory as _
from occams.form.traversal import closest
from plone.z3cform import layout
import zope.component
from occams.lab import FILTER_KEY

SUCCESS_MESSAGE = _(u"Successfully updated")
PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
NO_CHANGES = _(u"No changes made.")

ALIQUOT_LABEL_QUEUE = 'aliquot_label_queue'

class AliquotFilterForm(common.LabFilterForm):
    """
    Specimen Filter form. This form presents itself as an overlay on the Primary
    Clinical Lab view as a way to filter specimen.
    """
    label = u"Filter Aliquot"

    @property
    def fields(self):
        aliquotfilter =  zope.component.getMultiAdapter((self.context, self.request), interfaces.IAliquotFilter)
        return aliquotfilter.getFilterFields(omitable=["show_all"])


class EmbeddedAliquotFilterForm(common.LabFilterForm):
    """
    Specimen Filter form. This form presents itself as an overlay on the Primary
    Clinical Lab view as a way to filter specimen.
    """
    label = u"Filter Aliquot"

    @property
    def fields(self):
        aliquotfilter =  zope.component.getMultiAdapter((self.context, self.request), interfaces.IAliquotFilter)
        return aliquotfilter.getFilterFields(omitable=["freezer", "rack", "box", "show_all"])

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
        browser_session[FILTER_KEY] = {}
        for key, value in data.items():
            if value is not None:
                if getattr(value, 'name', False):
                    browser_session[FILTER_KEY][key] = value.name
                else:
                    browser_session[FILTER_KEY][key] = value
        browser_session.save()
        messages.addStatusMessage(_(u"Your Filter has been applied"), type=u'info')
        return self.request.response.redirect("%s" % self.action)

AliquotFilterFormView = layout.wrap_form(EmbeddedAliquotFilterForm)


class ResearchLabEditForm(common.OccamsCrudEditForm):
    label = _(u"Specimen to be processed")

    @z3c.form.button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

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
                #obj = Session.query(model.Specimen).filter_by(id=id).one()
                data.state = state
            Session.flush()
            self._update_subforms()
            self.status = _(u"%d Specimen have been changed to the status of %s." % (number_specimen, acttitle))
            # messages.addStatusMessage(status, type=u'info')
        else:
            self.status = _(u"Please select Specimen")
            # messages.addStatusMessage(status, type=u'error')

    @z3c.form.button.buttonAndHandler(_('Ready selected'), name='ready')
    def handleCompleteDraw(self, action):
        self.changeState(action, 'pending-aliquot', 'ready')
        return self.status

    @z3c.form.button.buttonAndHandler(_('Mark Selected Cancelled'), name='cancel-draw')
    def handleCancelDraw(self, action):
        """
        Mark the selected specimen as cancelled. This is used for reporting purposes
        """
        self.saveChanges(action)
        self.changeState(action, 'cancel-draw', 'canceled')
        return self.status

class ResearchLabViewForm(common.OccamsCrudForm):
    label = u"Specimen for Processing"

    batch_size = 10

    editform_factory = ResearchLabEditForm

    edit_schema = z3c.form.field.Fields()
    @property
    def view_schema(self):
        fields = z3c.form.field.Fields(interfaces.ISpecimen).\
                    select('state',
                            )
        fields += z3c.form.field.Fields(interfaces.IViewableSpecimen).\
            select('patient_our',
             'cycle_title',
             'tube_type',
             )
        fields += z3c.form.field.Fields(interfaces.ISpecimen).\
            select('specimen_type',
             'tubes',
             'collect_date',
             'collect_time',
             'notes')
        return fields

    def _getQuery(self):
        # multiadapter defined in filters.py
        specimenfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        query =  specimenfilter.getQuery(default_state='complete')
        return query

class ResearchLabView(BrowserView):
    """
    Primary view for a clinical lab object.
    """
    def listAliquotTypes(self):
        query = (
            Session.query(model.AliquotType)
            .order_by(model.AliquotType.title.asc())
            )
        for aliquot_type in iter(query):
            url = "%s/%s/%s" %(self.context.absolute_url(), aliquot_type.specimen_type.name, aliquot_type.name)
            yield {'url': url, 'title': aliquot_type.title}

    def current_filter(self):
        specimenfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        filter =  specimenfilter.getFilterValues()
        if 'Specimen State' not in filter:
            filter['Specimen State'] = u"Ready Aliquot"
        return filter.iteritems()


    def getPreview(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        site = closest(self.context, clinical.ISite)
        location = interfaces.ILabLocation(site).lab_location
        query = (
            Session.query(model.Specimen)
                .filter(or_(
                    model.Specimen.location.has(id=location.id),
                    model.Specimen.previous_location.has(id=location.id),
                    ))
                .filter(model.Specimen.state.has(name = u'pending-draw',))
                .filter(model.Specimen.collect_date <= datetime.date.today())
                .order_by(model.Specimen.id.desc())
            )
        for entry in iter(query):
            yield entry

    @property
    def entry_count(self):
        if not hasattr(self, '_v_crud_form'):
            self._v_crud_form = ResearchLabViewForm(self.context, self.request)
            self._v_crud_form.update()
        return self._v_crud_form.count

    @property
    def crudForm(self):
        if not hasattr(self, '_v_crud_form'):
            self._v_crud_form = ResearchLabViewForm(self.context, self.request)
            self._v_crud_form.update()
        return self._v_crud_form

class AliquotSpecimenEditForm(crud.EditForm):
    """
    """
    label = _(u"Specimen to Aliquot Templates")
    prefix = 'aliquot-creator'

    def render_batch_navigation(self):
        """
        Render the batch navigation to include the default styles for Plone
        """
        navigation = BatchNavigation(self.batch, self.request)
        def make_link(page):
            return "%s?%spage=%s" % (self.request.getURL(), self.prefix, page)
        navigation.make_link = make_link
        return navigation()


    @z3c.form.button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @z3c.form.button.buttonAndHandler(_('Create Aliquot'), name='aliquot')
    def handleCreateAliquot(self, action):
        """
        """
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Aliquot.")
            return
        success = _(u"Successfully Aliquoted")
        partly_success = _(u"Some Aliquot could not be created.")
        status = no_changes = _(u"No Aliquot created.")
        created = 0
        state = Session.query(model.AliquotState).filter_by(name = 'pending').one()
        location = Session.query(model.Location).filter_by(name = self.context.context.location).one()
        for subform in self.subforms:
            data, errors = subform.extractData()
            if not data['select'] or not data['count']:
                continue
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            count = data.pop('count')
            del data['select']
            changes = subform.applyChanges(data)
            if changes:
                kwargs = subform.content
                kwargs['state'] = state
                kwargs['location'] = location
                kwargs['previous_location'] = location
                kwargs['inventory_date'] = kwargs['store_date']
                # clean up the dictionary
                for field in ['patient_legacy_number', 'aliquot_type_title', 'cycle_title', 'patient_our']:
                    if field in kwargs.keys():
                        del kwargs[field]
                while count:
                    newAliquot = model.Aliquot(**kwargs)
                    Session.add(newAliquot)
                    count = count -1
                    created = created + 1
            if status is no_changes:
                status = success
        Session.flush()
        if status is success:
            status = _(u"Successfully created %d Aliquot" % created)
        self.status = status

    @z3c.form.button.buttonAndHandler(_('Mark Specimen Aliquoted'), name='aliquoted')
    def handleCompleteSpecimen(self, action):
        selected = self.selected_items()
        state = Session.query(model.SpecimenState).filter_by(name='aliquoted').one()
        if selected:
            for id, aliquottemplate in selected:
                aliquottemplate['specimen'].state =state
            Session.flush()
            self._update_subforms()
            self.status = _(u"Your specimen have been marked as aliquoted")
        else:
            self.status = _(u"Please select aliquot templates to complete")
        self.request.response.redirect(self.request.URL)

class AliquotSpecimenForm(common.OccamsCrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """
    batch_size = 10

    editform_factory = AliquotSpecimenEditForm

    @property
    def edit_schema(self):
        fields = z3c.form.field.Fields(interfaces.IAliquotGenerator).\
        select('count')
        fields += z3c.form.field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title'
                     )
        fields += z3c.form.field.Fields(interfaces.IAliquot).\
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
        pass

    def updateWidgets(self):
        self.update_schema['count'].widgetFactory = widgets.StorageFieldWidget
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
        super(crud.CrudForm, self).updateWidgets()

    def _getQuery(self):
        # multiadapter defined in filters.py
        specimenfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        return specimenfilter.getQuery(default_state='pending-aliquot', omitable=['show_all'])

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        if getattr(self, '_v_aliquotList', False):
            return self._v_aliquotList
        self._v_aliquotList = []
        i = 0
        for specimen in iter(self.query):
            types = Session.query(model.AliquotType).filter(model.AliquotType.specimen_type == specimen.specimen_type).order_by(model.AliquotType.id)
            viewableSpecimen = interfaces.IViewableSpecimen(specimen)
            for aliquotType in types:
                newAliquot = {
                'patient_our':viewableSpecimen.patient_our,
                'patient_legacy_number':specimen.patient.legacy_number,
                'cycle_title': viewableSpecimen.cycle_title,
                'specimen':specimen,
                'aliquot_type':aliquotType,
                'aliquot_type_title':aliquotType.title,
                'store_date':datetime.date.today(),
                'location': specimen.location,
                'previous_location': specimen.location
                }
                self._v_aliquotList.append((i, newAliquot))
                i = i + 1
        return self._v_aliquotList

class AliquotPreparedSubForm(crud.EditSubForm):
    """
    Individual row sub forms for the specimen crud form.
    """
    def updateWidgets(self):
        """
        Set the default processing location based on the property of the Clinical Lab of that same name
        """
        super(AliquotPreparedSubForm, self).updateWidgets()
        browser_session = ISession(self.request)
        if ALIQUOT_LABEL_QUEUE in browser_session \
                and 'label_queue' in self.widgets \
                and self.content.id in browser_session['aliquot_label_queue']:
            self.widgets['label_queue'].value = 1

class AliquotPreparedEditForm(common.OccamsCrudEditForm):


    label = _(u"Aliquot to be processed")

    prefix = 'aliquot-prepared'

    editsubform_factory = AliquotPreparedSubForm

    def changeState(self, action, state, acttitle):
        """
        Using the passed state, change the selected items to that state
        """
        selected = self.selected_items()
        # messages = IStatusMessage(self.request)
        if selected:
            number_aliquot = len(selected)
            state = Session.query(model.AliquotState).filter_by(name=state).one()
            for id, data in selected:
                obj = Session.query(model.Aliquot).filter_by(id=id).one()
                obj.state = state
            Session.flush()
            self._update_subforms()
            self.status = _(u"%d Aliquot have been changed to the status of %s." % (number_aliquot, acttitle))
        else:
            self.status = _(u"Please select Aliquot")


    @z3c.form.button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @z3c.form.button.buttonAndHandler(_('Toggle Print Queue'), name='print')
    def handlePrintAliquot(self, action):
        self.saveChanges(action)
        selected = self.selected_items()
        if selected:
            browser_session = ISession(self.request)
            if ALIQUOT_LABEL_QUEUE in browser_session:
                label_queue = browser_session[ALIQUOT_LABEL_QUEUE]
            else:
                browser_session[ALIQUOT_LABEL_QUEUE] = label_queue = set()
            alquot_number = len(selected)
            for id, data in selected:
                if id in label_queue:
                    label_queue.discard(id)
                else:
                    label_queue.add(id)
            browser_session.save()
            self._update_subforms()
            self.status = _(u"%d Aliquot have been added to the print queue." % (alquot_number))
        else:
            self.status = _(u"Please select Aliquot")
        return self.status

    @z3c.form.button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        return self.status

    @z3c.form.button.buttonAndHandler(_('Check In Aliquot'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-in', 'Checked In')
        return self.status

    @z3c.form.button.buttonAndHandler(_('Check out Aliquot'), name='checkout')
    def handleCheckoutAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'pending-checkout', 'Pending Check Out')
        return self.status

    @z3c.form.button.buttonAndHandler(_('Delete Unused Aliquot'), name='delete')
    def handleUnusedAliquot(self, action):
        self.saveChanges(action)
        selected = self.selected_items()
        if selected:
            browser_session = ISession(self.request)
            if ALIQUOT_LABEL_QUEUE in browser_session:
                label_queue = browser_session[ALIQUOT_LABEL_QUEUE]
            else:
                browser_session[ALIQUOT_LABEL_QUEUE] = label_queue = set()
            alquot_number = len(selected)
            for id, data in selected:
                aliquot = Session.query(model.Aliquot).filter_by(id=id).one()
                Session.delete(aliquot)
                label_queue.discard(id)
            browser_session.save()
            Session.flush()
            self._update_subforms()
            self.status = _(u"%d Aliquot have been deleted." % (alquot_number))
        else:
            self.status = _(u"Please select Aliquot")
        return self.status

class AliquotPreparedForm(common.OccamsCrudForm):
    """
    Primary view for a clinical lab object.
    """
    label = u""
    description = _(u"")

    editform_factory = AliquotPreparedEditForm

    @property
    def edit_schema(self):
        fields = z3c.form.field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('aliquot_id',
                      'label_queue',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title'
                     )
        fields += z3c.form.field.Fields(interfaces.IAliquot).\
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

    def updateWidgets(self):
        super(AliquotPreparedForm, self).updateWidgets()
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

    def _getQuery(self):
        aliquotfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
        return aliquotfilter.getQuery(default_state='pending')

class AliquotSpecimenView(BrowserView):
    """
    Primary view for a clinical lab object.
    """
    def current_filter(self):
        specimenfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        filter =  specimenfilter.getFilterValues()
        return filter.iteritems()

    def listAliquotTypes(self):
        query = (
            Session.query(model.AliquotType)
            .order_by(model.AliquotType.title.asc())
            )
        for aliquot_type in iter(query):
            url = "%s/%s/%s" %(closest(self.context, interfaces.ILab).absolute_url(), aliquot_type.specimen_type.name, aliquot_type.name)
            yield {'url': url, 'title': aliquot_type.title}

    @property
    def specimen_entry_count(self):
        if not hasattr(self, '_v_specimen_crud_form'):
            self._v_specimen_crud_form = AliquotSpecimenForm(self.context, self.request)
            self._v_specimen_crud_form.update()
        return self._v_specimen_crud_form.count

    @property
    def specimen_crud_form(self):
        if not hasattr(self, '_v_specimen_crud_form'):
            self._v_specimen_crud_form = AliquotSpecimenForm(self.context, self.request)
            self._v_specimen_crud_form.update()
        return self._v_specimen_crud_form

    @property
    def aliquot_entry_count(self):
        if not hasattr(self, '_v_aliquot_crud_form'):
            self._v_aliquot_crud_form = AliquotPreparedForm(self.context, self.request)
            self._v_aliquot_crud_form.update()
        return self._v_aliquot_crud_form.count

    @property
    def aliquot_crud_form(self):
        if not hasattr(self, '_v_aliquot_crud_form'):
            self._v_aliquot_crud_form = AliquotPreparedForm(self.context, self.request)
            self._v_aliquot_crud_form.update()
        return self._v_aliquot_crud_form

    @property
    def print_queue(self):
        browser_session = ISession(self.request)
        if ALIQUOT_LABEL_QUEUE in browser_session:
            return len(browser_session[ALIQUOT_LABEL_QUEUE])
        else:
            return 0

class AliquotLabelForm(z3c.form.form.Form):
    """
    Specimen Filter form. This form presents itself as an overlay on the Primary
    Clinical Lab view as a way to filter specimen.
    """
    # label = u"Label Aliquot"
    description = _(u"Please enter the starting column and row for a partially used. ")

    @property
    def label(self):
        browser_session = ISession(self.request)
        if 'aliquot_label_queue' in browser_session:
            label_length = len(browser_session['aliquot_label_queue'])
        else:
            label_length = 0
        return u"Print Aliquot Labels for %d Aliquot" % label_length

    fields = z3c.form.field.Fields(interfaces.ILabelPrinter)

    @z3c.form.button.buttonAndHandler(_('Print Aliquot Labels'), name='print')
    def handlePrintAliquot(self, action):

        browser_session = ISession(self.request)
        if ALIQUOT_LABEL_QUEUE in browser_session:
            data, errors = self.extractData()
            if errors:
                self.status = 'Please correct the indicated errors'
                return
            aliquotQ = (
                Session.query(model.Aliquot)
                .join(model.Specimen)
                .filter(model.Aliquot.id.in_(browser_session[ALIQUOT_LABEL_QUEUE]))
                .order_by(model.Specimen.patient_id, model.Aliquot.aliquot_type_id, model.Aliquot.id)
                )

            content = interfaces.ILabelPrinter(self.context).printLabelSheet(aliquotQ.all(), data['startcol'], data['startrow'])

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
        browser_session[ALIQUOT_LABEL_QUEUE] = set()
        browser_session.save()
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_(u"Your Queue has been cleared"), type=u'info')
        return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())

    @z3c.form.button.buttonAndHandler(u'Close')
    def handleClose(self, action):
        pass

class AliquotCheckoutEditForm(common.OccamsCrudEditForm):


    label = _(u"Aliquot to be Checked Out")

    prefix = 'aliquot-checkout'

    # editsubform_factory = AliquotPreparedSubForm

    def changeState(self, action, state, acttitle):
        """
        Using the passed state, change the selected items to that state
        """
        selected = self.selected_items()
        # messages = IStatusMessage(self.request)
        if selected:
            number_aliquot = len(selected)
            state = Session.query(model.AliquotState).filter_by(name=state).one()
            for id, data in selected:
                obj = Session.query(model.Aliquot).filter_by(id=id).one()
                obj.state = state
            Session.flush()
            self._update_subforms()
            self.status = _(u"%d Aliquot have been changed to the status of %s." % (number_aliquot, acttitle))
        else:
            self.status = _(u"Please select Aliquot")


    @z3c.form.button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @z3c.form.button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        return self.status

    @z3c.form.button.buttonAndHandler(_('Return Aliquot'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-in', 'Checked In')
        return self.status

    @z3c.form.button.buttonAndHandler(_('Complete Checkout'), name='checkout')
    def handleCheckoutAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-out', 'Checked Out')
        return self.status

class AliquotCheckoutForm(common.OccamsCrudForm):
    """
    Primary view for a clinical lab object.
    """
    label = u""
    description = _(u"")

    editform_factory = AliquotCheckoutEditForm

    @property
    def edit_schema(self):
        fields = z3c.form.field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('aliquot_id',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title',
                     'vol_count',
                     'frb',
                     )
        fields += z3c.form.field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select('store_date',
                     'special_instruction',
                     'notes')

        fields += z3c.form.field.Fields(interfaces.IAliquot).\
            select(
                   'location',
                   'sent_date',
                   'sent_name',
                   'sent_notes',)

        return fields

    def _getQuery(self):
        aliquotfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
        return aliquotfilter.getQuery(default_state='pending-checkout')

class AliquotCheckoutView(BrowserView):
    """
    Primary view for a clinical lab object.
    """
    def current_filter(self):
        aliquotfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
        filter =  aliquotfilter.getFilterValues()
        return filter.iteritems()

    def listAliquotTypes(self):
        query = (
            Session.query(model.AliquotType)
            .order_by(model.AliquotType.title.asc())
            )
        for aliquot_type in iter(query):
            url = "%s/%s/%s" %(closest(self.context, interfaces.ILab).absolute_url(), aliquot_type.specimen_type.name, aliquot_type.name)
            yield {'url': url, 'title': aliquot_type.title}

    @property
    def aliquot_entry_count(self):
        if not hasattr(self, '_v_aliquot_crud_form'):
            self._v_aliquot_crud_form = AliquotCheckoutForm(self.context, self.request)
            self._v_aliquot_crud_form.update()
        return self._v_aliquot_crud_form.count

    @property
    def aliquot_crud_form(self):
        if not hasattr(self, '_v_aliquot_crud_form'):
            self._v_aliquot_crud_form = AliquotCheckoutForm(self.context, self.request)
            self._v_aliquot_crud_form.update()
        return self._v_aliquot_crud_form

class AliquotBatchCheckoutForm(z3c.form.form.Form):
    """
    Specimen Filter form. This form presents itself as an overlay on the Primary
    Clinical Lab view as a way to filter specimen.
    """
    description = _(u"")
    ignoreContext=True
    @property
    def label(self):
        return u"Bulk Update %d Aliquot" % self._getQuery().count()

    fields = z3c.form.field.Fields(interfaces.IAliquotCheckout)

    def _getQuery(self):
        aliquotfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
        return aliquotfilter.getQuery(default_state='pending-checkout')

    @z3c.form.button.buttonAndHandler(_('Update ALiquot'), name='update')
    def handleUpdateAliquot(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = 'Please correct the indicated errors'
            return
        query = self._getQuery()
        for aliquot in iter(query):
            for key, value in data.iteritems():
                if value:
                    setattr(aliquot, key, value)
        Session.flush()
        return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())

    @z3c.form.button.buttonAndHandler(u'Close')
    def handleClose(self, action):
        pass

class AliquotReciept(BrowserView):
    """
    """

    def _getQuery(self):
        aliquotfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
        return aliquotfilter.getQuery(default_state='pending-checkout')

    def getQueueItems(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        for aliquot in iter(self._getQuery()):
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







class AliquotCheckInEditForm(common.OccamsCrudEditForm):


    label = _(u"Aliquot to be Checked In")

    prefix = 'aliquot-checkin'

    # editsubform_factory = AliquotPreparedSubForm

    def changeState(self, action, state, acttitle):
        """
        Using the passed state, change the selected items to that state
        """
        selected = self.selected_items()
        # messages = IStatusMessage(self.request)
        if selected:
            number_aliquot = len(selected)
            state = Session.query(model.AliquotState).filter_by(name=state).one()
            for id, data in selected:
                obj = Session.query(model.Aliquot).filter_by(id=id).one()
                obj.state = state
            Session.flush()
            self._update_subforms()
            self.status = _(u"%d Aliquot have been changed to the status of %s." % (number_aliquot, acttitle))
        else:
            self.status = _(u"Please select Aliquot")


    @z3c.form.button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @z3c.form.button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        return self.status

    @z3c.form.button.buttonAndHandler(_('Check In Aliquot'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-in', 'Checked In')
        return self.status

class AliquotCheckInForm(common.OccamsCrudForm):
    """
    Primary view for a clinical lab object.
    """
    label = u""
    description = _(u"")

    editform_factory = AliquotCheckInEditForm

    @property
    def edit_schema(self):
        fields = z3c.form.field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('aliquot_id',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title',
                     )
        fields += z3c.form.field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select('store_date',
                     'special_instruction',
                    )
        fields += z3c.form.field.Fields(interfaces.IAliquot).\
            select(
                   'freezer',
                   'rack',
                   'box',
                   'thawed_num',
                   'location',
                   'notes')
        fields += z3c.form.field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select(
                   'sent_date',
                   'sent_name',
                   'sent_notes',)

        return fields

    def updateWidgets(self):
        super(AliquotCheckInForm, self).updateWidgets()
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


    def _getQuery(self):
        aliquotfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
        return aliquotfilter.getQuery(default_state='checked-out')





class AliquotCheckInView(BrowserView):
    """
    Primary view for a clinical lab object.
    """

    def current_filter(self):
        aliquotfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
        filter =  aliquotfilter.getFilterValues()
        if 'Aliquot State' not in filter:
            filter['Aliquot State'] = u"Checked Out"
        return filter.iteritems()

    def has_filter(self):
        aliquotfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
        filter =  aliquotfilter.getFilterValues()
        if filter:
            return True
        return False

    def listAliquotTypes(self):
        query = (
            Session.query(model.AliquotType)
            .order_by(model.AliquotType.title.asc())
            )
        for aliquot_type in iter(query):
            url = "%s/%s/%s" %(closest(self.context, interfaces.ILab).absolute_url(), aliquot_type.specimen_type.name, aliquot_type.name)
            yield {'url': url, 'title': aliquot_type.title}

    @property
    def aliquot_entry_count(self):
        if not hasattr(self, '_v_aliquot_crud_form'):
            self._v_aliquot_crud_form = AliquotCheckInForm(self.context, self.request)
            self._v_aliquot_crud_form.update()
        return self._v_aliquot_crud_form.count

    @property
    def aliquot_crud_form(self):
        if not hasattr(self, '_v_aliquot_crud_form'):
            self._v_aliquot_crud_form = AliquotCheckInForm(self.context, self.request)
            self._v_aliquot_crud_form.update()
        return self._v_aliquot_crud_form

    @property
    def aliquot_filter_form(self):
        if not hasattr(self, '_v_aliquot_filter_form'):
            self._v_aliquot_filter_form = AliquotFilterFormView(self.context, self.request)
            self._v_aliquot_filter_form.update()
        return self._v_aliquot_filter_form
