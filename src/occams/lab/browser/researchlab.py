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

from occams.lab import interfaces
from occams.lab import Session
from occams.lab import model
from occams.lab.browser import labcrud
from occams.lab import MessageFactory as _
from occams.form.traversal import closest
from plone.z3cform import layout

SUCCESS_MESSAGE = _(u"Successfully updated")
PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
NO_CHANGES = _(u"No changes made.")


class AliquotFilterForm(z3c.form.form.Form):
    """
    Specimen Filter form. This form presents itself as an overlay on the Primary
    Clinical Lab view as a way to filter specimen.
    """
    ignoreContext = True
    label = u"Filter Aliquot"
    description = _(u"Please enter filter criteria. You may filter by any or all options. "
                           u" Aliquot are, by default, filtered by state, which depends on your current view. "
                           u"The filter will persist while you are logged in. ")


    # fields = z3c.form.field.Fields(interfaces.IAliquotFilterForm)

    def updateWidgets(self):
        """
        Apply The information in the browser request as values to this form
        """
        z3c.form.form.Form.updateWidgets(self)
        browser_session = ISession(self.request)
        if 'aliquotfilter' in browser_session:
            aliquotfilter = browser_session['aliquotfilter']
            for key, widget in self.widgets.items():
                if key in aliquotfilter:
                    value = aliquotfilter[key]
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
        browser_session['aliquotfilter'] = {}
        for key, value in data.items():
            if value is not None:
                if getattr(value, 'name', False):
                    browser_session['aliquotfilter'][key] = value.name
                else:
                    browser_session['aliquotfilter'][key] = value
        browser_session.save()
        messages.addStatusMessage(_(u"Your Filter has been applied"), type=u'info')
        return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())

    @z3c.form.button.buttonAndHandler(u'Remove Filter')
    def handleClearFilter(self, action):
        browser_session = ISession(self.request)
        browser_session['aliquotfilter'] = {}
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_(u"Your Filter has been cleared"), type=u'info')
        return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())

class ResearchLabEditForm(labcrud.OccamsCrudEditForm):
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
                obj = Session.query(model.Specimen).filter_by(id=id).one()
                obj.state = state
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

class ResearchLabViewForm(crud.CrudForm):
    label = u"Specimen for Processing"
    description = _(u"")

    ignoreContext = True
    batch_size = 10
    addform_factory = crud.NullForm

    @property
    def editform_factory(self):
        return ResearchLabEditForm

    @property
    def view_schema(self):
        fields = z3c.form.field.Fields(interfaces.ISpecimen, mode=z3c.form.interfaces.DISPLAY_MODE).\
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

    def update(self):
        self.update_schema = z3c.form.field.Fields()
        self.query = self._getQuery()
        self.count = self.query.count()
        super(ResearchLabViewForm, self).update()

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
        if getattr(self, '_sqlBatch', None) is None:
            self._sqlBatch = SqlBatch(self.query)
        return self._sqlBatch


    def _getQuery(self):
        if hasattr(self, '_v_query'):
            return self._v_query
        browser_session  = ISession(self.request)
        if 'specimenfilter' in browser_session:
            specimenfilter = browser_session['specimenfilter']
        else:
            specimenfilter = {}
        query = (
            Session.query(model.Specimen)
                .filter(model.Specimen.processing_location.has(name=self.context.location))
            )
        if 'patient' in specimenfilter:
            query = query.join(model.Patient).filter(or_(
                                 model.Patient.our == specimenfilter['patient'],
                                 model.Patient.legacy_number == specimenfilter['patient'],
                                 model.Patient.reference_numbers.any(reference_number = specimenfilter['patient'])
                                 )
                        )
        if 'specimen_type' in specimenfilter:
            query = query.filter(model.Specimen.specimen_type.has(name = specimenfilter['specimen_type']))
        if 'before_date' in specimenfilter:
            if 'after_date' in specimenfilter:
                query = query.filter(model.Specimen.collect_date >= specimenfilter['before_date'])
                query = query.filter(model.Specimen.collect_date <= specimenfilter['after_date'])
            else:
                query = query.filter(model.Specimen.collect_date == specimenfilter['before_date'])
        if specimenfilter.get('show_all', False):
            query = query.join(model.SpecimenState).filter(model.SpecimenState.name.in_(['complete', 'aliquoted', 'cancel-draw']))
        else:
            query = query.filter(model.Specimen.state.has(name = 'complete'))
        query = query.order_by(model.Specimen.id.desc())
        self._v_query = query
        return self._v_query

