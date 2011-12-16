from AccessControl import getSecurityManager
from avrc.data.store.batch import SqlBatch
from avrc.data.store.interfaces import IDataStore
from beast.browser.crud import BatchNavigation
from hive.lab import MessageFactory as _, \
                     SCOPED_SESSION_KEY
from hive.lab.interfaces.labels import ILabelPrinter
from hive.lab.interfaces.managers import IAliquotManager, \
                                         ISpecimenManager
from plone.z3cform.crud import crud
from z3c.form import button, field, form as z3cform
from z3c.form.interfaces import DISPLAY_MODE
from z3c.saconfig import named_scoped_session
import sys
from datetime import date

SUCCESS_MESSAGE = _(u"Successfully updated")
PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
NO_CHANGES = _(u"No changes made.")

# ------------------------------------------------------------------------------
# Button Cores  |
# --------------
# These classes offer the base functionality for all of the buttons in this
# product.
# ------------------------------------------------------------------------------

class OrderedSubForm(crud.EditSubForm):
    """
        # Brought over from to exchange the order of the view and update schemas

    """
    @property
    def fields(self):
        fields = field.Fields(self._select_field())

        crud_form = self.context.context

        view_schema = crud_form.view_schema
        if view_schema is not None:
            view_fields = field.Fields(view_schema)
            for f in view_fields.values():
                f.mode = DISPLAY_MODE
                # This is to allow a field to appear in both view
                # and edit mode at the same time:
                if not f.__name__.startswith('view_'):
                    f.__name__ = 'view_' + f.__name__
            fields += view_fields

        update_schema = crud_form.update_schema
        if update_schema is not None:
            fields += field.Fields(update_schema)
        return fields

class ButtonCore(crud.EditForm):
    """
    Core for all buttons
    """
    dsmanager = None
    sampletype = None
    editsubform_factory = OrderedSubForm

    @property
    def prefix(self):
        return 'crud-edit.'


    def __init__(self, context, request):
        """
        Provide a specimen manager for these buttons
        """
        super(crud.EditForm, self).__init__(context, request)

    @property
    def currentUser(self):
        return getSecurityManager().getUser().getId()
        
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
        query = self.context.getQuery()
        batch_size = self.context.batch_size or sys.maxint
        page = self._page()
        return SqlBatch(
            query, start=page * batch_size, size=batch_size)
    #batch = zope.cachedescriptors.property.CachedProperty(batch)

    def changeState(self, action, state, acttitle):
        """
        Using the passed state, change the selected items to that state
        """
        selected = self.selected_items()
        if selected:
            for id, obj in selected:
                setattr(obj, 'state', unicode(state))
                self.dsmanager.put(obj)
            self.status = _(u"Your %s have been changed to the status of %s." % (self.sampletype, acttitle))
        else:
            self.status = _(u"Please select %s" % (self.sampletype))

    def saveChanges(self, action):
        """
        Apply changes to all items on the page
        """
        success = SUCCESS_MESSAGE
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = NO_CHANGES
        for subform in self.subforms:
            data, errors = subform.extractData()
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            self.context.before_update(subform.content, data)
            obj = subform.content
            updated = False
            for prop, value in data.items():

                if hasattr(obj, prop) and getattr(obj, prop) != value:
                    setattr(obj, prop, value)
                    updated = True
                    if status is no_changes:
                        status = success
            if updated:
                self.dsmanager.put(obj)
        self.status = status



# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class SpecimenButtonCore(ButtonCore):
    """
    Core functionality for specimen buttons
    """

    label = _(u"")

    def __init__(self, context, request):
        """
        Provide a specimen manager for these buttons
        """
        super(SpecimenButtonCore, self).__init__(context, request)
        if hasattr(context, 'dsmanager') and context.dsmanager is not None:
            self.dsmanager = context.dsmanager
        else:
            self.dsmanager = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
        self.sampletype = _(u"specimen")

    def printLabels(self, action):
        selected = self.selected_items()
        label_list = []
        labelsheet = ILabelPrinter(self.context.context)
        for id, item in selected:
            count = item.tubes
            if count is None or count < 1:
                count = 1
            for i in range(count):
                label_list.append(item)
        content = labelsheet.printLabelSheet(label_list)

        self.request.RESPONSE.setHeader("Content-type", "application/pdf")
        self.request.RESPONSE.setHeader("Content-disposition",
                                        "attachment;filename=labels.pdf")
        self.request.RESPONSE.setHeader("Cache-Control", "no-cache")
        self.request.RESPONSE.write(content)
        self.status = _(u"Your print is on its way. Refresh the page to view only unprinted labels.")

    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotButtonCore(ButtonCore):
    """
    Core functionality for aliquot buttons
    """
    label = _(u"")

    def __init__(self, context, request):
        """
        Provide a specimen manager for these buttons
        """
        super(AliquotButtonCore, self).__init__(context, request)
        if hasattr(context, 'dsmanager') and context.dsmanager is not None:
            self.dsmanager = context.dsmanager
        else:
            self.dsmanager = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
        self.sampletype = _(u"aliquot")


    def queueLabels(self, action):
        """
        Place these aliquot in the print queue
        """
        selected = self.selected_items()
        if selected:
            labelsheet = ILabelPrinter(self.context.context)
            for id, obj in selected:
                labelsheet.queueLabel(obj)
            self.status = _(u"Your %s have been queued." % self.sampletype)
        else:
            self.status = _(u"Please select %s to queue." % self.sampletype)

    def changeState(self, action, state, acttitle):
        """
        Using the passed state, change the selected items to that state
        """
        selected = self.selected_items()
        if selected:
            for id, obj in selected:
                setattr(obj, 'state', unicode(state))
                self.dsmanager.put(obj, by=self.currentUser)
            self.status = _(u"Your %s have been changed to the status of %s." % (self.sampletype, acttitle))
        else:
            self.status = _(u"Please select %s" % (self.sampletype))

    def saveChanges(self, action):
        """
        Apply changes to all items on the page
        """
        success = SUCCESS_MESSAGE
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = NO_CHANGES
        for subform in self.subforms:
            data, errors = subform.extractData()
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            self.context.before_update(subform.content, data)
            obj = subform.content
            updated = False
            for prop, value in data.items():

                if hasattr(obj, prop) and getattr(obj, prop) != value:
                    setattr(obj, prop, value)
                    updated = True
                    if status is no_changes:
                        status = success
            if updated:
                self.dsmanager.put(obj, by=self.currentUser)
        self.status = status

    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

# ------------------------------------------------------------------------------
# Specimen Buttons |
# --------------
# These classes provide the various transitions and modifications of the pages
# that support and modify specimen
# ------------------------------------------------------------------------------

class SpecimenPendingButtons(SpecimenButtonCore):
    label = _(u"")
    z3cform.extends(SpecimenButtonCore)

    @property
    def prefix(self):
        return 'specimen-pending.'
        
    @button.buttonAndHandler(_('Print Selected'), name='printed')
    def handlePrint(self, action):
        self.saveChanges(action)
        self.printLabels(action)
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Save All Changes'), name='updated')
    def handleUpdate(self, action):
        self.saveChanges(action)
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Batch Selected'), name='batched')
    def handleBatchDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'batched', 'batched')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Postpone Selected'), name='postponed')
    def handlePostponeDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'postponed', 'postponed')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Selected Undrawn'), name='rejected')
    def handleCancelDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'rejected', 'canceled')
        
        return self.request.response.redirect(self.action)
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class SpecimenBatchedButtons(SpecimenButtonCore):
    label = _(u"")
    z3cform.extends(SpecimenButtonCore)
    @property
    def prefix(self):
        return 'specimen-batched.'

    @button.buttonAndHandler(_('Print Selected'), name='printed')
    def handlePrint(self, action):
        self.saveChanges(action)
        self.printLabels(action)
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Save All Changes'), name='updated')
    def handleUpdate(self, action):
        self.saveChanges(action)
        
        return self.request.response.redirect(self.action)
        
    @button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        
        return self.request.response.redirect(self.action)
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class SpecimenPostponedButtons(SpecimenButtonCore):
    label = _(u"Postponed Specimen")
    z3cform.extends(SpecimenButtonCore)
    @property
    def prefix(self):
        return 'specimen-postponed.'

    @button.buttonAndHandler(_('Print Selected'), name='printed')
    def handlePrint(self, action):
        self.saveChanges(action)
        self.printLabels(action)
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Save All Changes'), name='updated')
    def handleUpdate(self, action):
        self.saveChanges(action)
        
        return self.request.response.redirect(self.action)
        
    @button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Batch Selected'), name='batched')
    def handleBatchDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'batched', 'batched')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Selected Undrawn'), name='cancel')
    def handleCancelDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'rejected', 'canceled')
        
        return self.request.response.redirect(self.action)

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class SpecimenRecoverButtons(SpecimenButtonCore):
    label = _(u"")
    z3cform.extends(SpecimenButtonCore)

    @property
    def prefix(self):
        return 'specimen-recover.'
        
    @button.buttonAndHandler(_('Recover selected'), name='recover')
    def handleRecover(self, action):
        self.changeState(action, 'pending-draw', 'recover')
        
        return self.request.response.redirect(self.action)

