from zope import schema
from zope.app.pagetemplate import viewpagetemplatefile

from z3c.form import field
from z3c.form.interfaces import INPUT_MODE

from plone.z3cform.layout import FormWrapper
from plone.z3cform.widget import singlecheckboxwidget_factory
from plone.z3cform.crud import crud

from hive.lab import MessageFactory as _

class NestedFormView(FormWrapper):
    """
    Subclass FormWrapper so that we can use custom frame template.
    """
    index = viewpagetemplatefile.ViewPageTemplateFile("templates/nestedform.pt")


class PreselectedEditSubForm(crud.EditSubForm):

    def _select_field(self):
        select_field = field.Field(
            schema.Bool(__name__='select',
                             required=False,
                             title=_(u'select'),
                             default=True))
        select_field.widgetFactory[INPUT_MODE] = singlecheckboxwidget_factory
        return select_field


class wrappableAddForm(crud.AddForm):
    """
    Needed to make crud play with plone.app.z3cform (which provides kss)
    """
    template = viewpagetemplatefile.ViewPageTemplateFile('templates/crud-add.pt')



class BatchNavigation(crud.BatchNavigation):
    template = viewpagetemplatefile.ViewPageTemplateFile('templates/batch.pt')