class ResearchLabView(BrowserView):
    """
    Primary view for a clinical lab object.
    """

    def current_filter(self):
        browser_session = ISession(self.request)
        if 'specimenfilter' in browser_session:
            specimenfilter = browser_session['specimenfilter']
            for name, filter in specimenfilter.iteritems():
                if name in interfaces.ISpecimenFilterForm and name != 'show_all':
                    yield(interfaces.ISpecimenFilterForm[name].title, filter)
            if 'show_all' in specimenfilter and specimenfilter['show_all']:
                yield (u'Specimen State', u'Pending Draw, Complete, Draw Cancelled')
            else:
                yield(u'Specimen State', u'Pending Draw')
        else:
            yield(u'Specimen State', u'Pending Draw')

    def listAliquotTypes(self):
        query = (
            Session.query(model.AliquotType)
            .order_by(model.AliquotType.title.asc())
            )
        for aliquot_type in iter(query):
            url = "%s/%s/%s" %(self.context.absolute_url(), aliquot_type.specimen_type.name, aliquot_type.name)
            yield {'url': url, 'title': aliquot_type.title}

    def getPreview(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        site = closest(self.context, clinical.ISite)
        location = interfaces.ILabLocation(site).lab_location
        query = (
            Session.query(model.Specimen)
                .filter(model.Specimen.location.has(id=location.id))
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
        # location = Session.query(model.Location).filter_by(name=self.context.location).one()
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
                kwargs['state'] = Session.query(model.AliquotState).filter_by(name = 'pending').one()
                kwargs['inventory_date'] = kwargs['store_date']
                # kwargs['location'] = location
                # clean up the dictionary
                for field in ['patient_legacy_number', 'aliquot_type_title', 'cycle_title', 'patient_our']:
                    if field in kwargs.keys():
                        del kwargs[field]
                while count:
                    newAliquot = model.Aliquot(**kwargs)
                    Session.add(newAliquot)
                    count = count -1
                    created = created + 1
                Session.flush()
            if status is no_changes:
                status = success
        if status is success:
            status = _(u"Successfully created %d Aliquot" % created)
        self.status = status

    @z3c.form.button.buttonAndHandler(_('Mark Specimen Complete'), name='aliquoted')
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

class AliquotSpecimenForm(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """
    editform_factory = AliquotSpecimenEditForm
    addform_factory = crud.NullForm

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

    def update(self):
        self.update_schema = self.edit_schema
        self.query = self._getQuery()
        self.count = self.query.count()
        super(AliquotSpecimenForm, self).update()

    @property
    def display_state(self):
        return (u'pending-aliquot', )

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
            if 'thawed_num' in self.update_schema.keys():
                self.update_schema['thawed_num'].widgetFactory = widgets.StorageFieldWidget
        super(crud.CrudForm, self).updateWidgets()

    def _getQuery(self):
        if hasattr(self, '_v_query'):
            return self._v_query
        browser_session  = ISession(self.request)
        if 'specimenfilter' in browser_session:
            specimenfilter = browser_session['specimenfilter']
        else:
            specimenfilter = {}
        query = (
            Session.query(model.Specimen)
                .filter(model.Specimen.processing_location.has(name=self.context.location))
            )
        if 'patient' in specimenfilter:
            query = query.join(model.Patient).filter(or_(
                                 model.Patient.our == specimenfilter['patient'],
                                 model.Patient.legacy_number == specimenfilter['patient'],
                                 model.Patient.reference_numbers.any(reference_number = specimenfilter['patient'])
                                 )
                        )
        if 'specimen_type' in specimenfilter:
            query = query.filter(model.Specimen.specimen_type.has(name = specimenfilter['specimen_type']))
        if 'before_date' in specimenfilter:
            if 'after_date' in specimenfilter:
                query = query.filter(model.Specimen.collect_date >= specimenfilter['before_date'])
                query = query.filter(model.Specimen.collect_date <= specimenfilter['after_date'])
            else:
                query = query.filter(model.Specimen.collect_date == specimenfilter['before_date'])

        query = query.filter(model.Specimen.state.has(name = 'pending-aliquot'))
        query = query.order_by(model.Specimen.id.desc())
        self._v_query = query
        return self._v_query

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
                'location': specimen.processing_location
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
        if 'aliquot_label_queue' in browser_session \
                and 'label_queue' in self.widgets \
                and self.content.id in browser_session['aliquot_label_queue']:
            self.widgets['label_queue'].value = 1

class AliquotPreparedEditForm(labcrud.OccamsCrudEditForm):


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
            if 'aliquot_label_queue' in browser_session:
                label_queue = browser_session['aliquot_label_queue']
            else:
                browser_session['aliquot_label_queue'] = label_queue = set()
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
        self.changeState(action, 'checked-', 'Checked In')
        return self.status

    @z3c.form.button.buttonAndHandler(_('Check out Aliquot'), name='checkout')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-in', 'Checked In')
        browser_session = ISession(self.request)
        return self.status


    @z3c.form.button.buttonAndHandler(_('Delete Unused Aliquot'), name='delete')
    def handleUnusedAliquot(self, action):
        self.saveChanges(action)
        selected = self.selected_items()
        if selected:
            browser_session = ISession(self.request)
            if 'aliquot_label_queue' in browser_session:
                label_queue = browser_session['aliquot_label_queue']
            else:
                browser_session['aliquot_label_queue'] = label_queue = set()
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

class AliquotPreparedForm(crud.CrudForm):
    """
    Primary view for a clinical lab object.
    """
    label = u""
    description = _(u"")

    ignoreContext = True
    editform_factory = AliquotPreparedEditForm
    addform_factory = crud.NullForm
    batch_size = 20

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

    def update(self):
        self.update_schema = self.edit_schema
        self.query = self._getQuery()
        self.count = self.query.count()
        super(AliquotPreparedForm, self).update()

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        if getattr(self, '_sqlBatch', None) is None:
            self._sqlBatch = SqlBatch(self.getQuery())
        return self._sqlBatch

    def link(self, item, field):
        if field == 'patient_our':
            if not hasattr(self, '_v_patient_urls'):
                self._v_patient_urls = {}
            if not self._v_patient_urls.has_key(item.specimen.patient.id):
                try:
                    patient = clinical.IClinicalObject(item.specimen.patient)
                    self._v_patient_urls[item.specimen.patient.id] = '%s/aliquot' % patient.absolute_url()
                except KeyError:
                     self._v_patient_urls[item.specimen.patient.id] = None
            return self._v_patient_urls[item.specimen.patient.id]

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
        if not hasattr(self, '_v_query'):
            query = (
                Session.query(model.Aliquot)
                .join(model.Aliquot.specimen)
                .join(model.Specimen.patient)
                )
            browser_session  = ISession(self.request)
            if 'specimenfilter' in browser_session:
                aliquotfilter = browser_session['specimenfilter']
            else:
                aliquotfilter = {}
            if 'patient' in aliquotfilter:
                query = query.filter(or_(
                                     model.Patient.our == aliquotfilter['patient'],
                                     model.Patient.legacy_number == aliquotfilter['patient'],
                                     model.Patient.reference_numbers.any(reference_number = aliquotfilter['patient'])
                                     )
                            )
            if 'aliquot_type' in aliquotfilter:
                query = query.filter(model.Aliquot.aliquot_type.has(name = aliquotfilter['aliquot_type']))
            if 'after_date' in aliquotfilter:
                if 'before_date' in aliquotfilter:
                    query = query.filter(model.Aliquot.store_date >= aliquotfilter['after_date'])
                    query = query.filter(model.Aliquot.store_date <= aliquotfilter['before_date'])
                else:
                    query = query.filter(model.Aliquot.store_date == aliquotfilter['after_date'])
            if 'freezer' in aliquotfilter:
                query = query.filter(model.Aliquot.freezer == aliquotfilter['freezer'])
            if 'rack' in aliquotfilter:
                query = query.filter(model.Aliquot.rack == aliquotfilter['rack'])
            if 'box' in aliquotfilter:
                query = query.filter(model.Aliquot.box == aliquotfilter['box'])
            query = query.filter(model.Aliquot.state.has(name = 'pending'))
            query = query.order_by(model.Aliquot.id.desc())
            self._v_query = query
        return self._v_query

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
        if 'aliquot_label_queue' in browser_session:
            data, errors = self.extractData()
            if errors:
                self.status = 'Please correct the indicated errors'
                return
            aliquotQ = (
                Session.query(model.Aliquot)
                .join(model.Specimen)
                .filter(model.Aliquot.id.in_(browser_session['aliquot_label_queue']))
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
        browser_session['aliquot_label_queue'] = set()
        browser_session.save()
        messages = IStatusMessage(self.request)
        messages.addStatusMessage(_(u"Your Queue has been cleared"), type=u'info')
        return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())

    @z3c.form.button.buttonAndHandler(u'Cancel')
    def handleClose(self, action):
        pass

class AliquotSpecimenView(BrowserView):
    """
    Primary view for a clinical lab object.
    """
    def current_filter(self):
        browser_session = ISession(self.request)
        if 'specimenfilter' in browser_session:
            specimenfilter = browser_session['specimenfilter']
            for name, filter in specimenfilter.iteritems():
                if name in interfaces.ISpecimenFilterForm and name != 'show_all':
                    yield(interfaces.ISpecimenFilterForm[name].title, filter)
            if 'show_all' in specimenfilter and specimenfilter['show_all']:
                yield (u'Specimen State', u'Pending Aliquot, Complete, Draw Cancelled')
            else:
                yield('Specimen State', 'Pending Aliquot')
        else:
            yield('Specimen State', 'Pending Aliquot')

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
        if 'aliquot_label_queue' in browser_session:
            return len(browser_session['aliquot_label_queue'])
        else:
            return 0

    # @property
    # def aliquot_print_form(self):
    #     if not hasattr(self, '_v_aliquot_print_form'):
    #         self._v_aliquot_print_form = AliquotLabelFormView(self.context, self.request)
    #         self._v_aliquot_print_form.update()
    #     return self._v_aliquot_print_form


