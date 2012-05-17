
from five import grok
from occams.lab import MessageFactory as _, \
                     SCOPED_SESSION_KEY
from occams.lab.browser import crud
from occams.lab.browser import buttons
from occams.lab.interfaces import IClinicalLab

from z3c.form import button, field, form as z3cform


class SpecimenPendingButtons(buttons.SpecimenButtonCore):
    label = _(u"")
    z3cform.extends(buttons.SpecimenButtonCore)

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

class View(crud.SpecimenCoreForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IClinicalLab)
    grok.require('occams.lab.ManageSpecimen')

    def update(self):
        import pdb; pdb.set_trace( )
        super(View, self).update()

    @property
    def editform_factory(self):
        return SpecimenPendingButtons

    @property
    def display_state(self):
        return u"pending-draw"

    # def __init__(self, context, request):
    #     super(ClinicalLabView, self).__init__(context, request)

    # def update(self):
    #     self.crudform = self.getCrudForm()
    #     super(ClinicalLabView, self).update()

    # def getCrudForm(self):
    #     """
    #     Create a form instance.
    #     @return: z3c.form wrapped for Plone 3 view
    #     """
    #     context = self.context.aq_inner
    #     form = crud.SpecimenPendingForm(context, self.request)
    #     if hasattr(form, 'getCount') and form.getCount() < 1:
    #         return None
    #     view = NestedFormView(context, self.request)
    #     view = view.__of__(context)
    #     view.form_instance = form
    #     return view
