import os
from zope import schema
from zope.component import getSiteManager

from z3c.form import field
from z3c.form import button
from z3c.form import form as z3cform
from z3c.form.interfaces import DISPLAY_MODE

from Products.CMFCore.utils import getToolByName

from plone.z3cform.crud import crud

from avrc.aeh import MessageFactory as _
from avrc.aeh.browser.form import BatchNavigation
from avrc.aeh.browser.form import PreselectedEditSubForm
from avrc.aeh.browser.widget import AmountFieldWidget
from avrc.aeh.browser.widget import StorageFieldWidget

from avrc.aeh.specimen.aliquot import IAliquot
from avrc.aeh.specimen.aliquot import AliquotLabel

from avrc.data.registry.utility import unformat
from avrc.data.store.interfaces import IAliquot as IDSAliquot
from avrc.data.store.interfaces import IDatastore
from zope.interface import Invalid

class NoLocation(Invalid):
    __doc__ = _(u"The aliquot does not have a location")

# ------------------------------------------------------------------------------
# Aliquots
# ------------------------------------------------------------------------------
from pprint import pprint
class AliquotButtonManager(crud.EditForm):

    label = _(u"Aliquot")
    editsubform_factory = PreselectedEditSubForm

    def render_batch_navigation(self):
        navigation = BatchNavigation(self.batch, self.request)
        def make_link(page):
            return "%s?%spage=%s" % (self.request.getURL(), self.prefix, page)
        navigation.make_link = make_link
        return navigation()

    @button.buttonAndHandler(_('Save All Changes'), name='update')
    def handleUpdate(self, action):
        success = _(u"Successfully updated")
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = _(u"No changes made.")
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
                if hasattr(aliquotobj, prop):
                    if  getattr(aliquotobj, prop) != value:
                        setattr(aliquotobj, prop, value)
                        updated = True
                        status = success
            if updated:
                aliquot_manager.put(aliquotobj)
        self.status = status

    @button.buttonAndHandler(_('Create Labels for Selected'), name='print')
    def handlePrint(self, action):
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Print.")
            return
        label_printer = self.context.context.label_printer


        for id, newaliquot in selected:
            parts = []
            obj = IAliquot(newaliquot)
            if obj.cell_amount:
                parts.append("%sx10^6" % obj.cell_amount)
            if obj.volume:
                parts.append("%smL" % obj.volume)
            if obj.special_instruction and obj.special_instruction != u'na':
                parts.append(obj.special_instruction)

            labeldata={
                'study':obj.study_title,
                'week':obj.protocol_title,
                'date':obj.store_date,
                'our': obj.patient_title,
                'aliquot': unicode(1000000 + int(newaliquot.dsid)),
                'type':"%s %s" % (newaliquot.aliquot_type, " ".join(parts))
                }
            label = AliquotLabel(**labeldata)
            label_printer.catalog_object(label, uid=str(label.aliquot))

#            session['relabels'].append(label)

    @button.buttonAndHandler(_('Check-in Selected'), name='checkin')
    def handleComplete(self, action):
        success = _(u"Successfully updated")
        partly_success = _(u"Some of your changes could not be applied.")
        self.status = no_changes = _(u"No changes made.")
        self.handleUpdate(self, action)
        if self.status != no_changes and self.status != success:
            return
        selected = self.selected_items()
        if selected:
            sm = getSiteManager(self)
            ds = sm.queryUtility(IDatastore, 'fia')
            aliquot_manager = ds.aliquot
            self.status = _(u"Your aliquot have been checked in.")
            for id, aliquotobj in selected:
                aliquotobj = aliquot_manager.get(id)
                if aliquotobj.freezer is None or aliquotobj.freezer == '' or \
                aliquotobj.rack is None or aliquotobj.rack == '' or \
                aliquotobj.box is None or aliquotobj.box == '':
                    self.status = _(u"A Check In of an aliquot was attempted "
                                    u"with no location data.That aliquot was "
                                    u"not checked in. Please review the aliquot "
                                    u"below.")
                else:
                    setattr(aliquotobj, 'state', unicode('checked-in'))
                    aliquotobj = aliquot_manager.put(aliquotobj)
        else:
            self.context.status = _(u"Please select an aliquot.")
        self._update_subforms()

    @button.buttonAndHandler(_('Mark Selected unused'), name='unused')
    def handleReject(self, action):
        #self.handleUpdate(self, action)
        selected = self.selected_items()
        if selected:
            sm = getSiteManager(self)
            ds = sm.queryUtility(IDatastore, 'fia')
            aliquot_manager = ds.aliquot
            for id, aliquotobj in selected:
                aliquotobj = IDSAliquot(aliquotobj)
                setattr(aliquotobj, 'state', unicode('unused'))

                aliquotobj = aliquot_manager.put(aliquotobj)
            self.status = _(u"Your aliquot have been marked unused.")
        else:
            self.status = _(u"Please select an aliquot.")
        self._update_subforms()

