from AccessControl import getSecurityManager
from Products.statusmessages.interfaces import IStatusMessage
from avrc.data.store.interfaces import IDataStore
from beast.browser import widgets
from datetime import date
from five import grok
from hive.lab import MessageFactory as _, \
                      utilities as utils, \
                     SCOPED_SESSION_KEY
from hive.lab.browser import buttons
from hive.lab.interfaces.aliquot import IAliquot, \
                                        IAliquotGenerator, \
                                        IAliquotSupport, \
                                        IViewableAliquot, \
                                        IAliquotFilterForm, \
                                        IInventoryFilterForm
from hive.lab.interfaces.lab import IFilter, \
                                    IFilterForm, \
                                    IResearchLab
from hive.lab.interfaces.labels import ILabelPrinter, \
                                       ILabel
from hive.lab.interfaces.managers import IAliquotManager, \
                                         ISpecimenManager
from hive.lab.interfaces.specimen import IBlueprintForSpecimen, \
                                         IViewableSpecimen, \
                                         ISpecimen, \
                                         ISpecimenSupport, \
                                         ISpecimenFilterForm
from plone.directives import form
from plone.z3cform.crud import crud
from z3c.form import button, \
                     field, \
                     form as z3cform
from z3c.form.interfaces import DISPLAY_MODE
from z3c.saconfig import named_scoped_session
from zope.app.intid.interfaces import IIntIds
from zope.schema.vocabulary import SimpleTerm, \
                                   SimpleVocabulary
from zope.security import checkPermission
import datetime
import os.path
import zope.component
import zope.interface
import zope.schema

# ------------------------------------------------------------------------------
# Base Forms |
# --------------
# These classes provide the various transitions and modifications of the pages
# that support and modify specimen
# ------------------------------------------------------------------------------

        
# ------------------------------------------------------------------------------
# Form for requesting aditional specimen for a particular visit.
# ------------------------------------------------------------------------------

class SpecimenAddForm(z3cform.Form):
    label = _(u'Add Specimen')
    ignoreContext = True

    def __init__(self, context, request):
        super(SpecimenAddForm, self).__init__(context, request)
        self.redirect_url = os.path.join(context.absolute_url(), '@@specimen')

    @property
    def currentUser(self):
        return getSecurityManager().getUser().getId()
        
    def specimenVocabulary(self):
        context = self.context.aq_inner
        termlist = []
        intids = zope.component.getUtility(IIntIds)
        subject_zid = intids.getId(context.aq_parent)
        date_collected = context.visit_date
        for cycle in context.cycles:
            cycle_obj = cycle.to_object
            study = cycle_obj.aq_parent
            study_title = study.Title()
            cycle_title = cycle_obj.Title()

            for related_blueprint in study.related_specimen:
                blueprint = related_blueprint.to_object
                term_title = '%s, %s -- %s' % (study_title, cycle_title, blueprint.Title())
                specimen = blueprint.createSpecimen(subject_zid, cycle.to_id, date_collected)
                termlist.append(SimpleTerm(
                                       title=term_title,
                                       token='%s' % term_title,
                                       value=specimen))
        return SimpleVocabulary(terms=termlist)

    def update(self):
        available_specimen = zope.schema.List(
            title=_(u'Available Specimen'),
            value_type=zope.schema.Choice(
                           title=_(u'Available Specimen'),
                           description=_(u''),
                           source=self.specimenVocabulary()
                           )
            )
        available_specimen.__name__ = 'available_specimen'
        self.fields += field.Fields(available_specimen)
        super(SpecimenAddForm, self).update()

    @button.buttonAndHandler(_('Request More Specimen'), name='requestSpecimen',
    condition=lambda self: checkPermission('hive.lab.RequestSpecimen', self.context))
    def requestSpecimen(self, action):
        specimen_manager = ISpecimenManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
        data, errors = self.extractData()
        messages = IStatusMessage(self.request)
        if errors:
            messages.addStatusMessage(
                _(u'There was an error with your request.'),
                type='error'
                )
            return
        for specimen in data['available_specimen']:
            specimen_manager.put(specimen)

        return self.request.response.redirect(self.redirect_url)

# ------------------------------------------------------------------------------
# Label Queue Listing
# ------------------------------------------------------------------------------
class LabelForm(crud.CrudForm):
    """
    """
    def __init__(self, context, request):
        super(LabelForm, self).__init__(context, request)
        self.labeler = ILabelPrinter(context)

    editform_factory = buttons.LabelButtons
    ignoreContext = True
    addform_factory = crud.NullForm

    batch_size = 80

    view_schema = field.Fields(ILabel).\
        select('dsid', 'patient_title', 'study_title',
       'protocol_title', 'pretty_type', 'date')

    def get_items(self):
        brainz = self.labeler.getLabelBrains()
        labellist = []
        for label in brainz:
            labellist.append((label.getPath(), label))
        return labellist