# ------------------------------------------------------------------------------
# These are supporting Research Lab Views
# ------------------------------------------------------------------------------

class ReadySpecimenButtons(SpecimenButtonCore):
    label = _(u"")

    @property
    def prefix(self):
        return 'specimen-ready.'
        
    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @button.buttonAndHandler(_('Ready selected'), name='ready')
    def handleCompleteDraw(self, action):
        self.changeState(action, 'pending-aliquot', 'ready')
        
        return self.request.response.redirect(self.action)

# ------------------------------------------------------------------------------
# Creating aliquot is different enough that subclassing another button manager 
# seems like a bad idea. 
# ------------------------------------------------------------------------------
class AliquotCreator(crud.EditForm):
    """
    """
    label = _(u"")
    @property
    def prefix(self):
        return 'aliquot-creator.'
        
    def __init__(self, context, request):
        """
        Provide a specimen manager for these buttons
        """
        super(AliquotCreator, self).__init__(context, request)
        self.specimen_manager = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
        self.aliquot_manager = IAliquotManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))

    editsubform_factory = OrderedSubForm

    @property
    def currentUser(self):
        return getSecurityManager().getUser().getId()
        
    def render_batch_navigation(self):
        """
        Render the batch navigation to include the default styles for Plone
        """
        navigation = BatchNavigation(self.batch, self.request)

        def make_link(page):
            return "%s?%spage=%s" % (self.request.getURL(), self.prefix, page)

        navigation.make_link = make_link
        return navigation()

    def changeState(self, action, state, acttitle):
        """
        Change the state of a specimen based on the id pulled from a template 
        """
        selected = self.selected_items()
        if selected:
            for id, aliquottemplate in selected:
                specimenobj = self.context.specimen_manager.get(aliquottemplate.specimen_dsid)
                setattr(specimenobj, 'state', unicode(state))
                self.context.specimen_manager.put(specimenobj)
            self.status = _(u"Your specimen have been %s." % (acttitle))
        else:
            self.status = _(u"Please select aliquot templates." % (acttitle))

    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass
        
    @button.buttonAndHandler(_('Create Aliquot'), name='aliquot')
    def handleCreateAliquot(self, action):
        """
        """
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Aliquot.")
            return
        success = _(u"Successfully Aliquoted")
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = _(u"No Aliquot Entered.")
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
            blueprint = subform.content
            count = 0
            for prop, value in data.items():
                if prop == 'select':
                    continue
                elif prop == 'count':
                    count = value
                elif hasattr(blueprint, prop):
                    setattr(blueprint, prop, value)
            for i in range(count):
                if hasattr(blueprint, 'dsid'):
                    # the put has updated blueprint. reset it.
                    blueprint.dsid = None
                self.aliquot_manager.put(blueprint, by=self.currentUser)
            if status is no_changes:
                status = success
        self.status = status
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Specimen Complete'), name='complete')
    def handleCompleteSpecimen(self, action):
        self.changeState(action, 'aliquoted', 'completed')
        
        return self.request.response.redirect(self.action)



# ------------------------------------------------------------------------------
# Aliquot Buttons |
# --------------
# These classes provide the various transitions and modifications of the pages
# that support and modify aliquot
# ------------------------------------------------------------------------------        

#class AliquotVerifier(AliquotButtonCore):

class AliquotPreparedButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-prepared.'
        
    @button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        return self.request.response.redirect(self.action)
        
    @button.buttonAndHandler(_('Print Selected'), name='print')
    def handlePrintAliquot(self, action):
        self.saveChanges(action)
        self.queueLabels(action)
        return self.request.response.redirect(self.action)
        
    @button.buttonAndHandler(_('Check In Aliquot'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-in', 'Checked In')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Aliquot Unused'), name='unused')
    def handleUnusedAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'unused', 'Unused')
        
        return self.request.response.redirect(self.action)
#class AliquotRecoverer(AliquotButtonCore):
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotRecoverButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-recover.'
        
    @button.buttonAndHandler(_('Recover Aliquot'), name='recover')
    def handleRecoverAliquot(self, action):
        self.changeState(action, 'pending', 'Recovered')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Hold'), name='hold')
    def handleHoldAliquot(self, action):
        self.changeState(action, 'hold', 'Held')
        
        return self.request.response.redirect(self.action)

