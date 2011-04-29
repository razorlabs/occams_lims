from datetime import date

from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility
import zope.schema

from Products.statusmessages.interfaces import IStatusMessage

from five import grok
from plone.dexterity.utils import createContentInContainer
from plone.directives import dexterity
from plone.directives import form
from plone.z3cform.crud import crud
from z3c.form import button, field
from z3c.form.interfaces import DISPLAY_MODE

from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import ISubject
from avrc.data.store.interfaces import ISpecimen as IDSSpecimen

from avrc.aeh import MessageFactory as _
from avrc.aeh.browser.base import BaseUpdateForm
from avrc.aeh.browser.form import NestedFormView
from avrc.aeh.content.patient import IPatient
from avrc.aeh.specimen.specimen import ISpecimen
from zope.event import notify
from zope.lifecycleevent import ObjectAddedEvent


class FormRequestor(form.Form):
    grok.context(IPatient)
    label=_(u'Enter Forms')
    description=_(u'Enter the date of the patient\'s visit. '
                  u'The system will gather the required forms, and '
                  u'guide you through collecting optional forms and '
                  u'test data.')

    ignoreContext=True

    def __init__(self ,context, request):
        super(FormRequestor, self).__init__(context, request)
        self.objcontext = context


    @property
    def fields(self):
        visit_date = zope.schema.Date(
            __name__ = 'visit_date',
            title=u'Date of Visit',
            default=date.today()
            )
        return field.Fields(visit_date)


    @property
    def action(self):
        """ Rewrite HTTP POST action.
            If the form is rendered embedded on the others pages we
            make sure the form is posted through the same view always,
            instead of making HTTP POST to the page where the form was rendered.
        """
        return self.context.absolute_url() + '/@@formrequestor'


    def getCycleList(self, currentDate=None):
        """ Get the list of all cycles the current patient should use for a
        """
        if currentDate is None:
            currentDate = date.today()
        cycles=[]
        for enrollment in self.context.getEnrollments():
            days = currentDate - enrollment.consent_date
            days = days.days
            last_visit_date = self.context.getLastVisitDate(currentDate)
            if last_visit_date is not None:
                last_visit = last_visit_date - enrollment.consent_date
                last_visit = last_visit.days
            else:
                last_visit = None
            cycles.extend(enrollment.getCurrentCycle(days, last_visit))
        return cycles


    @button.buttonAndHandler(_('Add a Visit'),name='addVisit')
    def addVisit(self, action):
        """ Form button hander.
        """
        data, errors = self.extractData()

        if errors:
            self.status = _(
                u'A visit cannot be added. Make sure that the '
                u'patient is enrolled in a study.'
                )
            return
        elif not len(self.getCycleList(data['visit_date'])):
            self.status = _(
                u'There doesn\'t seem to be a cycle on schedule for '
                u'this patient.'
                )
            return

        newobj = createContentInContainer(
            self.context,
            'avrc.aeh.visit',
            visit_date=data['visit_date']
            )
#        notify(ObjectAddedEvent(newobj))
        return self.request.response.redirect(newobj.absolute_url())


