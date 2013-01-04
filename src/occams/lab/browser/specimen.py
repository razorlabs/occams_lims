
from occams.lab import MessageFactory as _
# from occams.lab.browser import crud

from z3c.form import button, field
from Products.Five.browser import BrowserView

from occams.lab import interfaces
from occams.lab import model
import zope.schema

from plone.z3cform import layout

from occams.lab.browser import common
from Products.statusmessages.interfaces import IStatusMessage
from zope.schema.vocabulary import SimpleTerm, \
                                   SimpleVocabulary
import os
from avrc.aeh import interfaces as clinical

from occams.lab import Session

from plone.z3cform.crud import crud
import z3c.form

class AliquotTypeAddForm(crud.AddForm):
    label = _(u"Add Aliquot Type")


class AliquotTypeEditForm(crud.EditForm):
    label = _(u"Aliquot Types")

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

    @z3c.form.button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        return self.status

class AliquotTypeForm(crud.CrudForm):
    """
    Primary view for a clinical lab object.
    """
    label = _(u"Aliquot Types")
    description = _(u"")

    ignoreContext = True

    addform_factory = AliquotTypeAddForm

    editform_factory =  AliquotTypeEditForm

    add_schema = z3c.form.field.Fields(interfaces.IAliquotType).select('title', )
    update_schema = z3c.form.field.Fields(interfaces.IAliquotType).select('title', )

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        query = (
                 Session.query(model.AliquotType)
                 .filter(model.AliquotType.specimen_type == self.context.item)
                 .order_by(model.AliquotType.title.asc())
                 )
        return [(aliq.id, aliq) for aliq in iter(query)]



class SpecimenTypeEditForm(z3c.form.form.EditForm):
    """
    Form for editing the properties of a specimen
    """
    fields = z3c.form.field.Fields(interfaces.ISpecimenType).select('title','tube_type', 'default_tubes')

    def getContent(self):
        return self.context.item

WrappedSpecimenTypeEditForm = layout.wrap_form(SpecimenTypeEditForm)


class SpecimenEditView(BrowserView):
    """
    View of a specimen type. Allows editing of
    """
    @property
    def edit_specimen_type_form(self):
        specimen_edit_form = WrappedSpecimenTypeEditForm(self.context, self.request)
        specimen_edit_form.update()
        return specimen_edit_form

    @property
    def crud_form(self):
        if not hasattr(self, '_v_crud_form'):
            self._v_crud_form = AliquotTypeForm(self.context, self.request)
            self._v_crud_form.update()
        return self._v_crud_form

    @property
    def list_aliquot_types(self):
        query = (
            Session.query(model.AliquotType)
            .filter(model.AliquotType.specimen_type == self.context.item)
            .order_by(model.AliquotType.title.asc())
            )
        for aliquot_type in iter(query):
            url = "./%s/%s" %(self.context.item.name, aliquot_type.name)
            yield {'url': url, 'title': aliquot_type.title}




class SpecimenViewForm(common.OccamsCrudForm):
    """
    Primary view for a clinical lab object.
    """
    label = _(u"Specimen")

    batch_size = 20

    # editform_factory =  ClinicalLabEditForm

    @property
    def edit_schema(self):
        fields = z3c.form.field.Fields(interfaces.ISpecimen, mode=z3c.form.interfaces.DISPLAY_MODE).\
                    select('state',
                            )
        fields += z3c.form.field.Fields(interfaces.IViewableSpecimen, mode=z3c.form.interfaces.DISPLAY_MODE).\
                    select('patient_our',
                             'patient_initials',
                             'cycle_title',
                             )
        fields += z3c.form.field.Fields(interfaces.ISpecimen, mode=z3c.form.interfaces.DISPLAY_MODE).\
                    select('specimen_type',
                             'tubes',
                             'collect_date',
                             'collect_time',
                             'location',
                             'notes'
                             )
        return fields

    # def updateWidgets(self):
    #     if self.update_schema is not None:
    #         if 'collect_time' in self.update_schema.keys():
    #             self.update_schema['collect_time'].widgetFactory = widgets.TimeFieldWidget
    #         if 'tubes' in self.update_schema.keys():
    #             self.update_schema['tubes'].widgetFactory = widgets.StorageFieldWidget


    # def before_update(self, content, data):
    #     location = Session.query(model.Location).filter_by(name = self.context.location).one()
    #     data['previous_location'] = location

    def _getQuery(self):
        # multiadapter defined in filters.py
        specimenfilter = zope.component.getMultiAdapter((self.context, self.request),interfaces.ISpecimenFilter)
        return specimenfilter.getQuery(default_state='pending-draw')


