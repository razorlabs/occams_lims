from zope.component import  getSiteManager
from z3c.form import button, field
from z3c.form import form as z3cform
from plone.z3cform.crud import crud

from avrc.data.store.interfaces import IDatastore
from beast.browser.crud import BatchNavigation
from z3c.form.interfaces import  DISPLAY_MODE

from hive.lab import MessageFactory as _
from hive.lab.interfaces.labels import ILabelPrinter
from hive.lab.interfaces.managers import ISpecimenManager
from hive.lab.interfaces.managers import IAliquotManager

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
        Using the passed state, change the selected items to that state
        """
        selected = self.selected_items()
        if selected:
            for id, obj in selected:
                setattr(obj, 'state', unicode(state))
                newobj = self.dsmanager.put(obj)
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
                newobj = self.dsmanager.put(obj)
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
            sm = getSiteManager(self)
            ds = sm.queryUtility(IDatastore, 'fia')
            self.dsmanager = ISpecimenManager(ds)
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

    @button.buttonAndHandler(_('Print Selected'), name='printed')
    def handlePrint(self, action):
        self.saveChanges(action)
        self.queLabels(action)
        return

    @button.buttonAndHandler(_('Save All Changes'), name='updated')
    def handleUpdate(self, action):
        self.saveChanges(action)
        return

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
            sm = getSiteManager(self)
            ds = sm.queryUtility(IDatastore, 'fia')
            self.dsmanager = ISpecimenManager(ds)
        self.sampletype = _(u"aliquot")

    def queLabels(self, action):
        """
        Place these aliquot in the print que
        """
        selected = self.selected_items()
        if selected:
            labelsheet = ILabelPrinter(self.context.context)
            for id, obj in selected:
                labelsheet.queLabel(obj)
            self.status = _(u"Your %s have been qued." % self.sampletype)
        else:
            self.status = _(u"Please select %s to que." % self.sampletype)

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

    @button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        self.printLabels(action)
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Batch Selected'), name='batched')
    def handleBatchDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'batched', 'batched')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Postpone Selected'), name='postponed')
    def handlePostponeDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'postponed', 'postponed')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Mark Selected Undrawn'), name='rejected')
    def handleCancelDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'rejected', 'canceled')
        self._update_subforms()
        return
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class SpecimenBatchedButtons(SpecimenButtonCore):
    label = _(u"")
    z3cform.extends(SpecimenButtonCore)

    @button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        self.queLabels(action)
        self._update_subforms()
        return
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class SpecimenPostponedButtons(SpecimenButtonCore):
    label = _(u"Postponed Specimen")
    z3cform.extends(SpecimenButtonCore)
    @button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        self.queLabels(action)
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Batch Selected'), name='batched')
    def handleBatchDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'batched', 'batched')
        self.queLabels(action)
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Mark Selected Undrawn'), name='cancel')
    def handleCancelDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'rejected', 'canceled')
        self._update_subforms()
        return

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class SpecimenRecoverButtons(SpecimenButtonCore):
    label = _(u"")
    z3cform.extends(SpecimenButtonCore)

    @button.buttonAndHandler(_('Recover selected'), name='recover')
    def handleRecover(self, action):
        self.changeState(action, 'pending-draw', 'recover')
        self._update_subforms()
        return

# ------------------------------------------------------------------------------
# These are supporting Research Lab Views
# ------------------------------------------------------------------------------

class ReadySpecimenButtons(SpecimenButtonCore):
    label = _(u"")

    @button.buttonAndHandler(_('Select All'), name='selectall')
    def handleSelectAll(self, action):
        pass

    @button.buttonAndHandler(_('Ready selected'), name='ready')
    def handleCompleteDraw(self, action):
        self.changeState(action, 'pending-aliquot', 'ready')
        self._update_subforms()
        return

# ------------------------------------------------------------------------------
# Creating aliquot is different enough that subclassing another button manager 
# seems like a bad idea. 
# ------------------------------------------------------------------------------
class AliquotCreator(crud.EditForm):
    """
    """
    label = _(u"")

    def __init__(self, context, request):
        """
        Provide a specimen manager for these buttons
        """
        super(AliquotCreator, self).__init__(context, request)
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        self.specimen_manager = ISpecimenManager(ds)
        self.aliquot_manager = ISpecimenManager(ds)

    editsubform_factory = OrderedSubForm

    def changeState(self, action, state, acttitle):
        """
        Change the state of a specimen based on the id pulled from a template 
        """
        selected = self.selected_items()
        if selected:
            for id, aliquottemplate in selected:
                specimenobj = self.context.specimen_manager.get(aliquottemplate.specimen_dsid)
                setattr(specimenobj, 'state', unicode(state))
                newspecimen = self.context.specimen_manager.put(specimenobj)
            self.status = _(u"Your specimen have been %s." % (acttitle))
        else:
            self.status = _(u"Please select aliquot templates." % (acttitle))

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
                newaliquot = self.context.aliquot_manager.put(blueprint)
            if status is no_changes:
                status = success
        self.status = status
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Mark Specimen Complete'), name='complete')
    def handleCompleteSpecimen(self, action):
        self.changeSpecimenState(action, 'aliquoted', 'completed')
        self._update_subforms()
        return



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

    @button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Check In Aliquot'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.queLabels(action)
        self.changeAliquotState(action, 'checked-in', 'Checked In')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Print Selected'), name='print')
    def handlePrintAliquot(self, action):
        self.saveChanges(action)
        self.queLabels(action)
        return

    @button.buttonAndHandler(_('Mark Aliquot Unused'), name='unused')
    def handleUnusedAliquot(self, action):
        self.saveChanges(action)
        self.changeAliquotState(action, 'unused', 'Unused')
        self._update_subforms()
        return
#class AliquotRecoverer(AliquotButtonCore):
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotRecoverButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @button.buttonAndHandler(_('Recover Aliquot'), name='recover')
    def handleRecoverAliquot(self, action):
        self.changeAliquotState(action, 'pending', 'Recovered')
        self._update_subforms()
        return

#class AliquotEditManager(AliquotButtonCore):
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotEditButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Check Back In'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeAliquotState(action, 'checked-in', 'Checked In')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Check Out'), name='checkout')
    def handleCheckoutAliquot(self, action):
        self.saveChanges(action)
        self.changeAliquotState(action, 'pending-checkout', 'Checked Out')
        self._update_subforms()
        return
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
#class AliquotCheckoutManager(AliquotButtonCore):
class AliquotCheckoutButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @button.buttonAndHandler(_('Complete Check Out'), name='checkout')
    def handleCheckoutAliquot(self, action):
        self.saveChanges(action)
        self.changeAliquotState(action, 'checked-out', 'Checked Out')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Return To Hold'), name='hold')
    def handleRehold(self, action):
        self.changeAliquotState(action, 'hold', 'Held')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Check Back In'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.changeAliquotState(action, 'checked-in', 'Checked In')
        self._update_subforms()
        return
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------        
#class AllAliquotManager(AliquotButtonCore):
class AliquotQueButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @button.buttonAndHandler(_('Que & Hold'), name='que')
    def handleQue(self, action):
        self.changeAliquotState(action, 'hold', 'Qued')
        self._update_subforms()
        return
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
#class QueManager(AliquotButtonCore):
class AliquotHoldButtons(AliquotButtonCore):
    """
    """
    z3cform.extends(AliquotButtonCore)

    @button.buttonAndHandler(_('Print List'), name='print')
    def handleQue(self, action):
        return self.request.response.redirect('%s/%s' % (self.context.context.absolute_url(), 'checklist'))

    @button.buttonAndHandler(_('Check Out'), name='checkout')
    def handleCheckout(self, action):
        self.changeAliquotState(action, 'pending-checkout', 'Checked Out')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Release Hold'), name='release')
    def handleRelease(self, action):
        self.changeAliquotState(action, 'checked-in', 'Released')
        self._update_subforms()
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Inaccurate'), name='incorrect')
    def handleInaccurate(self, action):
        self.changeAliquotState(action, 'incorrect', 'incorrect')
        self._update_subforms()
        return

    @button.buttonAndHandler(_('Mark Missing'), name='missing')
    def handleMissing(self, action):
        self.changeAliquotState(action, 'missing', 'Missing')
        self._update_subforms()
        return

# ------------------------------------------------------------------------------
# Label Buttons |
# --------------
# These classes provide the various transitions and modifications of the labels
# in the label que
# ------------------------------------------------------------------------------    

#class LabelManager(crud.EditForm):
class LabelButtons(crud.EditForm):
    """
    """
    editsubform_factory = OrderedSubForm

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
        que = self.context.labeler.getLabelQue()
        label_list = []
        for id, label in selected:
            label_list.append(label)
            que.uncatalog_object(str(id))
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

    @button.buttonAndHandler(_('Remove Selected'), name='remove')
    def handleRemove(self, action):
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Remove.")
            return
        #self.context.labeler
        for id, label in selected:
            self.context.labeler.purgeLabel(id)
        self._update_subforms()
