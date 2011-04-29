from Products.CMFCore.utils import getToolByName

from plone.directives import dexterity

from zope.security import checkPermission

from five import grok

from avrc.aeh import MessageFactory as _
from avrc.aeh.browser.aliquotform import AliquotRequestor
from avrc.aeh.browser.aliquotform import AliquotByOUR
from avrc.aeh.browser.clinicallabform import SpecimenRequestor
from avrc.aeh.browser.form import NestedFormView
from avrc.aeh.browser.labelprintform import AliquotLabelPrinter
from avrc.aeh.browser.labelprintform import AliquotLabelRePrinter
from avrc.aeh.browser.specimenaliquotform import SpecimenToAliquotor
from avrc.aeh.browser.specimenlabform import SpecimenAliquotor
from avrc.aeh.content.institute import IInstitute


class View(dexterity.DisplayForm):
    """ Main View
    """
    grok.context(IInstitute)
    grok.require('avrc.aeh.ViewInstitute')

    def canAddPatient(self):
        return checkPermission('avrc.aeh.AddPatient', self.context)


    def canSearchPatients(self):
        return checkPermission('avrc.aeh.ViewPatient', self.context)


    def findPatientsOrEnrollments(self):
        request = self.context.REQUEST
        results=[]
        if request and request.has_key('search_terms'):
            search_terms = request['search_terms']
            if search_terms == '':
                return []
            catalog = getToolByName(self.context, 'portal_catalog')
            searchbyour = catalog(portal_type='avrc.aeh.patient',
                                  getId=search_terms)
            if searchbyour and len(searchbyour):
                if len(searchbyour) == 1:
                    request.response.redirect(searchbyour[0].getURL())
                else:
                    for result in searchbyour:
                        if result not in results:
                            results.append(result)
                    results.extend(searchbyour)
            results.extend(catalog(portal_type='avrc.aeh.patient',
                                   initials=search_terms.upper()))
            results.extend(catalog(portal_type='avrc.aeh.patient',
                                   aeh_number=search_terms))
            results.extend(catalog(portal_type='avrc.aeh.enrollment',
                                   enrollment_identifier=search_terms))
        return results

# 
# class ClinicalLabView(dexterity.DisplayForm):
#     grok.context(IInstitute)
#     grok.require('avrc.aeh.ViewClinicalSpecimen')
#     grok.name('clinicallab')
# 
#     def __init__(self, context, request):
#         super(ClinicalLabView, self).__init__(context, request)
#         self.specimen_requestor = self.getFormRequestor()
# 
# 
#     def getFormRequestor(self):
#         """
#         Create a form instance.
#         @return: z3c.form wrapped for Plone 3 view
#         """
#         context = self.context.aq_inner
#         form = SpecimenRequestor(context, self.request)
#         view = NestedFormView(context,self.request)
#         view = view.__of__(context)
#         view.form_instance=form
#         return view


class SpecimenLabView(dexterity.DisplayForm):
    grok.context(IInstitute)
    grok.require('avrc.aeh.ViewClinicalSpecimen')
    grok.name('specimenlab')


    def __init__(self, context, request):
        super(SpecimenLabView, self).__init__(context, request)
        self.specimens = self.getFormRequestor()
        self.specimen_aliquotor = self.getFormAliquotRequestor()
        self.aliquotbyour = self.getAliquotRequestor()
        self.aliquotlabels = self.getAliquotLabels()


    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = SpecimenAliquotor(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view


    def getFormAliquotRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = SpecimenToAliquotor(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view


    def getAliquotLabels(self):
        context = self.context.aq_inner
        form = AliquotLabelPrinter(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view


    def getAliquotRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotByOUR(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view


class AliquotLabView(dexterity.DisplayForm):
    grok.context(IInstitute)
    grok.require('avrc.aeh.ViewClinicalSpecimen')
    grok.name('aliquotlab')

    def __init__(self, context, request):
        super(AliquotLabView, self).__init__(context, request)
        self.aliquot_requestor = self.getFormRequestor()
        self.aliquotbyour = self.getAliquotRequestor()
        self.aliquotlabels = self.getAliquotLabels()


    def getAliquotRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotByOUR(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view


    def getFormRequestor(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = AliquotRequestor(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view


    def getAliquotLabels(self):
        context = self.context.aq_inner
        form = AliquotLabelRePrinter(context, self.request)
        view = NestedFormView(context,self.request)
        view = view.__of__(context)
        view.form_instance=form
        return view


    def ourNumberFilter(self):
        if self.request.has_key('our') and self.request['our'] is not None:
            return self.request['our']
        session_manager = getToolByName(self.context,'session_data_manager')
        session = session_manager.getSessionData(create=False)
        if session and session.has_key('ournumkey'):
            if session['ournumkey'] is not None:
                return session['ournumkey']
