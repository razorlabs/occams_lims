from Products.Five.browser import BrowserView
from collective.beaker.interfaces import ISession
import z3c.form
import datetime
from beast.browser import widgets
from Products.statusmessages.interfaces import IStatusMessage
from plone.z3cform.crud import crud
from plone.z3cform import layout
from occams.lab import interfaces
from occams.lab import Session
from occams.lab import model
from occams.lab import MessageFactory as _
from occams.lab.browser import common
from z3c.form.interfaces import DISPLAY_MODE, INPUT_MODE
import zope.component
from occams.form.traversal import closest
from occams.lab import FILTER_KEY

EDIT_ALIQUOT_KEY = "occams.lab.editaliquot"

class AliquotFilterForm(common.LabFilterForm):
    """
    Specimen Filter form. This form presents itself as an overlay on the Primary
    Clinical Lab view as a way to filter specimen.
    """
    label = u"Filter Aliquot"

    @property
    def fields(self):
        aliquotfilter =  zope.component.getMultiAdapter((self.context, self.request), interfaces.IAliquotFilter)
        return aliquotfilter.getFilterFields(omitable=['aliquot_type',])

class EmbeddedAliquotFilterForm(common.LabFilterForm):
    """
    Specimen Filter form. This form presents itself as an overlay on the Primary
    Clinical Lab view as a way to filter specimen.
    """
    label = u"Filter Aliquot"

    @property
    def fields(self):
        aliquotfilter =  zope.component.getMultiAdapter((self.context, self.request), interfaces.IAliquotFilter)
        return aliquotfilter.getFilterFields(omitable=['aliquot_type',])

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

class EditAliquotSubForm(crud.EditSubForm):
    """
    Individual row sub forms for the specimen crud form.
    """

    @property
    def fields(self):
        browser_session = ISession(self.request)
        if EDIT_ALIQUOT_KEY not in browser_session:
            browser_session[EDIT_ALIQUOT_KEY] = set()
        fields = z3c.form.field.Fields(self._select_field())
        crud_form = self.context.context
        view_schema = crud_form.view_schema
        if view_schema is not None:
            view_fields = z3c.form.field.Fields(view_schema)
            for f in view_fields.values():
                f.mode = DISPLAY_MODE
                # This is to allow a field to appear in both view
                # and edit mode at the same time:
                if not f.__name__.startswith('view_'):
                    f.__name__ = 'view_' + f.__name__
            fields += view_fields
        update_schema = crud_form.update_schema
        if update_schema is not None:
            update_fields =  z3c.form.field.Fields(update_schema)
            if self.content.id in browser_session[EDIT_ALIQUOT_KEY]:
                for f in update_fields.values():
                    f.mode = INPUT_MODE
            else:
                for f in update_fields.values():
                    f.mode = DISPLAY_MODE
            fields += update_fields
        return fields

    def updateWidgets(self):
        """
        Set the default processing location based on the property of the Clinical Lab of that same name
        """
        super(EditAliquotSubForm, self).updateWidgets()
        if 'inventory_date' in self.widgets and self.widgets['inventory_date'].value == ('','','') and self.widgets['inventory_date'].mode == INPUT_MODE:
            today = datetime.date.today()
            self.widgets['inventory_date'].value = (today.year, today.month, today.day)


