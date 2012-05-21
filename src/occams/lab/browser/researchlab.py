
from five import grok
from occams.lab import MessageFactory as _, \
                     SCOPED_SESSION_KEY
# from occams.lab.browser import crud
from occams.lab.browser import buttons
from occams.lab.interfaces import IClinicalLab
from plone.directives import dexterity

from z3c.form import button, field, form as z3cform
from beast.browser.crud import BatchNavigation

from z3c.saconfig import named_scoped_session
from AccessControl import getSecurityManager
from occams.lab import interfaces
from occams.lab import model
import zope.schema
from plone.z3cform.crud import crud
from plone.z3cform import layout
from beast.browser import widgets
from occams.lab.browser.batch import SqlDictBatch
from z3c.form.interfaces import IField
from occams.form.traversal import closest
from sqlalchemy.orm import aliased
from zope.app.intid.interfaces import IIntIds


SUCCESS_MESSAGE = _(u"Successfully updated")
PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
NO_CHANGES = _(u"No changes made.")

class SpecimenCoreButtons(crud.EditForm):

    def render_batch_navigation(self):
        """
        Render the batch navigation to include the default styles for Plone
        """
        navigation = BatchNavigation(self.batch, self.request)
        def make_link(page):
            return "%s?%spage=%s" % (self.request.getURL(), self.prefix, page)
        navigation.make_link = make_link
        return navigation()


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
            obj = session.query(model.Specimen).filter(model.Specimen.id==subform.content_id).one()
            updated = False
            for prop, value in data.items():
                if hasattr(obj, prop) and getattr(obj, prop) != value:
                    setattr(obj, prop, value)
                    updated = True
                    if status is no_changes:
                        status = success
            if updated:
                session.flush()
        self.status = status

    def changeState(self, action, state, acttitle):
        """
        Using the passed state, change the selected items to that state
        """
        selected = self.selected_items()
        session = named_scoped_session(SCOPED_SESSION_KEY)
        if selected:
            for id, data in selected:
                obj = session.query(model.Specimen).filter(model.Specimen.id==id).one()
                specimenstate = session.query(model.SpecimenState).filter(model.SpecimenState.name==state).one()
                obj.state = specimenstate
                session.flush()
            self.status = _(u"Your specimen have been changed to the status of %s." % ( acttitle))
        else:
            self.status = _(u"Please select %s" % (self.sampletype))

    @button.buttonAndHandler(_('Print Selected'), name='printed')
    def handlePrint(self, action):
        self.saveChanges(action)
        self.printLabels(action)
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Save All Changes'), name='updated')
    def handleUpdate(self, action):
        self.saveChanges(action)
        return self.request.response.redirect(self.action)

class SpecimenPendingButtons(SpecimenCoreButtons):
    label = _(u"")
    z3cform.extends(SpecimenCoreButtons)

    @property
    def prefix(self):
        return 'specimen-pending.'

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

class SpecimenBatchedButtons(SpecimenCoreButtons):
    label = _(u"")
    z3cform.extends(SpecimenCoreButtons)

    @property
    def prefix(self):
        return 'specimen-pending.'

    @button.buttonAndHandler(_('Complete selected'), name='completed')
    def handleCompleteDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'complete', 'completed')
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Draw selected'), name='draw')
    def handleDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'pending-draw', 'pending draw')
        return self.request.response.redirect(self.action)

class SpecimenPostponedButtons(SpecimenCoreButtons):
    label = _(u"")
    z3cform.extends(SpecimenCoreButtons)

    @property
    def prefix(self):
        return 'specimen-pending.'

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

    @button.buttonAndHandler(_('Mark Selected Undrawn'), name='rejected')
    def handleCancelDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'rejected', 'canceled')
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Draw selected'), name='draw')
    def handleDraw(self, action):
        self.saveChanges(action)
        self.changeState(action, 'pending-draw', 'pending draw')
        return self.request.response.redirect(self.action)

