
from occams.lab import MessageFactory as _, \
                     SCOPED_SESSION_KEY
from z3c.form.interfaces import DISPLAY_MODE

from z3c.saconfig import named_scoped_session
from z3c.form import button, field, form as z3cform
from beast.browser.crud import NestedFormView
from occams.datastore import model as dsmodel
from AccessControl import getSecurityManager

from occams.lab import model
from Products.Five.browser import BrowserView
from datetime import date
from occams.lab import interfaces
from plone.z3cform.crud import crud
from zope.app.intid.interfaces import IIntIds
import zope.component
from beast.browser import widgets
from occams.lab.browser.specimen import SpecimenCoreButtons
from occams.lab.browser.specimen import SpecimenCoreForm
from occams.lab.browser.aliquot import AliquotButtonCore
from occams.lab.browser.aliquot import AliquotCoreForm
from occams.lab.browser.base import LabelForm
from collective.beaker.interfaces import ISession
from occams.lab.browser.aliquot import AliquotFilterForm
from datetime import timedelta
from sqlalchemy import or_
from sqlalchemy.orm import object_session
from Products.CMFCore.utils import getToolByName
from occams.lab.browser.base import FilterFormCore
from occams.lab.browser.aliquot import AliquotQueueForm
SUCCESS_MESSAGE = _(u"Successfully updated")
PARTIAL_SUCCESS = _(u"Some of your changes could not be applied.")
NO_CHANGES = _(u"No changes made.")

class ReadySpecimenButtons(SpecimenCoreButtons):
    label = _(u"")

    @property
    def prefix(self):
        return 'specimen-ready.'

    @button.buttonAndHandler(_('Ready selected'), name='ready')
    def handleCompleteDraw(self, action):
        pass
        self.changeState(action, 'pending-aliquot', 'ready')        
        return self.request.response.redirect(self.action)

class ReadySpecimenForm(SpecimenCoreForm):

    @property
    def view_schema(self):
        fields = field.Fields(interfaces.IViewableSpecimen).\
            select('patient_our',
             'cycle_title',
             'tube_type',
             'specimen_type_name',)
        fields += field.Fields(interfaces.ISpecimen).\
            select(
             'tubes',
             'collect_date', 
             'collect_time',
             'notes')            
        return fields

    @property
    def edit_schema(self):
        return None

    @property
    def editform_factory(self):
        return ReadySpecimenButtons

    @property
    def display_state(self):
        return (u"complete", )