class EditAliquotEditForm(common.OccamsCrudEditForm):
    @property
    def label(self):
        return _(u"Editable %s" % self.context.context.item.title)

    editsubform_factory = EditAliquotSubForm

    prefix = 'edit-aliquot'

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

    @z3c.form.button.buttonAndHandler(_('Edit Aliquot'), name='incorrect')
    def handleInaccurate(self, action):
        browser_session = ISession(self.request)
        if EDIT_ALIQUOT_KEY not in browser_session:
            browser_session[EDIT_ALIQUOT_KEY] = set()
        selected = self.selected_items()
        if selected:
            number_aliquot = len(selected)
            for id, data in selected:
                browser_session[EDIT_ALIQUOT_KEY].add(id)
            self.status = _(u"%d Aliquot have been added to the edit queue." % (number_aliquot))
        else:
            self.status = _(u"Please select Aliquot")
        browser_session.save()
        self._update_subforms()


    @z3c.form.button.buttonAndHandler(_('Save All Changes'), name='updated')
    def handleUpdate(self, action):
        self.saveChanges(action)
        browser_session = ISession(self.request)
        if EDIT_ALIQUOT_KEY not in browser_session:
            browser_session[EDIT_ALIQUOT_KEY] = set()
        for subform in self.subforms:
            browser_session[EDIT_ALIQUOT_KEY].discard(subform.content_id)
        return self.request.response.redirect("%s" % self.action)




    @z3c.form.button.buttonAndHandler(_('Discard Changes'), name='correct')
    def handleDiscard(self, action):
        browser_session = ISession(self.request)
        browser_session[EDIT_ALIQUOT_KEY] = set()
        browser_session.save()
        self.status = _(u"Changes have been discarded")
        return self.request.response.redirect("%s" % self.action)

    @z3c.form.button.buttonAndHandler(_('Mark Missing'), name='missing')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'missing', 'Missing')
        return self.status

    @z3c.form.button.buttonAndHandler(_('Check Out'), name='checkout')
    def handleCheckout(self, action):
        self.saveChanges(action)
        self.changeState(action, 'pending-checkout', 'Pending Check Out')
        return self.status

    @z3c.form.button.buttonAndHandler(_('Return to Checked-in'), name='checkin')
    def handleCheckin(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-in', 'Checked in')
        return self.status


class EditAliquotForm(common.OccamsCrudForm):
    """
    Primary view for a clinical lab object.
    """
    editform_factory = EditAliquotEditForm
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
        return fields

    @property
    def edit_schema(self):
        fields = z3c.form.field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select('volume',
                   'cell_amount',
                   'store_date',
                   'freezer',
                   'rack',
                   'box',
                   'inventory_date',
                   'location',
                   'notes',
                   'special_instruction',
                   'thawed_num',
                   'sent_date',
                   'sent_name',
                   'sent_notes',)


        return fields

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
            aliquotfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
            self._v_query = aliquotfilter.getQuery(default_state='checked-in')
        return self._v_query

class AliquotView(common.OccamsLabView):
    """
    View of a specimen type. Allows editing of
    """

    instructions = [
         {'title':'Select All',
        'description': 'Select or deselect all items displayed on the current page.'},
        {'title':'Edit Aliquot',
        'description': 'Places the selected aliquot into edit mode. '},
        {'title':'Save All Changes',
        'description': 'Saves all of the changes entered to the database. Returns the aliquot to display mode.'},
        {'title':'Discard Changes',
        'description': 'Returns the aliquot to display mode without saving changes.'},
        {'title':'Mark Missing',
        'description': 'Marks the selected aliquot as missing.'},
        {'title':'Check out',
        'description': 'Saves all of the changes entered to the database. Move the selected aliquot to a "pending check out" state, ' \
                            'and makes them available in the <a href="checkout">Check out</a> queue.'},
        {'title':'Return to Checked-In',
        'description': 'Return the selected aliquot to a "checked in" state. Useful when you\'ve found missing aliquot, etc'},
        ]

    def current_filter(self):
        aliquotfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
        filter =  aliquotfilter.getFilterValues()
        if 'Aliquot State' not in filter:
            filter['Aliquot State'] = u"Checked In"
        return filter.iteritems()

    def has_filter(self):
        aliquotfilter =  zope.component.getMultiAdapter((self.context, self.request),interfaces.IAliquotFilter)
        filter =  aliquotfilter.getFilterValues()
        if filter:
            return True
        return False

    @property
    def entry_count(self):
        if not hasattr(self, '_v_aliquot_edit_form'):
            return 4
            self._v_aliquot_edit_form = EditAliquotForm(self.context, self.request)
            self._v_aliquot_edit_form.update()
        return self._v_aliquot_edit_form.count

    @property
    def crud_form(self):
        if not hasattr(self, '_v_aliquot_edit_form'):
            self._v_aliquot_edit_form = EditAliquotForm(self.context, self.request)
            self._v_aliquot_edit_form.update()
        return self._v_aliquot_edit_form


    @property
    def filter_form(self):
        if not hasattr(self, '_v_aliquot_filter_form'):
            self._v_aliquot_filter_form = AliquotFilterFormView(self.context, self.request)
            self._v_aliquot_filter_form.update()
        return self._v_aliquot_filter_form