class AliquotCoreForm(crud.CrudForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """

    def update(self):
        self.update_schema = self.edit_schema
        super(AliquotCoreForm, self).update()
        
    @property
    def currentUser(self):
        return getSecurityManager().getUser().getId()

    ignoreContext = True
    addform_factory = crud.NullForm
    batch_size = 5

    @property
    def edit_schema(self):
        fields = field.Fields(interfaces.IViewableAliquot).\
                    select('patient_our',
                             # 'patient_initials',
                             'cycle_title',
                             # 'visit_date', 
                             'aliquot_type',
                             'volume',
                             'cell_amount', 
                             'store_date',
                             'labbook',
                             'freezer',
                             'rack',
                             'box',
                             'special_instruction',
                             'notes'
                             )
        return fields

    def link(self, item, field):
        if field == 'patient_our':
            intids = zope.component.getUtility(IIntIds)
            patient = intids.getObject(item['patient_zid'])
            url = '%s/aliquot' % patient.absolute_url()
            return url
        # elif field == 'visit_date' and item['visit_zid']:
        #     intids = zope.component.getUtility(IIntIds)
        #     visit = intids.getObject(item['visit_zid'])
        #     url = '%s/aliquot' % visit.absolute_url()
        #     return url

        elif field == 'aliquot_type':
            url = '%s/%s' % (self.context.absolute_url(), item['aliquot_type_name'])
            return url


    def updateWidgets(self):
        if self.update_schema is not None:
            if 'volume' in self.update_schema.keys():
                self.update_schema['volume'].widgetFactory = widgets.AmountFieldWidget
            if 'cell_amount' in self.update_schema.keys():
                self.update_schema['cell_amount'].widgetFactory = widgets.AmountFieldWidget
            if 'labbook' in self.update_schema.keys():
                self.update_schema['labbook'].widgetFactory = widgets.AmountFieldWidget                
            if 'freezer' in self.update_schema.keys():
                self.update_schema['freezer'].widgetFactory = widgets.StorageFieldWidget
            if 'rack' in self.update_schema.keys():
                self.update_schema['rack'].widgetFactory = widgets.StorageFieldWidget
            if 'box' in self.update_schema.keys():
                self.update_schema['box'].widgetFactory = widgets.StorageFieldWidget

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        session = named_scoped_session(SCOPED_SESSION_KEY)
        query = (
            session.query(
                model.Aliquot.id.label('id'),
                model.Patient.our.label('patient_our'),
                model.Patient.zid.label('patient_zid'),
                model.Cycle.title.label('cycle_title'),
                # model.Specimen.visit.visit_date.label('visit_date'),
                # model.Specimen.visit.zid.label('visit_zid'),
                model.AliquotType.id.label('aliquot_type'),
                model.AliquotType.name.label('aliquot_type_name'),
                model.Aliquot.labbook.label('labbook'),
                model.Aliquot.volume.label('volume'),
                model.Aliquot.cell_amount.label('cell_amount'),
                model.Aliquot.freezer.label('freezer'),
                model.Aliquot.rack.label('rack'),
                model.Aliquot.box.label('box'),
                model.Location.id.label('location'),
                model.Aliquot.notes.label('notes'),
                model.SpecialInstruction.id.label('special_instuction')
                )
                .select_from(model.Aliquot)
                .join(model.Specimen, (model.Specimen.id == model.Aliquot.specimen_id))
                .join(model.Patient, (model.Patient.id == model.Specimen.patient_id))
                .join(model.Cycle, (model.Cycle.id == model.Specimen.cycle_id))
                .join(model.AliquotType, (model.AliquotType.id == model.Aliquot.aliquot_type_id))
                .join(model.AliquotState, (model.AliquotState.id == model.Aliquot.state_id))
                .join(model.Location, (model.Location.id == model.Aliquot.location_id))
                .filter(model.AliquotState.name.in_(self.display_state))
                .order_by( model.Specimen.collect_date.desc(), model.Patient.our, model.AliquotType.name)
            )
        return SqlDictBatch(query)
        return [(1, {}),]

class ResearchLabViewForm(AliquotCoreForm):
    """
    Primary view for a clinical lab object.
    """

    # @property
    # def editform_factory(self):
    #     return SpecimenPendingButtons

    @property
    def display_state(self):
        return (u"checked-in",)

ResearchLabView = layout.wrap_form(ResearchLabViewForm)