class AliquotRequestor(crud.CrudForm):

    ignoreContext=True
    update_schema = field.Fields(IAliquot, mode=DISPLAY_MODE).select(
                        'aliquot_id',
                        'patient_title',
                        'patient_legacy_number',
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
                        'notes'
                        )\
                    + field.Fields(IAliquot, mode=DISPLAY_MODE).select(
                        'special_instruction'
                        )
    addform_factory = crud.NullForm
    editform_factory = AliquotButtonManager
    batch_size = 20

    @property
    def action(self):
        return os.path.join(self.context.absolute_url(), '@@aliquotlab')

    def updateWidgets(self):
        super(AliquotRequestor, self).updateWidgets()
        self.update_schema['volume'].widgetFactory = AmountFieldWidget
        self.update_schema['cell_amount'].widgetFactory = AmountFieldWidget
        self.update_schema['freezer'].widgetFactory = StorageFieldWidget
        self.update_schema['rack'].widgetFactory = StorageFieldWidget
        self.update_schema['box'].widgetFactory = StorageFieldWidget

    def get_items(self):
        request = self.request
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        aliquotlist = []
        aliquot_manager = ds.aliquot
        session_manager = getToolByName(self.context,'session_data_manager')
        session = session_manager.getSessionData(create=True)

        # Figure out from the request which form we are looking to input
        if (request.has_key('our') and request['our'] is not None) or \
           (session.has_key('ournumkey') and session['ournumkey'] is not None):
            if request.has_key('our') and request['our'] is not None:
                session['ournumkey'] = request['our']

            our_id = unformat(session['ournumkey'])
            if our_id is None:
                self.status = u"Sorry. We couldn't find that patient."
                aliquotables = aliquot_manager.list_by_state(state='pending')

            else:
                kwargs = dict(state=u'pending', our_id=our_id)
                aliquotables = aliquot_manager.list_by_state(**kwargs)
        else:
            aliquotables = aliquot_manager.list_by_state(state=u'pending')

        for aliquotobj in aliquotables:
            aliquotlist.append((aliquotobj.dsid, IAliquot(aliquotobj)))
        return aliquotlist

# ------------------------------------------------------------------------------
# Aliquot by OUR #
# ------------------------------------------------------------------------------

class AliquotByOUR(z3cform.Form):
    """ Form to select a cycle to view. This is to reduce the crazy
        navigation
    """

    ignoreContext=True

    def update(self):
        ournum = schema.TextLine(
            title=_(u"Enter an OUR#"),
            description=_(u"Enter an OUR# and press GO to show aliquots for "
                          u"only this OUR Number"),
            )

        ournum.__name__ = "our"
        self.fields += field.Fields(ournum)
        super(AliquotByOUR, self).update()

    @property
    def action(self):
        """ Rewrite HTTP POST action.
            If the form is rendered embedded on the others pages we
            make sure the form is posted through the same view always,
            instead of making HTTP POST to the page where the form was rendered.
        """
        return os.path.join(self.context.absolute_url(), "@@aliquotlab")

    @button.buttonAndHandler(_('Go'),name='go')
    def goToAliquot(self, action):
        """ Form button hander. """
        data, errors = self.extractData()
        if errors:
            self.status=_(u"Sorry. That our number is not recognized")
            return
        redirect_url = "%s?our=%s" % (self.action, data['our'])
        return self.request.response.redirect(redirect_url)

    @button.buttonAndHandler(_('Show All'),name='showall')
    def getAllAliquot(self, action):
        """ Form button hander. """
        session_manager = getToolByName(self.context,'session_data_manager')
        session = session_manager.getSessionData(create=True)
        session.invalidate()
        return self.request.response.redirect(self.action)