class ResearchLabView(BrowserView):
    """
    Primary view for a research lab object.
    """
 
    def labUrl(self):
        return self.context.absolute_url()

    def listAliquotTypes(self):
        session = named_scoped_session(SCOPED_SESSION_KEY)
        query = (
            session.query(model.AliquotType)
            .order_by(model.AliquotType.title.asc())
            )

        for aliquot_type in iter(query):
            url = "%s/%s/%s" %(self.labUrl(), aliquot_type.specimen_type.name, aliquot_type.name)
            yield {'url': url, 'title': aliquot_type.title}

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = ReadySpecimenForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getPreview(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        session = named_scoped_session(SCOPED_SESSION_KEY)
        query = (
            session.query(model.Specimen)
                .join(model.Patient)
                .join(model.Cycle)
                .join(model.Visit)
                .join(model.SpecimenType)
                .join(model.SpecimenState)
                .filter(model.SpecimenState.name.in_((u'pending-draw',)))
                .order_by( model.Visit.visit_date.desc(), model.SpecimenType.name, model.Patient.our)
            )
        for entry in iter(query):
            yield entry

class AliquotCreator(crud.EditForm):
    """
    """
    label = _(u"")
    @property
    def prefix(self):
        return 'aliquot-creator.'
        
    def changeState(self, action, state, acttitle):
        """
        Change the state of a specimen based on the id pulled from a template 
        """
        selected = self.selected_items()
        session = named_scoped_session(SCOPED_SESSION_KEY)
        state = session.query(model.SpecimenState).filter_by(name='aliquoted').one()
        if selected:
            for id, aliquottemplate in selected:
                aliquottemplate.specimen.state =state
            session.flush()
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
        session = named_scoped_session(SCOPED_SESSION_KEY)
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
            count = data.pop('count')
            changes = subform.applyChanges(data)
            kwargs = subform.content
            kwargs['state'] = session.query(model.AliquotState).filter_by(name = 'pending').one()
            kwargs['inventory_date'] = kwargs['store_date']
            # clean up the dictionary
            for field in ['patient_legacy_number', 'cycle_title', 'patient_our','select']:
                if field in kwargs.keys():
                    del kwargs[field]
            while count:
                newAliquot = model.Aliquot(**kwargs)
                session.add(newAliquot)
                count = count -1
            session.flush()
            if status is no_changes:
                status = success
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Specimen Complete'), name='complete')
    def handleCompleteSpecimen(self, action):
        self.changeState(action, 'aliquoted', 'completed')
        
        return self.request.response.redirect(self.action)

class AliquotReadyForm(AliquotCoreForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """
    editform_factory = AliquotCreator

    @property
    def edit_schema(self):
        fields = field.Fields(interfaces.IAliquotGenerator).\
        select('count')
        fields += field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('patient_our',
                     'patient_legacy_number', 
                     'cycle_title', 
                     'aliquot_type_title'
                     )
        fields += field.Fields(interfaces.IAliquot).\
            select('labbook',
                      'volume',
                     'cell_amount', 
                     'store_date', 
                     'freezer', 
                     'rack', 
                     'box',
                     'special_instruction',
                     'notes')
        return fields

    @property
    def display_state(self):
        return (u'pending-aliquot', )

    def updateWidgets(self):
        self.update_schema['count'].widgetFactory = widgets.StorageFieldWidget
        super(AliquotReadyForm, self).updateWidgets()

    def link(self, item, field):
        if field == 'patient_our':
            intids = zope.component.getUtility(IIntIds)
            patient = intids.getObject(item['specimen'].patient.zid)
            url = '%s/specimen' % patient.absolute_url()
            return url
        elif field == 'cycle_title' and getattr(item['specimen'].visit, 'zid', None):
            intids = zope.component.getUtility(IIntIds)
            visit = intids.getObject(item['specimen'].visit.zid)
            url = '%s/aliquot' % visit.absolute_url()
            return url

    def get_query(self):
        session = named_scoped_session(SCOPED_SESSION_KEY)
        specimenQ = (
            session.query(model.Specimen)
            .join(model.SpecimenState)
            .filter(model.SpecimenState.name.in_(self.display_state))
            )
        return specimenQ

    def get_items(self):
        """
        Use a special ``get_item`` method to return a query instead for batching
        """
        if getattr(self, '_aliquotList', None):
            return self._aliquotList
        session = named_scoped_session(SCOPED_SESSION_KEY)
        specimenQ = self.get_query()
        self._aliquotList = []
        i = 0
        for specimen in iter(specimenQ):
            types = session.query(model.AliquotType).filter(model.AliquotType.specimen_type == specimen.specimen_type)
            viewableSpecimen = interfaces.IViewableSpecimen(specimen)
            for aliquotType in types:
                newAliquot = {
                'patient_our':viewableSpecimen.patient_our,
                'patient_legacy_number':specimen.patient.legacy_number, 
                'cycle_title': viewableSpecimen.cycle_title,
                'specimen':specimen,
                'aliquot_type':aliquotType,
                'store_date':date.today(),
                'location': aliquotType.location
                }
                self._aliquotList.append((i, newAliquot))
                i = i + 1
        return self._aliquotList

class AliquotReadyView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotReadyForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def labUrl(self):
        return self.context.absolute_url()

class AliquotPreparedButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-prepared.'

    @button.buttonAndHandler(_('Print Selected'), name='print')
    def handlePrintAliquot(self, action):
        self.saveChanges(action)
        self.queueLabels(action)
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Check In Aliquot'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-in', 'Checked In')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Aliquot Unused'), name='unused')
    def handleUnusedAliquot(self, action):
        selected = self.selected_items()
        session = named_scoped_session(SCOPED_SESSION_KEY)
        if selected:
            for id, data in selected:
                aliquot = session.query(model.Aliquot).filter_by(id=id).one()
                session.delete(aliquot)
        session.flush()
        return self.request.response.redirect(self.action)

class AliquotPreparedForm(AliquotCoreForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """
    batch_size = 20
    editform_factory = AliquotPreparedButtons
    
    @property
    def display_state(self):
        return (u'pending', )


    def get_query(self):
        query = super(AliquotPreparedForm, self).get_query()
        browsersession  = ISession(self.request)
        if 'patient' in browsersession.keys():
            query = query.join(model.Specimen.patient).filter(or_(model.Patient.has(our=browsersession['patient']), model.Patient.has(legacy_number=browsersession['patient'])))
        return query

class AliquotPreparedView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotPreparedForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getLabelForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = LabelForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view
        
    def getFilterForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotFilterForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form

    def labUrl(self):
        return self.context.absolute_url()

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

class AliquoEditForm(AliquotCoreForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """
    batch_size = 20
    editform_factory = AliquotEditButtons
    
    @property
    def display_state(self):
        return (u'incorrect', )

class AliquotEditView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquoEditForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def labUrl(self):
        return self.context.absolute_url()

class AliquotHoldButtons(AliquotButtonCore):
    """
    """
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-hold.'
        
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

class AliquotCheckoutForm(AliquotCoreForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """
    batch_size = 20
    editform_factory = AliquotHoldButtons

    @property
    def edit_schema(self):
        fields = field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select('id')
        fields = field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('patient_our',
                     'patient_legacy_number',
                      'cycle_title', 
                      'aliquot_type_title',
                       'vol_count',)
        fields += field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select('store_date')
        fields += field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('frb', 
                    'special_instruction_title')
        fields += field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select('notes')

        fields += field.Fields(interfaces.IAliquot).\
            select('sent_date', 'sent_name', 'location', 'sent_notes')
        return fields

    def get_query(self):
        session = named_scoped_session(SCOPED_SESSION_KEY)
        current_user = session.query(dsmodel.User).filter_by(key = getSecurityManager().getUser().getId()).one()
        query = super(AliquotCheckoutForm, self).get_query()
        query = query.filter(model.Aliquot.modify_user_id == current_user.id)
        return query

    @property
    def display_state(self):
        return (u'pending-checkout', )

class AliquotCheckoutView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotCheckoutForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getQueueForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotQueueForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def labUrl(self):
        return self.context.absolute_url()

class AliquotRecoverButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-prepared.'

    @button.buttonAndHandler(_('Print Selected'), name='print')
    def handlePrintAliquot(self, action):
        self.saveChanges(action)
        self.queueLabels(action)
        return self.request.response.redirect(self.action)


    @button.buttonAndHandler(_('Recover Aliquot'), name='recover')
    def handleRecoverAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'pending', 'Checked In')
        
        return self.request.response.redirect(self.action)

class AliquotRecoverForm(AliquotCoreForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """
    batch_size = 20
    editform_factory = AliquotPreparedButtons
    
    @property
    def display_state(self):
        return (u'checked-in', 'unused')

    @property
    def view_schema(self):
        fields = field.Fields(interfaces.IAliquot).\
            select('id')
        fields += field.Fields(interfaces.IViewableAliquot).\
            select('state_title',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title',
                     'vol_count', 
                     )
        fields += field.Fields(interfaces.IAliquot).\
            select('store_date')
        fields += field.Fields(interfaces.IViewableAliquot).\
            select('frb',
                     'special_instruction_title'
                     )
        fields += field.Fields(interfaces.IAliquot).\
            select('notes')
        return fields

    edit_schema = None

    def get_query(self):
        query = super(AliquotRecoverForm, self).get_query()
        yesterday =  date.today() - timedelta(1)
        query = query.filter(model.Aliquot.modify_date >= yesterday )
        return query

class AliquotRecoverView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotRecoverForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getLabelForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = LabelForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def labUrl(self):
        return self.context.absolute_url()

class AliquotCheckInButtons(AliquotButtonCore):
    label = _(u"")
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-prepared.'

    @button.buttonAndHandler(_('Print Selected'), name='print')
    def handlePrintAliquot(self, action):
        self.saveChanges(action)
        self.queueLabels(action)
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Save Changes'), name='save')
    def handleSaveChanges(self, action):
        self.saveChanges(action)
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Check In Aliquot'), name='checkin')
    def handleCheckinAliquot(self, action):
        self.saveChanges(action)
        self.changeState(action, 'checked-in', 'Checked In')
        
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Mark Aliquot Unused'), name='unused')
    def handleUnusedAliquot(self, action):
        selected = self.selected_items()
        session = named_scoped_session(SCOPED_SESSION_KEY)
        if selected:
            for id, data in selected:
                aliquot = session.query(model.Aliquot).filter_by(id=id).one()
                session.delete(aliquot)
        session.flush()
        return self.request.response.redirect(self.action)

class AliquotCheckInForm(AliquotCoreForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """
    batch_size = 20
    editform_factory = AliquotCheckInButtons

    @property
    def edit_schema(self):
        fields = field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('aliquot_id',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title'
                     )
        fields += field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select('labbook',
                     'store_date', 
                     'special_instruction',
                     'sent_date',
                     'sent_name',
                     'sent_notes',
                    )
        fields += field.Fields(interfaces.IAliquot).\
            select('location',
                      'thawed_num',
                     'freezer', 
                     'rack', 
                     'box',
                     'notes')
        return fields

    @property
    def display_state(self):
        return (u'checked-out', )

    def get_query(self):
        query = super(AliquotCheckInForm, self).get_query()
        browsersession  = ISession(self.request)
        if 'patient' in browsersession.keys():
            query = query.join(model.Specimen.patient).filter(or_(model.Patient.has(our=browsersession['patient']), model.Patient.has(legacy_number=browsersession['patient'])))
        return query

class AliquotCheckInView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotCheckInForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getFilterForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotFilterForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def labUrl(self):
        return self.context.absolute_url()

class AliquotInventoryButtons(AliquotButtonCore):
    """
    """
    z3cform.extends(AliquotButtonCore)

    @property
    def prefix(self):
        return 'aliquot-inventory.'
        
    @button.buttonAndHandler(_('Mark Inventoried'), name='inventory')
    def handleInventory(self, action):
        session = named_scoped_session(SCOPED_SESSION_KEY)
        selected = self.selected_items()
        if selected:
            for id, obj in selected:
                setattr(obj, 'inventory_date',date.today())
                session.flush()
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

class AliquotInventoryForm(AliquotCoreForm):
    """
    Base Crud form for editing specimen. Some specimen will need to be
    """
    batch_size = 20
    editform_factory = AliquotInventoryButtons

    @property
    def edit_schema(self):
        fields = field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('aliquot_id',
                     'patient_our',
                     'patient_legacy_number',
                     'cycle_title',
                     'aliquot_type_title',
                     'vol_count'
                     )
        fields += field.Fields(interfaces.IAliquot, mode=DISPLAY_MODE).\
            select('labbook',
                     'store_date', 
                     'inventory_date',
                    )
        fields += field.Fields(interfaces.IViewableAliquot, mode=DISPLAY_MODE).\
            select('frb',
                      'special_instruction_title',
                    )
        return fields

    @property
    def display_state(self):
        return (u'checked-in', )

    def get_query(self):
        query = super(AliquotInventoryForm, self).get_query()
        browsersession  = ISession(self.request)
        if 'patient' in browsersession.keys():
            query = query.join(model.Specimen.patient).filter(or_(model.Patient.has(our=browsersession['patient']), model.Patient.has(legacy_number=browsersession['patient'])))
        if 'after_date' in browsersession.keys():
            if 'before_date' in browsersession.keys():
                query = query.filter(model.Aliquot.store_date >= browsersession['after_date'])
                query = query.filter(model.Aliquot.store_date <= browsersession['before_date'])
            else:
                query = query.filter(model.Aliquot.store_date == browsersession['after_date'])
        if 'aliquot_type' in browsersession.keys():
            query = query.filter(model.AliquotType.name == browsersession['aliquot_type'])
        if 'freezer' in browsersession.keys():
                query = query.filter(model.Aliquot.freezer==browsersession['freezer'])
        if 'rack' in browsersession.keys():
                query = query.filter(model.Aliquot.rack == browsersession['rack'])
        if 'box' in browsersession.keys():
                query = query.filter(model.Aliquot.box == browsersession['box'])
        if 'inventory_date' in browsersession.keys():
            query = query.filter(or_(model.Aliquot.inventory_date == None, model.Aliquot.inventory_date < browsersession['inventory_date']))
        if self.display_state and not browsersession.get('show_all', False):
            query = query.filter(model.AliquotState.name.in_(self.display_state))       
        return query

class InventoryFilterForm(FilterFormCore):
    """
    """
    @property
    def fields(self):
        if hasattr(self.context, 'omit_filter'):
            omitables = self.context.omit_filter
            return field.Fields(interfaces.IInventoryFilterForm).omit(*omitables)
        return field.Fields(interfaces.IInventoryFilterForm)


    def updateWidgets(self):
        super(InventoryFilterForm, self).updateWidgets()
        if self.fields is not None:
            if 'freezer' in self.fields.keys():
                self.fields['freezer'].widgetFactory = widgets.StorageFieldWidget
            if 'rack' in self.fields.keys():
                self.fields['rack'].widgetFactory = widgets.StorageFieldWidget
            if 'box' in self.fields.keys():
                self.fields['box'].widgetFactory = widgets.StorageFieldWidget

class AliquotInventoryView(BrowserView):
    """
    Primary view for a research lab object.
    """
    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotInventoryForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def getFilterForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = InventoryFilterForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def labUrl(self):
        return self.context.absolute_url()