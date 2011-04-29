import os
from zope.component import getSiteManager

from z3c.form import field
from z3c.form import button
from z3c.form.interfaces import DISPLAY_MODE

from plone.z3cform.crud import crud

from avrc.aeh import MessageFactory as _
from avrc.aeh.specimen.specimen import ISpecimen

from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import ISpecimen as IDSSpecimen

# ------------------------------------------------------------------------------
# Experimental Lab View
# ------------------------------------------------------------------------------

class SpecimenAliquotManager(crud.EditForm):

    label = None

    @button.buttonAndHandler(_('Ready Selected'), name='readied')
    def handlePrepared(self, action):
        selected = self.selected_items()
        if selected:
            sm = getSiteManager(self)
            ds = sm.queryUtility(IDatastore, 'fia')
            specimen_manager = ds.specimen
            for id, specimenobj in selected:
                specimenobj = IDSSpecimen(specimenobj)
                setattr(specimenobj, 'state', unicode('prepared-aliquot'))
                newspecimen = specimen_manager.put(specimenobj)
            self.status = _(u"Your specimen have been Prepared.")
        else:
            self.status = _(u"Please select specimen to aliquot.")
        return self.request.response.redirect(self.context.action)

    @button.buttonAndHandler(_('Reject Selected'), name='reject')
    def handleReject(self, action):
        selected = self.selected_items()
        if selected:
            sm = getSiteManager(self)
            ds = sm.queryUtility(IDatastore, 'fia')
            specimen_manager = ds.specimen
            for id, specimenobj in selected:
                specimenobj = IDSSpecimen(specimenobj)
                setattr(specimenobj, 'state', unicode('rejected'))

                newspecimen = specimen_manager.put(specimenobj)
            self.status = _(u"Your specimen have been rejected.")
        else:
            self.status = _(u"Please select specimen to aliquot.")
        self._update_subforms()

class SpecimenAliquotor(crud.CrudForm):
    ignoreContext=True
    update_schema = field.Fields(ISpecimen, mode=DISPLAY_MODE).select(
                        'patient_title',
                        'patient_legacy_number',
                        'study_title',
                        'protocol_title',
                        'specimen_type',
                        'tube_type',
                        'tubes',
                        'date_collected',
                        'time_collected' ,
                        'notes'
                        )
    addform_factory = crud.NullForm
    editform_factory = SpecimenAliquotManager
    batch_size = 0

    @property
    def action(self):
        return os.path.join(self.context.absolute_url(), '@@specimenlab')

    def update(self):
        super(SpecimenAliquotor, self).update()

    def get_items(self):
        sm = getSiteManager(self)
        ds = sm.queryUtility(IDatastore, 'fia')
        specimenlist=[]
        specimen_manager = ds.specimen
        for specimenobj in specimen_manager.list_by_state('pending-aliquot'):
            newSpecimen = ISpecimen(specimenobj)
            specimenlist.append((specimenobj.dsid, newSpecimen))
        return specimenlist
