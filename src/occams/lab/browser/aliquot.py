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
from occams.lab.browser import labcrud
import json
from z3c.form.interfaces import DISPLAY_MODE

import z3c.form
from occams.form.traversal import closest


class AliquotEditForm(labcrud.OccamsCrudEditForm):
    label = _(u"Stored Aliquot")

    prefix = 'aliquot'

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

    # @z3c.form.button.buttonAndHandler(_('Print Listing'), name='print')
    # def handleQueue(self, action):
    #     return self.request.response.redirect('%s/%s' % (self.context.context.absolute_url(), 'checklist'))

    @z3c.form.button.buttonAndHandler(_('Edit Aliquot'), name='incorrect')
    def handleInaccurate(self, action):
        self.changeState(action, 'incorrect', 'incorrect')

    @z3c.form.button.buttonAndHandler(_('Mark Missing'), name='missin')
    def handleCheckinAliquot(self, action):
        self.changeState(action, 'missing', 'Missing')
        return self.status

    @z3c.form.button.buttonAndHandler(_('Check Out'), name='checkout')
    def handleCheckout(self, action):
        self.changeState(action, 'pending-checkout', 'Pending Check Out')
        return self.status

class AliquotForm(crud.CrudForm):
    """
    Primary view for a clinical lab object.
    """
    label = u""
    description = _(u"")

    ignoreContext = True
    editform_factory = AliquotEditForm
    addform_factory = crud.NullForm
    batch_size = 20


    @property
    def view_schema(self):
        fields = z3c.form.field.Fields(interfaces.IViewableAliquot).\
            select('aliquot_id',
                     'state_title',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title'
                     )

        fields += z3c.form.field.Fields(interfaces.IAliquot).\
            select(
                     'store_date',
                     'inventory_date',
                     )
        fields += z3c.form.field.Fields(interfaces.IViewableAliquot).\
            select(
                    'location_title',
                     'vol_count',
                     'frb',
                     'thawed_num',
                     )

        fields += z3c.form.field.Fields(interfaces.IAliquot).\
            select( 'special_instruction',
                      'notes',
                     )
        return fields

    def update(self):
        self.query = self._getQuery()
        self.count = self.query.count()
        super(AliquotForm, self).update()

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        if getattr(self, '_sqlBatch', None) is None:
            self._sqlBatch = SqlBatch(self._getQuery())
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

    # def updateWidgets(self):
    #     super(AliquotPreparedForm, self).updateWidgets()
    #     if self.update_schema is not None:
    #         if 'volume' in self.update_schema.keys():
    #             self.update_schema['volume'].widgetFactory = widgets.AmountFieldWidget
    #         if 'cell_amount' in self.update_schema.keys():
    #             self.update_schema['cell_amount'].widgetFactory = widgets.AmountFieldWidget
    #         if 'freezer' in self.update_schema.keys():
    #             self.update_schema['freezer'].widgetFactory = widgets.StorageFieldWidget
    #         if 'rack' in self.update_schema.keys():
    #             self.update_schema['rack'].widgetFactory = widgets.StorageFieldWidget
    #         if 'box' in self.update_schema.keys():
    #             self.update_schema['box'].widgetFactory = widgets.StorageFieldWidget
    #         if 'thawed_num' in self.update_schema.keys():
    #             self.update_schema['thawed_num'].widgetFactory = widgets.StorageFieldWidget


    def _getQuery(self):
        if not hasattr(self, '_v_query'):
            query = (
                Session.query(model.Aliquot)
                .join(model.Aliquot.specimen)
                .join(model.Specimen.patient)
                )
            browser_session  = ISession(self.request)
            if 'aliquotfilter' in browser_session:
                aliquotfilter = browser_session['aliquotfilter']
            else:
                aliquotfilter = {}
            query = query.filter(model.Aliquot.aliquot_type.has(id = self.context.item.id))
            if 'patient' in aliquotfilter:
                query = query.filter(or_(
                                     model.Patient.our == aliquotfilter['patient'],
                                     model.Patient.legacy_number == aliquotfilter['patient'],
                                     model.Patient.reference_numbers.any(reference_number = aliquotfilter['patient'])
                                     )
                            )
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
            if "show_all" not in aliquotfilter or not aliquotfilter['show_all']:
                query = query.filter(model.Aliquot.state.has(name = 'checked-in'))
            query = query.order_by(model.Aliquot.id.desc())
            self._v_query = query
        return self._v_query



class AliquotView(BrowserView):
    """
    View of a specimen type. Allows editing of
    """

    def listAliquotTypes(self):
        query = (
            Session.query(model.AliquotType)
            .order_by(model.AliquotType.title.asc())
            )
        for aliquot_type in iter(query):
            url = "%s/%s/%s" %(closest(self.context, interfaces.ILab).absolute_url(), aliquot_type.specimen_type.name, aliquot_type.name)
            yield {'url': url, 'title': aliquot_type.title}


    def current_filter(self):
        browser_session = ISession(self.request)
        if 'aliquotfilter' in browser_session:
            aliquotfilter = browser_session['aliquotfilter']
            for name, filter in aliquotfilter.iteritems():
                if name in interfaces.IAliquotFilterForm and name != 'show_all':
                    yield(interfaces.IAliquotFilterForm[name].title, filter)
            if 'show_all' in aliquotfilter and aliquotfilter['show_all']:
                yield (u'Aliquot State', u'Checked In, Checked Out, Missing')
            else:
                yield('Aliquot State', 'Checked In')
        else:
            yield('Aliquot State', 'Checked In')

    @property
    def aliquot_entry_count(self):
        browser_session = ISession(self.request)
        filter = False
        if 'aliquotfilter' in browser_session:
            aliquotfilter = browser_session['aliquotfilter']
            for name, filter in aliquotfilter.iteritems():
                if name in interfaces.IAliquotFilterForm and name != 'show_all':
                    filter = True
                    break
        if not filter:
            return None
        if not hasattr(self, '_v_aliquot_crud_form'):
            self._v_aliquot_crud_form = AliquotForm(self.context, self.request)
            self._v_aliquot_crud_form.update()
        return self._v_aliquot_crud_form.count

    @property
    def aliquot_crud_form(self):
        if not hasattr(self, '_v_aliquot_crud_form'):
            self._v_aliquot_crud_form = AliquotForm(self.context, self.request)
            self._v_aliquot_crud_form.update()
        return self._v_aliquot_crud_form




