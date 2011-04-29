import os

from zope import component
from zope import schema
from zope.app.intid.interfaces import IIntIds
from zope.component import getSiteManager
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.site.hooks import getSite

from z3c.form import button
from z3c.form import field
from z3c.form import form as z3cform
from z3c.form.interfaces import DISPLAY_MODE

from five import grok
from Products.statusmessages.interfaces import IStatusMessage
from plone.directives import dexterity
from plone.directives import form
from plone.z3cform.crud import crud

from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import IAliquot as IDSAliquot
from avrc.data.store.interfaces import ISpecimen as IDSSpecimen
from avrc.data.store.interfaces import IVisit as IDSVisit

from avrc.aeh import MessageFactory as _
from avrc.aeh.browser import base
from avrc.aeh.browser.widget import StorageFieldWidget
from avrc.aeh.browser.form import NestedFormView
from avrc.aeh.browser.form import BatchNavigation
from avrc.aeh.browser.widget import TimeFieldWidget
from avrc.aeh.content import cycle
from avrc.aeh.content.visit import IVisit
from avrc.aeh.specimen import specimen
from avrc.aeh.specimen.aliquot import IAliquot
from avrc.aeh.specimen.specimen import ISpecimen
from avrc.aeh.specimen.vocabularies import SpecimenVocabulary
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

class FormRequestor(z3cform.Form):
    label=_(u'Enter Forms')
    ignoreContext=True

    def __init__(self,context,request):
        z3cform.Form.__init__(self,context,request)

    def update(self):
        context = self.context.aq_inner
        request_forms = schema.List(
            title=u'Optional Forms to Request',
            value_type=schema.Choice(
                vocabulary=context.getOptionalBehaviorFormVocabulary()
                )
            )
        request_forms.__name__ = 'request_forms'
        request_tests = schema.List(
            title=u'Optional Tests to Request',
            value_type=schema.Choice(
                vocabulary=context.getOptionalTestFormVocabulary()
                )
            )
        request_tests.__name__ = 'request_tests'
        self.fields += field.Fields(request_forms, request_tests)
        super(FormRequestor, self).update()

    @property
    def action(self):
        return self.context.absolute_url()

    @button.buttonAndHandler(_('Request More ...'),name='requestTests')
    def requestTests(self, action):
        data, errors = self.extractData()
        messages=IStatusMessage(self.request)
        if errors:
            messages.addStatusMessage(_(u'Please enter a visit date'),
                                      type='error'
                                      )
            return
        context = self.context.aq_inner
        site = getSite()
        sm = getSiteManager(site)
        ds = sm.queryUtility(IDatastore, 'fia')
        schema_manager = ds.schemata
        visit_manager = ds.visits
        requested_data = []
        requested_data.extend(data['request_tests'])
        requested_data.extend(data['request_forms'])
        newobjlist = []
        kwargs={'state':u'pending-entry'}
        for form in requested_data:
            newobj = ds.spawn(schema_manager.get(form), **kwargs)
            newobj = ds.put(newobj)
            newobjlist.append(newobj)

        visit_manager.add_instances(IDSVisit(context), newobjlist)
        notify(ObjectModifiedEvent(context))
        return self.request.response.redirect(context.absolute_url())

