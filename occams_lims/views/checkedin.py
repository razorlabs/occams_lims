from pyramid.httpexceptions import HTTPFound, HTTPOk
from pyramid.view import view_config
from pyramid.session import check_csrf_token
import wtforms

from occams.utils.forms import apply_changes

from .. import _, models
from ..validators import required_if
from .aliquot import filter_aliquot


@view_config(
    route_name='lims.checked-in',
    permission='process',
    renderer='../templates/checked-in/checked-in.pt')
def checked_in(context, request):
    db_session = request.db_session
    vals = filter_aliquot(context, request, state='checked-in')
    aliquot = vals['aliquot']

    available_locations = [
        (l.id, l.title)
        for l in db_session.query(models.Location).order_by('title')]

    if 'checkout' in request.POST:
        conditionally_required = required_if('ui_selected')
    else:
        conditionally_required = wtforms.validators.optional()

    class CheckoutForm(wtforms.Form):
        ui_selected = wtforms.BooleanField()
        id = wtforms.IntegerField(
            widget=wtforms.widgets.HiddenInput())
        amount = wtforms.DecimalField(
            places=1,
            validators=[conditionally_required])
        freezer = wtforms.StringField(
            validators=[wtforms.validators.optional()])
        rack = wtforms.StringField(
            validators=[wtforms.validators.optional()])
        box_row = wtforms.StringField(
            validators=[wtforms.validators.optional()])
        box_column = wtforms.StringField(
            validators=[wtforms.validators.optional()])
        box = wtforms.StringField(
            validators=[wtforms.validators.optional()])
        thawed_num = wtforms.IntegerField(
            validators=[wtforms.validators.optional()])
        location_id = wtforms.SelectField(
            choices=available_locations,
            coerce=int,
            validators=[wtforms.validators.optional()])
        notes = wtforms.TextAreaField(
            validators=[wtforms.validators.optional()])

    class CrudForm(wtforms.Form):
        aliquot = wtforms.FieldList(wtforms.FormField(CheckoutForm))

    form = CrudForm(request.POST, aliquot=aliquot)

    if request.method == 'POST' and check_csrf_token(request):

        if 'save' in request.POST and form.validate():
            for i, entry in enumerate(form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
            request.session.flash(_(u'Changed saved'), 'success')
            return HTTPFound(location=request.current_route_path())

        elif 'pending-checkout' in request.POST and form.validate():
            state = (
                db_session.query(models.AliquotState)
                .filter_by(name='pending-checkout')
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

def build_box_form(context, request):
    db_session = request.db_session

    def row_col_conflict():
        pass

    class BoxForm(wtforms.Form):
        row = wtforms.StringField(
            'row',
            [wtforms.validators.Optional(),
             row_col_conflict,
             wtforms.validators.NumberRange(min=1, max=9)
            ])

        column = wtforms.StringField(
            'column',
            [wtforms.validators.Optional(),
             row_col_conflict,
             wtforms.validators.Regexp(
                '[a-i]', message='row must be between a-i')
            ])

    return BoxForm

@view_config(
    route_name='lims.boxes',
    permission='view',
    renderer='../templates/checked-in/modal-boxes.pt')
def box_grid(context, request):
    db_session = request.db_session
    Form = build_box_form(context, request)
    form = Form(request.POST)

    return {
        'form': form
    }