class SpecimenAddForm(z3c.form.form.Form):
    label = _(u'Add Specimen')
    ignoreContext = True

    def specimenVocabulary(self):
        ## get the terms for our Vocabulary
        context = self.context.aq_inner
        termlist = []
        for cycle in context.cycles:
            for specimen_type in cycle.study.specimen_types:
                term_title =u"%s -- %s" % (cycle.title, specimen_type.title)
                termlist.append(
                    SimpleTerm(
                        title= term_title,
                        token=str(term_title),
                        value=(cycle, specimen_type)
                        )
                    )
        return SimpleVocabulary(terms=termlist)

    def update(self):
        request_specimen = zope.schema.List(
            title=_(u'Available Specimen'),
            value_type=zope.schema.Choice(
                           title=_(u'Available Specimen'),
                           description=_(u''),
                           source=self.specimenVocabulary()
                           )
            )
        request_specimen.__name__ = 'request_specimen'
        self.fields = field.Fields(request_specimen)
        super(SpecimenAddForm, self).update()

    @button.buttonAndHandler(_('Request More Specimen'), name='requestSpecimen')
    def requestSpecimen(self, action):
        data, errors = self.extractData()
        messages = IStatusMessage(self.request)
        if errors:
            messages.addStatusMessage(
                _(u'There was an error with your request.'),
                type='error'
                )
            return
        drawstate = Session.query(model.SpecimenState).filter_by(name=u'pending-draw').one()
        visit = zope.component.getMultiAdapter((self.context, Session), clinical.IClinicalModel)
        for cycle, specimen_type in data['request_specimen']:
            newSpecimen = model.Specimen(
                    patient = visit.patient,
                    cycle = cycle,
                    specimen_type = specimen_type,
                    state=drawstate,
                    collect_date = visit.visit_date,
                    location_id = visit.patient.site.lab_location.id,
                    tubes = specimen_type.default_tubes
                )
            Session.add(newSpecimen)
            Session.flush()
        return self.request.response.redirect(os.path.join(self.context.absolute_url(), '@@specimen'))

WrappedSpecimenAddForm = layout.wrap_form(SpecimenAddForm)

class SpecimenView(BrowserView):
    """
    View of a specimen type. Allows editing of
    """
    instructions = [
        # {'title':'Select All',
        # 'description': 'Select or deselect all items displayed on the current page.'},
        # {'title':'Toggle Print Queue',
        # 'description': 'Saves all changes, and then adds the selected specimen to the print queue'},
        # {'title':'Print Labels',
        # 'description': 'Prints labels for the specimen in the print queue'},
        # {'title':'Save All Changes',
        # 'description': 'Saves all of the changes entered to the database. This applies ' \
        # 'to all specimen, not just selected specimen.'},
        # {'title':'Complete Selected',
        # 'description': 'Saves all changes entered to the database (for all specimen). Then ' \
        # 'marks the selected specimen as complete. If the location you\'ve entered for the items ' \
        # 'is the current lab, you will find them <a href="./ready">ready to aliquot</a>'},
        # {'title':'Mark Selected Undrawn',
        # 'description': 'Mark the selected specimen as undrawn.'},
        # {'title':'Add Specimen',
        # 'description': 'Adds a new specimen. This action DOES NOT save current changes.'},
      ]


    @property
    def entry_count(self):
        if not hasattr(self, '_v_crud_form'):
            self._v_crud_form = SpecimenViewForm(self.context, self.request)
            self._v_crud_form.update()
        return self._v_crud_form.count

    @property
    def crud_form(self):
        if not hasattr(self, '_v_crud_form'):
            self._v_crud_form = SpecimenViewForm(self.context, self.request)
            self._v_crud_form.update()
        return self._v_crud_form

    @property
    def add_form(self):
        if not hasattr(self, '_v_add_form'):
            self._v_add_form = WrappedSpecimenAddForm(self.context, self.request)
            self._v_add_form.update()
        return self._v_add_form
