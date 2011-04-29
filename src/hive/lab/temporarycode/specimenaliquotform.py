from zope.component import getSiteManager

from z3c.form import field
from z3c.form import button
from z3c.form.interfaces import DISPLAY_MODE

from Products.CMFCore.utils import getToolByName
from plone.z3cform.crud import crud

from avrc.aeh import MessageFactory as _
from avrc.aeh.specimen import aliquot
from avrc.data.store.interfaces import IAliquot as IDSAliquot
from avrc.data.store.interfaces import IDatastore
from avrc.aeh.browser import widget
from avrc.aeh.specimen.specimen import IAliquotableSpecimen
#===============================================================================
# Experimental Lab # 2
#===============================================================================

class SpecimenToAliquotManager(crud.EditForm):
    label=_(u"")
    @button.buttonAndHandler(_('Aliquot and Label Selected'), name='aliquot')
    def handleAliquot(self, action):
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Aliquot.")
            return
        success = _(u"Successfully Aliquoted")
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = _(u"No Aliquot Entered.")
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        aliquot_manager = ds.aliquot
        
#        session_manager=getToolByName(self.context,'session_data_manager')
#        session = session_manager.getSessionData(create=True)
        label_printer = self.context.context.label_printer
#        if not session.has_key('labels'):
#            session['labels']=[]
        for subform in self.subforms:
            obj = subform.content
            count = 0
            data, errors = subform.extractData()
            aliquotlist=[]
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            if not data['select'] or not data['aliquot_count']:
                continue
            for prop, value in data.items():
                if prop == 'select':
                    continue
                elif prop == 'aliquot_count':
                    count = value
                elif hasattr(obj, prop):
                    setattr(obj, prop, value)
            for i in range(count):
                newaliquot = aliquot_manager.put(IDSAliquot(obj))
                aliquotlist.append(newaliquot)
                parts = []

                if obj.cell_amount:
                    parts.append("%sx10^6" % obj.cell_amount)

                if obj.volume:
                    parts.append("%smL" % obj.volume)
                if obj.special_instruction and obj.special_instruction != u'na':
                    parts.append(obj.special_instruction)
                    
                labeldata={'study':obj.study_title,
                           'week':obj.protocol_title,
                           'date':obj.store_date,
                           'our': obj.patient_title,
                           'aliquot': unicode(1000000 + int(newaliquot.dsid)),
                           'type':"%s %s" % (newaliquot.type, " ".join(parts))}
                
                label = aliquot.AliquotLabel(**labeldata)
                label_printer.catalog_object(label, uid=str(label.aliquot))
#                session['labels'].append(label)
            if status is no_changes:
                status = success

        self.status = status

    @button.buttonAndHandler(_('Complete Selected Specimen'), name='readied')
    def handlePrepared(self, action):
        selected = self.selected_items()
        if selected:
            sm = getSiteManager(self)
            ds = sm.queryUtility(IDatastore, 'fia')
            specimen_manager = ds.specimen
            for id, obj in selected:
                specimenobj = specimen_manager.get(obj.specimen_dsid)
                setattr(specimenobj, 'state', unicode('aliquoted'))

                newspecimen = specimen_manager.put(specimenobj)

        self.status = _(u"The Specimen has been marked as Complete")
        return self.request.response.redirect(self.action)

class SpecimenToAliquotor(crud.CrudForm):
    ignoreContext=True
    newmanager = field.Fields(aliquot.IAliquot).select('aliquot_count')

    newmanager += field.Fields(aliquot.IAliquot, mode=DISPLAY_MODE).\
                  select('patient_title', 'patient_legacy_number',
                         'study_title', 'protocol_title', 'aliquot_type')
    newmanager += field.Fields(aliquot.IAliquot).\
                  select('volume', 'cell_amount', 'store_date','freezer',
                         'rack', 'box', 'notes', 'special_instruction')

    update_schema = newmanager
    addform_factory = crud.NullForm
    editform_factory = SpecimenToAliquotManager

    batch_size = 0

    @property
    def action(self):
        return self.context.absolute_url() + '@@/specimenlab'

    def updateWidgets(self):
        super(SpecimenToAliquotor, self).updateWidgets()
        self.update_schema['aliquot_count'].widgetFactory = widget.StorageFieldWidget
        self.update_schema['volume'].widgetFactory = widget.AmountFieldWidget
        self.update_schema['cell_amount'].widgetFactory = widget.AmountFieldWidget
        self.update_schema['freezer'].widgetFactory = widget.StorageFieldWidget
        self.update_schema['rack'].widgetFactory = widget.StorageFieldWidget
        self.update_schema['box'].widgetFactory = widget.StorageFieldWidget

    def get_items(self):
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        aliquotlist=[]
        specimen_manager = ds.specimen
        count = 100
        for specimenobj in specimen_manager.list_by_state('prepared-aliquot'):
            for aliquot_obj in IAliquotableSpecimen(specimenobj).aliquot():
                newAliquot = aliquot.IAliquot(aliquot_obj)
                aliquotlist.append((count, newAliquot))
                count = count + 1
        return aliquotlist
