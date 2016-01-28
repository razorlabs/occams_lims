from slugify import slugify
from sqlalchemy import orm
from pyramid.httpexceptions import HTTPFound
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import wtforms

from occams.utils.forms import apply_changes
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

    specimen_types = (
        db_session.query(models.SpecimenType)
        .order_by(models.SpecimenType.title)
        .all())

    specimen_types_count = len(specimen_types)

    aliquot_types = (
        db_session.query(models.AliquotType)
        .options(orm.joinedload('specimen_type'))
        .join(models.AliquotType.specimen_type)
        .order_by(
            models.SpecimenType.title,
            models.AliquotType.title)
        .all())

    aliquot_types_count = len(specimen_types)

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
                query = query.filter(models.SpecimenType.id != self.id.data)

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
            choices=[(t.id, t.title) for t in specimen_types],
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
                query = query.filter(models.AliquotType.id != self.id.data)

            (exists,) = db_session.query(query.exists()).one()

            if exists:
                raise wtforms.validators.ValidationError(_(
                    'A type with a similar name already exists'))

    class AliquotTypeCrudForm(wtforms.Form):

        types = wtforms.FieldList(wtforms.FormField(AliquotTypeForm))

    class LabForm(wtforms.Form):
        name = wtforms.StringField(
            label=_(u'Name'),
            description=_(
                u'This is the system name'),
            validators=[wtforms.validators.Required()])
        title = wtforms.StringField(
            label=_(u'Title'),
            description=_(
                u'This is the human readable title'),
            validators=[wtforms.validators.Required()])
        active = wtforms.BooleanField(
            description=_(
                u'Actives labs will be available in new location dropdowns'),
            label=_(u'Active'))
        is_enabled = wtforms.BooleanField(
            description=_(
                u'Enabled labs will be available on Lims homepage'),
            label=_(u'Enabled'))

    # We need to accomodate WTForm's inability to process multiple forms
    # in the same page by adding a hidden value to check which form
    # was submitted

    lab_add_form = LabForm(
        request.POST if 'lab_add_form' in request.POST else None)

    specimen_type_add_form = SpecimenTypeForm(
        request.POST if 'specimen-type-add-form' in request.POST else None,
    )

    del specimen_type_add_form.id
    del specimen_type_add_form.ui_selected

    specimen_type_crud_form = SpecimenTypeCrudForm(
        request.POST if 'specimen-type-crud-form' in request.POST else None,
        types=specimen_types,
    )

    aliquot_type_add_form = AliquotTypeForm(
        request.POST if 'aliquot-type-add-form' in request.POST else None
    )

    del aliquot_type_add_form.id
    del aliquot_type_add_form.ui_selected

    aliquot_type_crud_form = AliquotTypeCrudForm(
        request.POST if 'aliquot-type-crud-form' in request.POST else None,
        types=aliquot_types,
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

    elif 'specimen-type-crud-form' in request.POST and 'save' in request.POST:
        if specimen_type_crud_form.validate():
            for i, entry in enumerate(specimen_type_crud_form.types.entries):
                del entry.form.id
                apply_changes(entry.form, specimen_types[i])
            db_session.flush()
            request.session.flash(
                _(u'Sucessfully updated specimen types'), 'success')
            return HTTPFound(location=request.current_route_path())
        else:
            request.session.flash(
                _(u'Form errors, please revise below'), 'danger')

    elif 'specimen-type-crud-form' in request.POST \
            and 'delete' in request.POST:
        ids = [
            e.form.id.object_data
            for e in specimen_type_crud_form.types.entries
            if e.form.ui_selected.data]
        if not ids:
            request.session.flash(_(u'No specimen types selected'), 'warning')

        (exists,) = (
            db_session.query(
                db_session.query(models.Specimen)
                .filter(models.Specimen.specimen_type_id.in_(ids))
                .exists())
            .one())

        if not exists:
            count = (
                db_session.query(models.SpecimenType)
                .filter(models.SpecimenType.id.in_(ids))
                .delete(synchronize_session=False))
            db_session.flush()
            request.session.flash(
                _(u'Deleted {0} specimen types'.format(count)), 'success')
            return HTTPFound(location=request.current_route_path())
        else:
            request.session.flash(
                _(u'Selected types already have specimen collected'),
                'danger')

    elif 'aliquot-type-add-form' in request.POST:
        if aliquot_type_add_form.validate():
            data = aliquot_type_add_form.data
            data['name'] = slugify(data['title'])
            db_session.add(models.AliquotType(**data))
            request.session.flash(
                _(u'Sucessfully added aliquot type'), 'success')
            return HTTPFound(location=request.current_route_path())
        else:
            request.session.flash(
                _(u'Form errors, please revise below'), 'danger')

    elif 'aliquot-type-crud-form' in request.POST and 'save' in request.POST:
        if aliquot_type_crud_form.validate():
            for i, entry in enumerate(aliquot_type_crud_form.types.entries):
                del entry.form.id
                apply_changes(entry.form, aliquot_types[i])
            db_session.flush()
            request.session.flash(
                _(u'Sucessfully updated aliquot types'), 'success')
            return HTTPFound(location=request.current_route_path())
        else:
            request.session.flash(
                _(u'Form errors, please revise below'), 'danger')

    elif 'aliquot-type-crud-form' in request.POST and 'delete' in request.POST:
        ids = [
            e.form.id.object_data
            for e in aliquot_type_crud_form.types.entries
            if e.form.ui_selected.data]
        if not ids:
            request.session.flash(_(u'No aliquot types selected'), 'warning')

        (exists,) = (
            db_session.query(
                db_session.query(models.Aliquot)
                .filter(models.Aliquot.aliquot_type_id.in_(ids))
                .exists())
            .one())

        if not exists:
            count = (
                db_session.query(models.AliquotType)
                .filter(models.AliquotType.id.in_(ids))
                .delete(synchronize_session=False))
            request.session.flash(
                _(u'Deleted {0} aliquot types'.format(count)), 'success')
            return HTTPFound(location=request.current_route_path())
        else:
            request.session.flash(
                _(u'Selected types already have aliquot collected'),
                'danger')

    elif 'lab_add_form' in request.POST:
        if lab_add_form.validate():
            db_session.add(models.Location(**lab_add_form.data))
            db_session.flush()

            request.session.flash(
                _(u'Sucessfully added lab'), 'success')
            return HTTPFound(location=request.current_route_path())
        else:
            request.session.flash(
                _(u'Form errors, please revise below'), 'danger')

    elif 'delete_location_form' in request.POST:
        title = request.POST['labs'].strip()

        (exists,) = (
            db_session.query(
                db_session.query(models.Location)
                .filter_by(title=title)
                .exists())
            .one())

        if exists:
            db_session.query(models.Location).filter(
                models.Location.title == title).delete()
            db_session.flush()

            request.session.flash(
                _(u'Sucessfully deleted lab'), 'success')
        else:
            request.session.flash(
                _(u'Lab did not exist in the database'),
                'danger')

        return HTTPFound(location=request.current_route_path())

    query = (
        db_session.query(models.Location)
        .order_by(models.Location.title))

    return {
        'specimen_types': specimen_types,
        'specimen_types_count': specimen_types_count,
        'specimen_type_add_form': specimen_type_add_form,
        'specimen_type_crud_form': specimen_type_crud_form,

        'aliquot_types': aliquot_types,
        'aliquot_types_count': aliquot_types_count,
        'aliquot_type_add_form': aliquot_type_add_form,
        'aliquot_type_crud_form': aliquot_type_crud_form,

        'lab_add_form': lab_add_form,

        'labs': query
    }
