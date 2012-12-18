from Products.Five.browser import BrowserView
from plone.z3cform.crud import crud
from occams.datastore.batch import SqlBatch
from occams.lab import Session
from occams.lab import MessageFactory as _
from beast.browser.crud import BatchNavigation
import sys
import z3c.form
import zope.component
from occams.lab import interfaces
from collective.beaker.interfaces import ISession
import datetime
from Products.statusmessages.interfaces import IStatusMessage
from occams.lab import FILTER_KEY
from avrc.aeh import interfaces as clinical
from occams.lab import model
from sqlalchemy.orm import exc
from occams.form.traversal import closest
from plone.z3cform import layout
from z3c.form.interfaces import DISPLAY_MODE
from beast.browser import widgets

# class LabFilterForm(z3c.form.form.Form):
#     """
#     Specimen Filter form. This form presents itself as an overlay on the Primary
#     Clinical Lab view as a way to filter specimen.
#     """
#     ignoreContext = True
#     description = _(u"Please enter filter criteria. You may filter by any or all options. "
#                            u" Aliquot and specimen are, by default, filtered by state, which depends on your current view. "
#                            u"The filter will persist while you are logged in. ")

#     @property
#     def fields(self):
#         filter =  zope.component.getMultiAdapter((self.context, self.request), interfaces.IFilter)
#         omitable = []
#         if 'omit' in self.request:
#             if type(self.request['omit']) == list:
#                 omitable = self.request['omit']
#             else:
#                 omitable =  [self.request['omit'],]
#         return filter.getFilterFields(omitable=omitable)

#     def updateWidgets(self):
#         """
#         Apply The information in the browser request as values to this form
#         """
#         z3c.form.form.Form.updateWidgets(self)
#         browser_session = ISession(self.request)
#         if FILTER_KEY in browser_session:
#             specimenfilter = browser_session[FILTER_KEY]
#             for key, widget in self.widgets.items():
#                 if key in specimenfilter:
#                     value = specimenfilter[key]
#                     if type(value) == datetime.date:
#                         widget.value = (unicode(value.year), unicode(value.month), unicode(value.day))
#                     elif type(value) == bool and value:
#                         widget.value = ['selected']
#                     elif hasattr(widget, 'terms'):
#                         widget.value = [value]
#                     else:
#                         widget.value = value
#                     widget.update()

#     @z3c.form.button.buttonAndHandler(u'Filter')
#     def handleFilter(self, action):
#         data, errors = self.extractData()
#         messages = IStatusMessage(self.request)
#         if errors:
#             messages.addStatusMessage(
#                 _(u'There was an error with your request.'),
#                 type=u'error'
#                 )
#             return
#         browser_session = ISession(self.request)
#         browser_session[FILTER_KEY] = {}
#         for key, value in data.items():
#             if value is not None:
#                 if getattr(value, 'name', False):
#                     browser_session[FILTER_KEY][key] = value.name
#                 else:
#                     browser_session[FILTER_KEY][key] = value
#         browser_session.save()
#         messages.addStatusMessage(_(u"Your Filter has been applied"), type=u'info')
#         return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())

#     @z3c.form.button.buttonAndHandler(u'Remove Filter')
#     def handleClearFilter(self, action):
#         browser_session = ISession(self.request)
#         browser_session[FILTER_KEY] = {}
#         messages = IStatusMessage(self.request)
#         messages.addStatusMessage(_(u"Your Filter has been cleared"), type=u'info')
#         return self.request.response.redirect("%s/filtersuccess" % self.context.absolute_url())


class LocationEditForm(crud.EditForm):
    """
    Provide the default crud.EditForm features that repeat in every form
    """
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
        for subform in self.subforms:
            data, errors = subform.extractData()
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            del data['select']
            self.context.before_update(subform.content, data)
            changes = subform.applyChanges(data)
            if changes:
                if status is no_changes:
                    status = success
        Session.flush()
        self._update_subforms()
        self.status = status

    @z3c.form.button.buttonAndHandler(_('Save All Changes'), name='updated')
    def handleUpdate(self, action):
        self.saveChanges(action)
        return self.status

class LocationCrudForm(crud.CrudForm):
    description = _(u"")

    ignoreContext = True
    batch_size = 20

    editform_factory = LocationEditForm
    add_schema = z3c.form.field.Fields(interfaces.ILocation).\
            select(
                    'name',
                    'title',
                    'active',
                    'long_title1',
                    'long_title2',
                    'address_street',
                    'address_city',
                    'address_state',
                    'address_zip',
                    'phone_number',
                    'fax_number',
                    )
    @property
    def edit_schema(self):
        fields = z3c.form.field.Fields(interfaces.ILocation).\
            select(
                    'active',
                    )
        fields += z3c.form.field.Fields(interfaces.IViewableLocation, mode=DISPLAY_MODE).\
            select(
                    'lab_title',
                    )
        fields += z3c.form.field.Fields(interfaces.ILocation).\
            select(
                    'long_title1',
                    'long_title2',
                    'address_street',
                    'address_city',
                    'address_state',
                    'address_zip',
                    'phone_number',
                    'fax_number',
                    )
        return fields

    def update(self):
        self.update_schema = self.edit_schema
        self.query = self._getQuery()
        self.count = self.query.count()
        super(LocationCrudForm, self).update()

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        if getattr(self, '_v_sqlBatch', None) is None:
            self._v_sqlBatch = SqlBatch(self.query)
        return self._v_sqlBatch

    def _getQuery(self):
        query = Session.query(model.Location).order_by(model.Location.title.asc())
        return query


    def updateWidgets(self):
        super(LocationCrudForm, self).updateWidgets()
        if self.update_schema is not None:
            if 'address_city' in self.update_schema.keys():
                self.update_schema['address_city'].widgetFactory = widgets.AmountFieldWidget
            if 'address_state' in self.update_schema.keys():
                self.update_schema['address_state'].widgetFactory = widgets.StorageFieldWidget
            if 'address_zip' in self.update_schema.keys():
                self.update_schema['address_zip'].widgetFactory = widgets.AmountFieldWidget
            # if 'rack' in self.update_schema.keys():
            #     self.update_schema['rack'].widgetFactory = widgets.StorageFieldWidget
            # if 'box' in self.update_schema.keys():
            #     self.update_schema['box'].widgetFactory = widgets.StorageFieldWidget
            # if 'thawed_num' in self.update_schema.keys():
            #     self.update_schema['thawed_num'].widgetFactory = widgets.StorageFieldWidget

LabLocationView = layout.wrap_form(LocationCrudForm)