class View(grok.View):
    grok.context(IPatient)
    grok.require('avrc.aeh.ViewPatient')

    def __init__(self, context, request):
        super(View, self).__init__(context, request)
        self.form_requestor = self.getFormRequestor()


    def enrollments(self, context=None):
        if context is None:
            context = self.context
        return context.getEnrollments(all=True)


    def getFormRequestor(self):
        """ Create a form instance.
            @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = FormRequestor(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

    def visits(self, context=None):
        if context is None:
            context = self.context
        visits = []
        for obj in context.objectValues():
            if obj.portal_type == 'avrc.aeh.visit':
                visits.append(obj)
        for visit in visits:
            visitdict={}
            cycles = visit.getCycles()
            cyclelist = []
            for cycle in cycles:
                studytitle = cycle.aq_parent.Title()
                cyclelist.append('%s, %s' % (studytitle, cycle.Title()))
            visitdict['cycles'] = cyclelist
            visitdict['visit_date'] = visit.visit_date
            visitdict['visit_url'] = visit.absolute_url()
            visitdict['form_pending_entry'] = visit.getEnteredDataSummary(state=u'pending-entry', count=True)
            visitdict['form_pending_review'] = visit.getEnteredDataSummary(state=u'pending-review', count=True)
            visitdict['form_complete'] = visit.getEnteredDataSummary(state=u'complete', count=True)
            visitdict['form_not_done'] = visit.getEnteredDataSummary(state=u'not-done', count=True)
            yield visitdict

from plone.dexterity.utils import addContentToContainer
from plone.dexterity.utils import createContent

class AddPatient(dexterity.AddForm):
    grok.name('avrc.aeh.patient')
    enable_form_tabbing = False
    addlschema = ()
    grok.require('avrc.aeh.AddPatient')

#
    def __init__(self, context, request):
        super(AddPatient, self).__init__(context, request)
        ds_phi = getUtility(IDatastore, 'phi', context)
        schema_manager = ds_phi.getSchemaManager()
        self.addlschema = []
        for schema in ('IBio', 'IContact'):
            self.addlschema.append(schema_manager.get(schema))
        self.addlschema = tuple(self.addlschema)


    @property
    def additionalSchemata(self):
        return self.addlschema


    @button.buttonAndHandler(_('Save'), name='save')
    def handleAdd(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.groups=()

        processdict={u'IBio':{}, u'IContact':{}}
        mainobj={}
        for key, entry in data.items():
            if not key in self.schema.names():
                iface, ifacefield = key.split('.')
                processdict[iface][ifacefield] = entry
            else:
                mainobj[key] = entry

        obj = self.createAndAdd(mainobj)
        obj = self.context[obj.getId()]
        if obj is not None:
            self._finishedAdd = True
            IStatusMessage(self.request).addStatusMessage(_(u'Item created'), 'info')
            ds_phi = getUtility(IDatastore, 'phi', self.context)
            schema_manager = ds_phi.getSchemaManager()
            phi_subject_manager = ds_phi.getSubjectManager()
            newobjlist=[]

            for iface, dict in processdict.items():
                newobj = ds_phi.put(ds_phi.spawn(schema_manager.get(iface), **dict))
                newobjlist.append(newobj)

            phi_subject_manager.add_instances(ISubject(obj), newobjlist)
            obj.reindexObject(idxs=['initials',])

class NameUpdateForm(BaseUpdateForm):
    grok.context(IPatient)
    grok.name('updatename')

    def __init__(self, context, request):
        super(form.SchemaEditForm, self).__init__(context, request)

        self.dsname = 'phi'
        ds = getUtility(IDatastore, self.dsname, self.context)
        patient_manager = ds.getSubjectManager()
        self.contentobj = patient_manager.getEnteredDataOfType(ISubject(context), u'IBio')
        self.contentschema = self.contentobj.__schema__


    @property
    def label(self):
        return _(u'Patient Name')


    @property
    def action(self):
        return self.context.absolute_url() + '/@@updatename'


class ContactUpdateForm(BaseUpdateForm):
    grok.context(IPatient)
    grok.name('updatecontact')


    def __init__(self, context, request):
        super(form.SchemaEditForm, self).__init__(context, request)

        self.dsname = 'phi'
        ds = getUtility(IDatastore, self.dsname, self.context)
        patient_manager = ds.getSubjectManager()
        self.contentobj = patient_manager.getEnteredDataOfType(ISubject(context), u'IContact')
        self.contentschema = self.contentobj.__schema__


    @property
    def label(self):
        return _(u'Patient Contact Info')


    @property
    def action(self):
        return self.context.absolute_url() + '/@@updatecontact'


#===============================================================================
# specimen
#===============================================================================


#class AliquotProtectionSubForm(crud.EditSubForm):
#    """
#    """
#    def update(self):
#        super(AliquotProtectionSubForm, self).update()
#        if self.widgets['state'].value in [[u'aliquoted'],[u'prepared-aliquot'], [u'complete']]:
#            self.widgets['state'].mode = DISPLAY_MODE


class SpecimenButtonManager(crud.EditForm):
    """
    """
    pass
#    editsubform_factory = AliquotProtectionSubForm

    label=_(u'')
    @button.buttonAndHandler(_('Do Nothing'), name='update')
    def handleUpdate(self, action):
        success = _(u'Successfully did nothing')
#        partly_success = _(u'Some of your changes could not be applied.')
#        status = no_changes = _(u'No changes made.')
#        sm = getSiteManager(self)
#        ds = sm.queryUtility(IDatastore, 'fia')
#        specimen_manager = ds.specimen
#        for subform in self.subforms:
#            data, errors = subform.extractData()
#            if errors:
#                if status is no_changes:
#                    status = subform.formErrorsMessage
#                elif status is success:
#                    status = partly_success
#                continue
#            self.context.before_update(subform.content, data)
#            specimenobj = IDSSpecimen(subform.content)
#            updated = False
#            for prop, value in data.items():
#                if hasattr(specimenobj, prop) and getattr(specimenobj, prop) != value:
#                    setattr(specimenobj, prop, value)
#                    updated = True
#                    if status is no_changes:
#                        status = success
#            if updated:
#                newspecimen = specimen_manager.put(specimenobj)

class SpecimenForm(crud.CrudForm):
    ignoreContext=True
    newmanager = field.Fields(ISpecimen, mode=DISPLAY_MODE).\
    select('study_title', 'protocol_title','specimen_type', 'tube_type', 'tubes', 'date_collected', 'time_collected', 'state',  'notes')
    update_schema = newmanager
    addform_factory = crud.NullForm
    editform_factory = SpecimenButtonManager

    batch_size = 20


    @property
    def action(self):
        return self.context.absolute_url() + '@@/visitspecimen'


    def get_items(self):
        ds = getUtility(IDatastore, 'fia', self.context)
        specimenlist=[]
        specimen_manager = ds.specimen
        intids = getUtility(IIntIds, context=self.context)
        patient = self.context
        patient_zid = intids.getId(patient)
        kargs={}
        kargs['subject_zid'] = patient_zid
        if self.request.has_key('specimen_type') and self.request['specimen_type'] is not None:
            kargs['specimen_type'] = self.request['specimen_type']

        if self.request.has_key('state') and self.request['state'] is not None:
            kargs['state'] = self.request['state']

        for specimenobj in specimen_manager.list_specimen_by_group(**kargs):
            newSpecimen = ISpecimen(specimenobj)
            specimenlist.append((specimenobj.dsid, newSpecimen))
        return specimenlist


class SpecimenUpdateForm(dexterity.DisplayForm):
    grok.context(IPatient)
    grok.require('zope2.View')
    grok.name('specimen')


    def __init__(self, context, request):
        super(SpecimenUpdateForm, self).__init__(context, request)
        self.specimen = self.getSpecimen()


    def getSpecimen(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = SpecimenForm(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view
