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

class FilterSuccessView(BrowserView):
    """
    A very basic view that will load quickly for a successful filter or add.
    """
    pass


class LabFilterForm(z3c.form.form.Form):
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
        specimenfilter =  zope.component.getMultiAdapter((self.context, self.request), interfaces.ISpecimenFilter)
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


class OccamsCrudEditForm(crud.EditForm):
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

class OccamsCrudForm(crud.CrudForm):
    """
    """