class EditAliquotForm(crud.CrudForm):
    """
    Primary view for a clinical lab object.
    """
    label = u""
    description = _(u"")

    ignoreContext = True
    editform_factory = AliquotEditForm
    addform_factory = crud.NullForm
    batch_size = 20


    @property
    def edit_schema(self):
        fields = z3c.form.field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('aliquot_id',
                     'state_title',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title'
                     )

        fields += z3c.form.field.Fields(interfaces.IAliquot).\
            select('volume',
                   'cell_amount',
                   'store_date',
                   'freezer',
                   'rack',
                   'box',
                   'inventory_date',
                   'location',
                   'storage_location',
                   'notes',
                   'special_instruction',
                   'thawed_num',
                   'sent_date',
                   'sent_name',
                   'sent_notes',)
        #.\
        #     select(
        #              'store_date',
        #              'inventory_date',
        #              )
        # fields += z3c.form.field.Fields(interfaces.IViewableAliquot).\
        #     select(
        #             'location_title',
        #              'vol_count',
        #              'frb',
        #              'thawed_num',
        #              )

        # fields += z3c.form.field.Fields(interfaces.IAliquot).\
        #     select( 'special_instruction',
        #               'notes',
        #              )
        return fields

    def update(self):
        self.update_schema = self.edit_schema
        self.query = self._getQuery()
        self.count = self.query.count()
        super(EditAliquotForm, self).update()

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        if getattr(self, '_sqlBatch', None) is None:
            self._sqlBatch = SqlBatch(self._getQuery())
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
        super(EditAliquotForm, self).updateWidgets()
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
            if 'aliquotfilter' in browser_session:
                aliquotfilter = browser_session['aliquotfilter']
            else:
                aliquotfilter = {}
            query = query.filter(model.Aliquot.aliquot_type.has(id = self.context.item.id))
            if 'patient' in aliquotfilter:
                query = query.filter(or_(
                                     model.Patient.our == aliquotfilter['patient'],
                                     model.Patient.legacy_number == aliquotfilter['patient'],
                                     model.Patient.reference_numbers.any(reference_number = aliquotfilter['patient'])
                                     )
                            )
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
            if "show_all" not in aliquotfilter or not aliquotfilter['show_all']:
                query = query.filter(model.Aliquot.state.has(name = 'checked-in'))
            query = query.order_by(model.Aliquot.id.desc())
            self._v_query = query
        return self._v_query


class EditAliquotView(BrowserView):
    """
    View of a specimen type. Allows editing of
    """

    def listAliquotTypes(self):
        query = (
            Session.query(model.AliquotType)
            .order_by(model.AliquotType.title.asc())
            )
        for aliquot_type in iter(query):
            url = "%s/%s/%s" %(closest(self.context, interfaces.ILab).absolute_url(), aliquot_type.specimen_type.name, aliquot_type.name)
            yield {'url': url, 'title': aliquot_type.title}


    def current_filter(self):
        browser_session = ISession(self.request)
        if 'aliquotfilter' in browser_session:
            aliquotfilter = browser_session['aliquotfilter']
            for name, filter in aliquotfilter.iteritems():
                if name in interfaces.IAliquotFilterForm and name != 'show_all':
                    yield(interfaces.IAliquotFilterForm[name].title, filter)
            if 'show_all' in aliquotfilter and aliquotfilter['show_all']:
                yield (u'Aliquot State', u'Checked In, Checked Out, Missing')
            else:
                yield('Aliquot State', 'Checked In')
        else:
            yield('Aliquot State', 'Checked In')

    @property
    def aliquot_entry_count(self):
        return 4
        browser_session = ISession(self.request)
        filter = False
        if 'aliquotfilter' in browser_session:
            aliquotfilter = browser_session['aliquotfilter']
            for name, filter in aliquotfilter.iteritems():
                if name in interfaces.IAliquotFilterForm and name != 'show_all':
                    filter = True
                    break
        if not filter:
            return None
        if not hasattr(self, '_v_aliquot_crud_form'):
            self._v_aliquot_crud_form = EditAliquotForm(self.context, self.request)
            self._v_aliquot_crud_form.update()
        return self._v_aliquot_crud_form.count

    @property
    def aliquot_crud_form(self):
        if not hasattr(self, '_v_aliquot_crud_form'):
            self._v_aliquot_crud_form = EditAliquotForm(self.context, self.request)
            self._v_aliquot_crud_form.update()
        return self._v_aliquot_crud_form
