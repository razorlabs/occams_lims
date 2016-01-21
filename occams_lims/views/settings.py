from slugify import slugify
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
                u'Default amount to use by default when '
                u'a new specimen'),
            validators=[wtforms.validators.optional()])

        def validate_title(self, field):
            query = (
                db_session.query(models.SpecimenType)
                .filter_by(name=slugify(field.data)))

            # apparently the removed field remains as None...
            if self.id and self.id.data:
                query.filter(models.SpecimenType.id != self.id.data)

            (exists,) = db_session.query(query.exists()).one()

            if exists:
                raise wtforms.validators.ValidationError(_(
                    'A type with a similar name already exists'))

    class SpecimenTypeCrudForm(wtforms.Form):

        types = wtforms.FieldList(wtforms.FormField(SpecimenTypeForm))

    class AliquotTypeForm(wtforms.Form):

        ui_selected = wtforms.BooleanField()

        id = wtforms.HiddenField()

        specimen_type_id = wtforms.SelectField(
            label=_(u'Specimen Type'),
            description=_(
                u'The specimen type this sample type can processed from'),
            choices=[(t.id, t.title) for t in specimen_types_query],
            coerce=int,
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

        units = wtforms.StringField(
            label=_(u'Measuring Units'),
            description=_(u'The unit of measurement per-sample of this type'),
            validators=[wtforms.validators.input_required()])

        def validate_title(self, field):
            query = (
                db_session.query(models.AliquotType)
                .filter_by(name=slugify(field.data)))

            # apparently the removed field remains as None...
            if self.id and self.id.data:
                query.filter(models.AliquotType.id != self.id.data)

            (exists,) = db_session.query(query.exists()).one()

            if exists:
                raise wtforms.validators.ValidationError(_(
                    'A type with a similar name already exists'))

    class AliquotTypeCrudForm(wtforms.Form):

        types = wtforms.FieldList(wtforms.FormField(AliquotTypeForm))

    # We need to accomodate WTForm's inability to process multiple forms
    # in the same page by adding a hidden value to check which form
    # was submitted

    specimen_type_add_form = SpecimenTypeForm(
        request.POST if 'specimen-type-add-form' in request.POST else None,
    )

    del specimen_type_add_form.id
    del specimen_type_add_form.ui_selected

    specimen_type_crud_form = SpecimenTypeCrudForm(
        request.POST if 'specimen-type-crud-form' in request.POST else None,
        types=specimen_types_query,
    )

    aliquot_type_add_form = AliquotTypeForm(
        request.POST if 'aliquot-type-add-form' in request.POST else None
    )

    del aliquot_type_add_form.id
    del aliquot_type_add_form.ui_selected

    aliquot_type_crud_form = AliquotTypeCrudForm(
        request.POST if 'aliquot-type-crud-form' in request.POST else None,
        types=aliquot_types_query,
    )

    if 'specimen-type-add-form' in request.POST:
        if specimen_type_add_form.validate():
            data = specimen_type_add_form.data
            data['name'] = slugify(data['title'])
            db_session.add(models.SpecimenType(**data))
            request.session.flash(
                _(u'Sucessfully added specimen type'), 'success')
            return HTTPFound(location=request.current_route_path())
        else:
            request.session.flash(
                _(u'Form errors, please revise below'), 'danger')

    elif 'specimen-type-crud-form' in request.POST:
        if specimen_type_crud_form.validate():
            pass
        else:
            pass

    elif 'specimen-type-delete-form' in request.POST:
        pass

    elif 'aliquot-type-add-form' in request.POST:
        if aliquot_type_add_form.validate():
            data = specimen_type_add_form.data
            data['name'] = slugify(data['title'])
            db_session.add(models.AliquotType(**data))
            request.session.flash(
                _(u'Sucessfully added aliquot type'), 'success')
            return HTTPFound(location=request.current_route_path())
        else:
            request.session.flash(
                _(u'Form errors, please revise below'), 'danger')

    elif 'aliquot-type-add-form' in request.POST:
        if aliquot_type_crud_form.validate():
            pass
        else:
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