#class AliquotEditManager(AliquotButtonCore):
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotEditButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-edit.'
        
    @button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Check Back In'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-in', 'Checked In')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Check Out'), name='checkout')
    def handleCheckoutAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'pending-checkout', 'Checked Out')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Hold'), name='hold')
    def handleRecoverAliquot(self, action):
        self.changeState(action, 'hold', 'Held')
        
        return self.request.response.redirect(self.action)
        
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotCheckinButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-checkin.'
        
    def saveChanges(self, action):
        """
        Apply changes to all items on the page
        """
        success = SUCCESS_MESSAGE
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = NO_CHANGES
        for subform in self.subforms:
            data, errors = subform.extractData()
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            self.context.before_update(subform.content, data)
            obj = subform.content
            updated = False
            for prop, value in data.items():
                if prop == 'thawed':
                    if value:
                        obj.thawed_num += 1
                        updated = True
                elif hasattr(obj, prop) and getattr(obj, prop) != value:
                    setattr(obj, prop, value)
                    updated = True
                    if status is no_changes:
                        status = success
            if updated:
                self.dsmanager.put(obj, by=self.currentUser)
        self.status = status

    @button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Check In'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-in', 'Checked In')
        
        return self.request.response.redirect(self.action)
        
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
#class AliquotCheckoutManager(AliquotButtonCore):
class AliquotCheckoutButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-checkout.'
    @button.buttonAndHandler(_('Print Receipt'), name='print')
    def handleQueue(self, action):
        return self.request.response.redirect('%s/%s' % (self.context.context.absolute_url(), 'receipt'))
        
    @button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        return self.request.response.redirect(self.action)
                
    @button.buttonAndHandler(_('Complete Check Out'), name='checkedout')
    def handleCheckoutAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-out', 'Checked Out')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Return To Queue'), name='queued')
    def handleRehold(self, action):
        self.changeState(action, 'queued', 'Held')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Check Back In'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.changeState(action, 'checked-in', 'Checked In')
        
        return self.request.response.redirect(self.action)
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------        
#class AllAliquotManager(AliquotButtonCore):
class AliquotQueueButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-queue.'
   
    @button.buttonAndHandler(_('Add to Queue'), name='queue')
    def handleQueue(self, action):
        self.changeState(action, 'queued', 'Queued')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Inaccurate'), name='incorrect')
    def handleInaccurate(self, action):
        self.changeState(action, 'incorrect', 'incorrect')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Hold'), name='hold')
    def handleRecoverAliquot(self, action):
        self.changeState(action, 'hold', 'Held')
        
        return self.request.response.redirect(self.action)
        
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
#class QueueManager(AliquotButtonCore):
class AliquotHoldButtons(AliquotButtonCore):
    """
    """
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-hold.'
        
    @button.buttonAndHandler(_('Print List'), name='print')
    def handleQueue(self, action):
        return self.request.response.redirect('%s/%s' % (self.context.context.absolute_url(), 'checklist'))

    @button.buttonAndHandler(_('Check Out'), name='checkout')
    def handleCheckout(self, action):
        self.changeState(action, 'pending-checkout', 'Checked Out')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Release From Queue'), name='release')
    def handleRelease(self, action):
        self.changeState(action, 'checked-in', 'Released')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Inaccurate'), name='incorrect')
    def handleInaccurate(self, action):
        self.changeState(action, 'incorrect', 'incorrect')
        #
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Missing'), name='missing')
    def handleMissing(self, action):
        self.changeState(action, 'missing', 'Missing')
        
        return self.request.response.redirect(self.action)


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
#class QueueManager(AliquotButtonCore):
class AliquotInventoryButtons(AliquotButtonCore):
    """
    """
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-inventory.'
        
    @button.buttonAndHandler(_('Mark Inventoried'), name='inventory')
    def handleInventory(self, action):
        selected = self.selected_items()
        if selected:
            for id, obj in selected:
                setattr(obj, 'inventory_date',date.today())
                self.dsmanager.put(obj)
            self.status = _(u"Your Aliquot have been inventoried.")
        else:
            self.status = _(u"Please select Aliquot to inventory")

        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Inaccurate'), name='incorrect')
    def handleInaccurate(self, action):
        self.changeState(action, 'incorrect', 'incorrect')
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Missing'), name='missing')
    def handleMissing(self, action):
        self.changeState(action, 'missing', 'Missing')
        return self.request.response.redirect(self.action)
# ------------------------------------------------------------------------------
# Label Buttons |
# --------------
# These classes provide the various transitions and modifications of the labels
# in the label queue
# ------------------------------------------------------------------------------    

#class LabelManager(crud.EditForm):
class LabelButtons(crud.EditForm):
    """
    """
    editsubform_factory = OrderedSubForm

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

