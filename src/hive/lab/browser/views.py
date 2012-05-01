

        
# ------------------------------------------------------------------------------
# Crud Forms
# ------------------------------------------------------------------------------

class AliquotList(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IAliquotSupport)
    grok.require('hive.lab.ViewAliquot')
    grok.name('aliquot')

    def __init__(self, context, request):
        super(AliquotList, self).__init__(context, request)

        self.crudform = self.getCrudForm()
        self.filter = self.filterAliquot()
        self.aliquotqueue = self.aliquotQueue()
        self.lab_url = self.labUrl()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotListForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view
# 
    def filterAliquot(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotFilterForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def aliquotQueue(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.AliquotQueueForm(context, self.request)
        if hasattr(form, 'get_items') and not len(form.get_items()):
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def labUrl(self):
        url = './'
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.search({'portal_type':'hive.lab.researchlab'})
        if len(brains):
            url = brains[0].getURL()
        return url
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class AliquotCheckList(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IChecklistSupport)
    grok.require('hive.lab.ViewAliquot')
    grok.name('checklist')

    def __init__(self, context, request):
        super(AliquotCheckList, self).__init__(context, request)
        self.dsmanager = IAliquotManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
        self.getaliquot = self.getAliquot()
        self.currentUser = getSecurityManager().getUser().getId()

    def getAliquot(self):
        """
        Get me some aliquot
        """
        kw = {}
        kw['state'] = u'queued'
        kw['modify-name'] = self.currentUser
        for aliquot in self.dsmanager.filter_records(**kw):
            yield IViewableAliquot(aliquot)


class AliquotReceipt(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(IResearchLab)
    grok.require('hive.lab.ViewAliquot')
    grok.name('receipt')

    def __init__(self, context, request):
        super(AliquotReceipt, self).__init__(context, request)
        self.dsmanager = IAliquotManager(IDataStore(named_scoped_session(SCOPED_SESSION_KEY)))
        self.getaliquot = self.getAliquot()
        self.currentUser = getSecurityManager().getUser().getId()
        
    def getAliquot(self):
        """
        Get me some aliquot
        """
        
        kw = {}
        kw['state'] = u'pending-checkout'
        kw['modify-name'] = self.currentUser
        for aliquot in self.dsmanager.filter_records(**kw):
            yield IViewableAliquot(aliquot)

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class SpecimenSupport(dexterity.DisplayForm):
    """
    Primary view for a clinical lab object.
    """
    grok.context(ISpecimenSupport)
    grok.require('hive.lab.ViewSpecimen')
    grok.name('specimen')

    def __init__(self, context, request):
        super(SpecimenSupport, self).__init__(context, request)
        self.crudform = self.getCrudForm()
        self.filter = self.filterSpecimen()
        self.requestmore = self.requestSpecimen()

    def getCrudForm(self):
        """
        Create a form instance.
        @return: z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.SpecimenSupportForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def canRequestSpecimen(self):
        return hasattr(self.context, 'visit_date')

    def filterSpecimen(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        form = crud.SpecimenFilterForm(context, self.request)
        if hasattr(form, 'getCount') and form.getCount() < 1:
            return None
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

    def requestSpecimen(self):
        """ Create a form instance.
            Returns:
                z3c.form wrapped for Plone 3 view
        """
        context = self.context.aq_inner
        if not self.canRequestSpecimen():
            return None
        form = crud.SpecimenAddForm(context, self.request)
        view = NestedFormView(context, self.request)
        view = view.__of__(context)
        view.form_instance = form
        return view

