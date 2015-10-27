from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.session import check_csrf_token
import wtforms

from occams.utils.forms import apply_changes

from .. import _, models
from .aliquot import filter_aliquot


@view_config(
    route_name='lims.checkin',
    permission='process',
    renderer='../templates/checkin/checkin.pt')
def checkin(context, request):
    db_session = request.db_session
    vals = filter_aliquot(context, request, state='checked-out')
    aliquot = vals['aliquot']

    available_locations = [
        (l.id, l.title)
        for l in db_session.query(models.Location).order_by('title')]

    class CheckinForm(wtforms.Form):
        ui_selected = wtforms.BooleanField()
        id = wtforms.IntegerField(
            widget=wtforms.widgets.HiddenInput())
        amount = wtforms.DecimalField(
            places=1,
            validators=[wtforms.validators.Optional()])
        freezer = wtforms.StringField(
            validators=[wtforms.validators.Optional()])
        rack = wtforms.StringField(
            validators=[wtforms.validators.Optional()])
        box = wtforms.StringField(
            validators=[wtforms.validators.Optional()])
        thawed_num = wtforms.IntegerField(
            validators=[wtforms.validators.Optional()])
        location_id = wtforms.SelectField(
            choices=available_locations,
            coerce=int,
            validators=[wtforms.validators.Optional()])
        notes = wtforms.TextAreaField(
            validators=[wtforms.validators.Optional()])

    class CrudForm(wtforms.Form):
        aliquot = wtforms.FieldList(wtforms.FormField(CheckinForm))

    form = CrudForm(request.POST, aliquot=aliquot)

    if request.method == 'POST' and check_csrf_token(request):

        if 'save' in request.POST and form.validate():
            for i, entry in enumerate(form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
            request.session.flash(_(u'Changed saved'), 'success')
            return HTTPFound(location=request.current_route_path())

        elif 'checkin' in request.POST and form.validate():
            state = (
                db_session.query(models.AliquotState)
                .filter_by(name='checked-in')
                .one())
            updated_count = 0
            for i, entry in enumerate(form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
                if entry.ui_selected.data:
                    aliquot[i].location = context
                    aliquot[i].state = state
                    updated_count += 1
            db_session.flush()
            if updated_count:
                request.session.flash(
                    _(u'${count} aliquot have been changed to the status of '
                      u'${state}',
                        mapping={
                            'count': updated_count,
                            'state': state.title
                        }),
                    'success')
            else:
                request.session.flash(_(u'Please select Aliquot'), 'warning')
            return HTTPFound(location=request.current_route_path())

    vals.update({
        'form': form,
    })

    return vals
