from cStringIO import StringIO

from z3c.form import field
from z3c.form import button
from z3c.form.interfaces import DISPLAY_MODE

from Products.CMFCore.utils import getToolByName

from plone.z3cform.crud import crud

from avrc.aeh import MessageFactory as _
from avrc.aeh.browser.form import PreselectedEditSubForm
from avrc.aeh.specimen import labels
from avrc.aeh.specimen import aliquot
from avrc.aeh.specimen.aliquot import IAliquotLabel

#===============================================================================
# Printables
#===============================================================================

class AliquotLabelManager(crud.EditForm):
    editsubform_factory = PreselectedEditSubForm
    label=_(u"")
    @button.buttonAndHandler(_('Print Selected'), name='print')
    def handlePrint(self, action):
        label_printer = self.context.context.label_printer

        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Print.")
            return
        stream = StringIO()
        labelWriter = labels.labelGenerator(labels.LCRY_1700, stream)
        for id, aliquot in selected:
            labelWriter.drawAnAliquotLabel(
                date="%s wk%s %s" % (aliquot.study, aliquot.week, aliquot.date.strftime("%m/%d/%Y")),
                PID=aliquot.our,
                aliquot=aliquot.aliquot,
                type=aliquot.type
                )
            label_printer.uncatalog_object(str(id))

        labelWriter.writeLabels()
        content = stream.getvalue()
        stream.close()

        self.request.RESPONSE.setHeader("Content-type","application/pdf")
        self.request.RESPONSE.setHeader("Content-disposition",
                                        "attachment;filename=labels.pdf")
        self.request.RESPONSE.setHeader("Cache-Control","no-cache")
        self.request.RESPONSE.write(content)

        self._update_subforms()
        self.status = _(u"You print is on its way. Refresh the page to view only unprinted labels.")
        return


    @button.buttonAndHandler(_('Refresh List'), name='refresh')
    def handleRefresh(self, action):
        return self.request.response.redirect(self.action)

    @button.buttonAndHandler(_('Remove Selected'), name='remove')
    def handleRemove(self, action):
        selected = self.selected_items()
        if not selected:
            self.status = _(u"Please select items to Remove.")
            return
        label_printer = self.context.context.label_printer
        for id, aliquoted in selected:
            label_printer.uncatalog_object(str(id))
        self._update_subforms()

    def _page(self):
        name = '%spage' % self.prefix
        return 0

class AliquotLabelPrinter(crud.CrudForm):
    ignoreContext=True
    newmanager = field.Fields(IAliquotLabel, mode=DISPLAY_MODE).\
                 select('aliquot','our','study','week','type','date')

    update_schema = newmanager
    addform_factory = crud.NullForm
    editform_factory = AliquotLabelManager
    LABEL_KEY = 'labels'
    batch_size = 0
    def __init__(self, context, request):
        super(AliquotLabelPrinter, self).__init__(context, request)
        self.LABEL_KEY = 'labels'

    @property
    def action(self):
        return self.context.absolute_url() + '@@/specimenlab'

    def get_items(self):
        label_printer = self.context.label_printer
        labellist=[]
        
        labels = None
        for labelbrain in label_printer():
            labeldata = {}
            #label = labelbrain.getObject()
            labeldata['aliquot'] = labelbrain['aliquot']
            labeldata['our'] = labelbrain['our']
            labeldata['date'] = labelbrain['date']
            labeldata['week'] = labelbrain['week']
            labeldata['study'] = labelbrain['study']
            labeldata['type'] = labelbrain['type']
            label = aliquot.AliquotLabel(**labeldata)
            labellist.append((int(label.aliquot), label))
        return labellist


class AliquotLabelRePrinter(AliquotLabelPrinter):
    def __init__(self, context, request):
        super(AliquotLabelRePrinter, self).__init__(context, request)
        self.LABEL_KEY = 'relabels'


