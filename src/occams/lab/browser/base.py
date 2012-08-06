
from occams.lab import MessageFactory as _, \
                     SCOPED_SESSION_KEY
# from occams.lab.browser import crud

from z3c.form import button, field
from beast.browser.crud import BatchNavigation

from z3c.saconfig import named_scoped_session

from occams.lab import interfaces
from plone.z3cform.crud import crud
from occams.datastore.batch import SqlBatch

import datetime
from z3c.form import form
from collective.beaker.interfaces import ISession
import sys

SUCCESS_MESSAGE = _(u"Successfully updated")
PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
NO_CHANGES = _(u"No changes made.")

class CoreButtons(crud.EditForm):
    label = _(u"")

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
        query = self.context.get_query()
        batch_size = self.context.batch_size or sys.maxint
        page = self._page()
        return SqlBatch(
            query, start=page * batch_size, size=batch_size)

    @property
    def _stateModel(self):
        raise NotImplementedError

    @property
    def sampletype(self):
        raise NotImplementedError

    @property
    def _model(self):
        raise NotImplementedError

    def saveChanges(self, action):
        """
        Apply changes to all items on the page
        """
        success = SUCCESS_MESSAGE
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = NO_CHANGES
        session = named_scoped_session(SCOPED_SESSION_KEY)
        for subform in self.subforms:
            data, errors = subform.extractData()
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            changes = subform.applyChanges(data)
            if changes:
                session.flush()
            if status is no_changes:
                status = success
        self.status = status

    def changeState(self, action, state, acttitle):
        """
        Using the passed state, change the selected items to that state
        """
        selected = self.selected_items()
        session = named_scoped_session(SCOPED_SESSION_KEY)
        if selected:
            state = session.query(self._stateModel).filter_by(name=state).one()
            for id, data in selected:
                obj = session.query(self._model).filter_by(id=id).one()
                obj.state = state
                session.flush()
            self.status = _(u"Your %s have been changed to the status of %s." % (self.sampletype, acttitle))
        else:
            self.status = _(u"Please select %s" % (self.sampletype))


    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

class CoreForm(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """

    def update(self):
        self.update_schema = self.edit_schema
        super(CoreForm, self).update()

    ignoreContext = True
    addform_factory = crud.NullForm
    batch_size = 20

    @property
    def edit_schema(self):
        raise NotImplementedError

    @property
    def editform_factory(self):
        raise NotImplementedError

    @property
    def display_state(self):
        raise NotImplementedError

    def get_query(self):
        raise NotImplementedError
        #makes testing a LOT easier

    def getCount(self):
        return self.get_query().count()

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        if getattr(self, '_sqlBatch', None) is None:
            self._sqlBatch = SqlBatch(self.get_query())
        return self._sqlBatch


class LabelButtons(crud.EditForm):
    """
    """

    @property
    def prefix(self):
        return 'label.'

    def render_batch_navigation(self):
        """
        Render the batch navigation to include the default styles for Plone
        """
        navigation = BatchNavigation(self.batch, self.request)
        def make_link(page):
            return "%s?%spage=%s" % (self.request.getURL(), self.prefix, page)
        navigation.make_link = make_link
        return navigation()

    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    label = _(u"Label Printer")
    @button.buttonAndHandler(_('Print Selected'), name='print_pdf')
    def handlePDFPrint(self, action):
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Print.")
            return
        queue = self.context.labeler.getLabelQueue()
        label_list = []
        for id, label in selected:
            label_list.append(label)
            queue.uncatalog_object(str(id))
        content = self.context.labeler.printLabelSheet(label_list)

        self.request.RESPONSE.setHeader("Content-type", "application/pdf")
        self.request.RESPONSE.setHeader("Content-disposition",
                                        "attachment;filename=labels.pdf")
        self.request.RESPONSE.setHeader("Cache-Control", "no-cache")
        self.request.RESPONSE.write(content)
        self.status = _(u"You print is on its way. Refresh the page to view only unprinted labels.")
        return

    @button.buttonAndHandler(_('Refresh List'), name='refresh')
    def handleRefresh(self, action):
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Clear Selected'), name='remove')
    def handleRemove(self, action):
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Clear.")
            return
        #self.context.labeler
        for id, label in selected:
            self.context.labeler.purgeLabel(id)

        return self.request.response.redirect(self.action)

class LabelForm(crud.CrudForm):
    """
    """
    def __init__(self, context, request):
        super(LabelForm, self).__init__(context, request)
        self.labeler = interfaces.ILabelPrinter(context)

    editform_factory = LabelButtons
    ignoreContext = True
    addform_factory = crud.NullForm

    @property
    def batch_size(self):
        return self.context.no_across * self.context.no_down

    view_schema = field.Fields(interfaces.ILabel).\
        select('id',
         'patient_title',
         'cycle_title',
         'sample_date',
         'sample_type')

    def get_items(self):

        brainz = self.labeler.getLabelBrains()
        labellist = []
        for label in brainz:
            labellist.append((label.getPath(), label))
        return labellist

class FilterFormCore(form.Form):
    """
    Take form data and apply it to the session so that filtering takes place.
    """
    ignoreContext = True

    def update(self):
        super(FilterFormCore, self).update()
        session = ISession(self.request)
        for key, value in session.items():
            if value is None or key not in self.fields.keys():
                continue
            elif type(value) == datetime.date:
                self.widgets[key].value = (unicode(value.year), unicode(value.month), unicode(value.day))
            elif hasattr(self.widgets[key], 'terms'):
                try: # to process this vocabulary object
                    self.widgets[key].value = [value]
                except:
                    self.widgets[key].value = value
            else:
                self.widgets[key].value = value

    @property
    def fields(self):
        if hasattr(self.context, 'omit_filter'):
            omitables = self.context.omit_filter
            return field.Fields(interfaces.IFilterForm).omit(*omitables)
        return field.Fields(interfaces.IFilterForm).omit('state')

    @button.buttonAndHandler(u'Filter')
    def handleFilter(self, action):
        session = ISession(self.request)
        data, errors = self.extractData()
        if errors:
            self.status = _(u"Sorry.")
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

        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(u'Remove Filter')
    def handleClearFilter(self, action):
        session = ISession(self.request)
        session.clear()
        return self.request.response.redirect(self.action)