class View(dexterity.DisplayForm):
    grok.context(IVisit)
    grok.require('zope2.View')

    def __init__(self, context, request):
        super(View, self).__init__(context, request)
        self.form_requestor = self.getFormRequestor()
        self.cycles = self.listCycles()
        self.tests = context.getTestFormList()
        self.behaviorforms = context.getBehaviorFormList()



    def getFormRequestor(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = FormRequestor(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

    def listCycles(self):
        context = self.context.aq_inner
        cycles = context.getCycles()
        cyclelist=[]
        for cycle in cycles:
            studytitle = cycle.aq_parent.Title()

            cyclelist.append('%s, %s' % (studytitle, cycle.Title()))
        return cyclelist



class BehavioralAddForm(base.BaseAddForm):
    """ Base form for adding behavioral data """
    grok.context(IVisit)
    grok.name('addrecord')

    @property
    def action(self):
        return self.context.absolute_url() + '/@@addrecord?form=' + self.formid

class BehavioralUpdateForm(base.BaseUpdateForm):
    grok.context(IVisit)
    grok.name('editrecord')

    @property
    def action(self):
        id = self.recordid
        return self.context.absolute_url() + '/@@editrecord?record=' + id

class TestUpdateForm(base.BaseUpdateForm):
    grok.context(IVisit)
    grok.name('edittest')

    @property
    def action(self):
        id = self.recordid
        return self.context.absolute_url() + '/@@edittest?record=' + id


class BehavioralDisplayForm(base.BaseDisplayForm):
    grok.context(IVisit)
    grok.name('viewrecord')

    @property
    def action(self):
        id = self.recordid
        return self.context.absolute_url() + '/@@viewrecord?record=' + id

class TestDisplayForm(base.BaseDisplayForm):
    grok.context(IVisit)
    grok.name('viewtest')

    @property
    def action(self):
        id = self.recordid
        return self.context.absolute_url() + '/@@viewtest?record=' + id




# ------------------------------------------------------------------------------
# Specimen Form
# ------------------------------------------------------------------------------

class AliquotProtectionSubForm(crud.EditSubForm):

    def update(self):
        super(AliquotProtectionSubForm, self).update()

class SpecimenButtonManager(crud.EditForm):

    editsubform_factory = AliquotProtectionSubForm

    @button.buttonAndHandler(_('Save All Changes'), name='update')
    def handleUpdate(self, action):
        success = _(u'Successfully updated')
        partly_success = _(u'Some of your changes could not be applied.')
        status = no_changes = _(u'No changes made.')
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        specimen_manager = ds.specimen
        for subform in self.subforms:
            data, errors = subform.extractData()
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            self.context.before_update(subform.content, data)
            specimenobj = IDSSpecimen(subform.content)
            updated = False
            for prop, value in data.items():
                if hasattr(specimenobj, prop) and \
                        getattr(specimenobj, prop) != value:
                    setattr(specimenobj, prop, value)
                    updated = True
                    if status is no_changes:
                        status = success
            if updated:
                specimen_manager.put(specimenobj)

class SpecimenForm(crud.CrudForm):
    ignoreContext=True
    update_schema = field.Fields(ISpecimen, mode=DISPLAY_MODE).select(
                        'study_title',
                        'protocol_title',
                        'specimen_type',
                        'tube_type',)\
                    + field.Fields(ISpecimen).select(
                        'tubes',
                        'date_collected',
                        'time_collected',
                        'state',
                        'notes'
                        )
    addform_factory = crud.NullForm
    editform_factory = SpecimenButtonManager

    batch_size = 0

    @property
    def action(self):
        return os.path.join(self.context.absolute_url(), '@@visitspecimen')

    def updateWidgets(self):
        super(SpecimenForm, self).updateWidgets()
        self.update_schema['time_collected'].widgetFactory = TimeFieldWidget
        self.update_schema['tubes'].widgetFactory = StorageFieldWidget

    def get_items(self):
        visit = self.context.aq_inner
        specimenlist = []
        for specimen in visit.requestedSpecimen():
            specimenlist.append((specimen.dsid, specimen))
        return specimenlist

class SpecimenAddForm(z3cform.Form):
    label=_(u'Enter Forms')
    ignoreContext=True

    def __init__(self,context,request):
        z3cform.Form.__init__(self,context,request)

    def cycleVocabulary(self):
        context = self.context.aq_inner
        cycles = context.getCycles()
        termlist=[]
        intids = component.getUtility(IIntIds)
        for cycle in cycles:
            int
            studytitle = cycle.aq_parent.Title()
            cycletitle = '%s, %s' % (studytitle, cycle.Title())
            protocol_zid = intids.getId(cycle)
            termlist.append(SimpleTerm(
                                       title=cycletitle,
                                       token='%s' % protocol_zid,
                                       value=protocol_zid))
        return SimpleVocabulary(terms=termlist)

    def update(self):
        available_cycles = schema.Choice(
                           title=_(u'Available Study Protocol'),
                           description=_(u''),
                           source=self.cycleVocabulary()
                           )
        available_cycles.__name__ = 'available_cycles'

        self.fields += field.Fields(available_cycles)
        available_specimen = schema.Choice(
                           title=_(u'Available Specimen'),
                           description=_(u''),
                           source=SpecimenVocabulary()
                           )
        available_specimen.__name__ = 'available_specimen'
        self.fields += field.Fields(available_specimen)
        super(SpecimenAddForm, self).update()

    @property
    def action(self):
        return self.context.absolute_url()

    @button.buttonAndHandler(_('Request More ...'),name='requestTests')
    def requestTests(self, action):
        data, errors = self.extractData()
        messages=IStatusMessage(self.request)
        if errors:
            messages.addStatusMessageself(
                _(u'There was an error with your request.'),
                type='error'
                )
            return
        visit = self.context.aq_inner
        visit.addRequestedSpecimen(
            iface=data['available_specimen'],
            protocol_zid=data['available_cycles']
            )

        redirect_url = os.path.join(self.context.absolute_url(), '@@specimen')
        return self.request.response.redirect(redirect_url)

class SpecimenUpdateForm(dexterity.DisplayForm):
    grok.context(IVisit)
    grok.require('zope2.View')
    grok.name('specimen')

    def __init__(self, context, request):
        super(SpecimenUpdateForm, self).__init__(context, request)
        self.specimen = self.getSpecimen()
        self.cycles = self.listCycles()
        self.requestspecimen = self.requestSpecimen()

    def getSpecimen(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = SpecimenForm(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

    def requestSpecimen(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = SpecimenAddForm(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

    def listCycles(self):
        context = self.context.aq_inner
        cycles = context.getCycles()
        cyclelist=[]
        for cycle in cycles:
            studytitle = cycle.aq_parent.Title()
            cyclelist.append('%s, %s' % (studytitle, cycle.Title()))
        return cyclelist

# ------------------------------------------------------------------------------
# Aliquot
# ------------------------------------------------------------------------------
#
class AliquotButtonManager(crud.EditForm):

    editsubform_factory = AliquotProtectionSubForm

    def render_batch_navigation(self):
        navigation = BatchNavigation(self.batch, self.request)
        def make_link(page):
            return '%s?%spage=%s' % (self.request.getURL(), self.prefix, page)
        navigation.make_link = make_link
        return navigation()

    @button.buttonAndHandler(_('Save All Changes'), name='update')
    def handleUpdate(self, action):
        success = _(u'Successfully updated')
        partly_success = _(u'Some of your changes could not be applied.')
        status = no_changes = _(u'No changes made.')
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        aliquot_manager = ds.aliquot
        for subform in self.subforms:
            data, errors = subform.extractData()
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            self.context.before_update(subform.content, data)
            aliquotobj = IDSAliquot(subform.content)
            updated = False
            for prop, value in data.items():
                if hasattr(aliquotobj, prop) and \
                        getattr(aliquotobj, prop) != value:
                    setattr(aliquotobj, prop, value)
                    updated = True
                    if status is no_changes:
                        status = success
            if updated:
                aliquot_manager.put(aliquotobj)

class AliquotForm(crud.CrudForm):
    ignoreContext=True
    update_schema = field.Fields(IAliquot, mode=DISPLAY_MODE).select(
                        'aliquot_id',
                        'patient_title',
                        'study_title',
                        'protocol_title',
                        'aliquot_type',
                        )\
                    + field.Fields(IAliquot).select(
                        'volume',
                        'cell_amount',
                        'store_date',
                        'freezer',
                        'rack',
                        'box',
                        'state',
                        'notes',
                        'special_instruction'
                        )
    addform_factory = crud.NullForm
    editform_factory = AliquotButtonManager

    batch_size = 20

    @property
    def action(self):
        return os.path.join(self.context.absolute_url(), '@@aliquotupdateform')

    def updateWidgets(self):
        super(AliquotForm, self).updateWidgets()
        self.update_schema['volume'].widgetFactory = StorageFieldWidget
        self.update_schema['cell_amount'].widgetFactory = StorageFieldWidget
        self.update_schema['freezer'].widgetFactory = StorageFieldWidget
        self.update_schema['rack'].widgetFactory = StorageFieldWidget
        self.update_schema['box'].widgetFactory = StorageFieldWidget

    def get_items(self):
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        aliquotlist=[]
        aliquot_manager = ds.aliquot
        intids = component.getUtility(IIntIds)
        patient = self.context.aq_parent
        patient_zid = intids.getId(patient)
        for cycle in self.context.cycles:
            kwargs = dict(protocol_zid=cycle.to_id, subject_zid=patient_zid)
            for aliquotobj in aliquot_manager.list_aliquot_by_group(**kwargs):
                newAliquot = IAliquot(aliquotobj)
                aliquotlist.append((aliquotobj.dsid, newAliquot))
        return aliquotlist

class AliquotUpdateForm(dexterity.DisplayForm):
    grok.context(IVisit)
    grok.require('zope2.View')
    grok.name('aliquot')

    def __init__(self, context, request):
        super(AliquotUpdateForm, self).__init__(context, request)
        self.aliquot = self.getAliquot()
        self.cycles = self.listCycles()

    def getAliquot(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotForm(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view

    def listCycles(self):
        context = self.context.aq_inner
        cycles = context.getCycles()
        cyclelist=[]
        for cycle in cycles:
            studytitle = cycle.aq_parent.Title()
            cyclelist.append('%s, %s' % (studytitle, cycle.Title()))
        return cyclelist
