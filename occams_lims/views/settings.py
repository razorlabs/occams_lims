from sqlalchemy import orm
from pyramid.httpexceptions import HTTPFound
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import wtforms

from occams_lims import _, models


@view_config(
    route_name='lims.settings',
    permission='admin',
    renderer='../templates/settings/settings.pt'
)
def settings(context, request):
    """
    Manages application-wide settings
    """

    if request.method == 'POST':
        check_csrf_token(request)

    db_session = request.db_session

    specimen_types_query = (
        db_session.query(models.SpecimenType)
        .order_by(models.SpecimenType.title))

    specimen_types_count = specimen_types_query.count()

    aliquot_types_query = (
        db_session.query(models.AliquotType)
        .options(orm.joinedload('specimen_type'))
        .join(models.AliquotType.specimen_type)
        .order_by(
            models.SpecimenType.title,
            models.AliquotType.title))

    aliquot_types_count = specimen_types_query.count()

    # We need to accomodate WTForm's inability to process multiple forms
    # in the same page by adding a hidden value to check which form
    # was submitted

    specimen_type_add_form = SpecimenTypeForm(
        request.POST if 'specimen-type-add-form' in request.POST else None,
    )

    specimen_type_crud_form = SpecimenTypeCrudForm(
        request.POST if 'specimen-type-crud-form' in request.POST else None,
        types=specimen_types_query,
    )

    aliquot_type_add_form = AliquotTypeForm(
        request.POST if 'aliquot-type-add-form' in request.POST else None
    )

    aliquot_type_crud_form = AliquotTypeCrudForm(
        request.POST if 'aliquot-type-crud-form' in request.POST else None,
        types=aliquot_types_query,
    )

    if 'specimen-type-add-form' in request.POST \
            and specimen_type_add_form.validate():
        pass

    elif 'specimen-type-crud-form' in request.POST \
            and specimen_type_crud_form.validate():
        pass

    elif 'specimen-type-delete-form' in request.POST:
        pass

    elif 'aliquot-type-add-form' in request.POST \
            and aliquot_type_add_form.validate():
        pass

    elif 'aliquot-type-add-form' in request.POST \
            and aliquot_type_crud_form.validate():
        pass

    elif 'aliquot-type-delete-form' in request.POST:
        pass

    return {
        'specimen_types': specimen_types_query,
        'specimen_types_count': specimen_types_count,
        'specimen_type_add_form': specimen_type_add_form,
        'specimen_type_crud_form': specimen_type_crud_form,

        'aliquot_types': aliquot_types_query,
        'aliquot_types_count': aliquot_types_count,
        'aliquot_type_add_form': aliquot_type_add_form,
        'aliquot_type_crud_form': aliquot_type_crud_form,
    }


class SpecimenTypeForm(wtforms.Form):

    ui_selected = wtforms.BooleanField()

    id = wtforms.HiddenField()

    title = wtforms.StringField(
        label=_(u'Title'),
        description=_(u'The displayed label'),
        validators=[
            wtforms.validators.input_required(),
        ])

    description = wtforms.TextAreaField(
        label=_(u'Description'),
        validators=[wtforms.validators.optional()])

    tube_type = wtforms.StringField(
        label=_(u'Tube Type'),
        validators=[wtforms.validators.optional()])

    default_tubes = wtforms.IntegerField(
        label=_(u'Default Amount'),
        description=_(
            u'Default amount to use by default when creating a new specimen'),
        validators=[wtforms.validators.optional()])


class SpecimenTypeCrudForm(wtforms.Form):

    types = wtforms.FieldList(wtforms.FormField(SpecimenTypeForm))


class AliquotTypeForm(wtforms.Form):

    ui_selected = wtforms.BooleanField()

    id = wtforms.HiddenField()

    specimen_type_id = wtforms.SelectField(
        choices=[],
        validators=[
            wtforms.validators.input_required()
        ])

    title = wtforms.StringField(
        label=_(u'Title'),
        validators=[
            wtforms.validators.input_required(),
        ])

    description = wtforms.TextAreaField(
        label=_(u'Description'),
        validators=[wtforms.validators.optional()])

    tube_type = wtforms.StringField(
        label=_(u'Tube Type'),
        validators=[wtforms.validators.optional()])

    units = wtforms.StringField(
        label=_(u'Units'),
        validators=[wtforms.validators.input_required()])


class AliquotTypeCrudForm(wtforms.Form):

    types = wtforms.FieldList(wtforms.FormField(AliquotTypeForm))
