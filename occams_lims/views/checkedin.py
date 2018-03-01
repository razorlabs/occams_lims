from pyramid.httpexceptions import HTTPFound, HTTPOk
from pyramid.view import view_config
from pyramid.session import check_csrf_token
import wtforms
import sqlalchemy as sa

from occams.utils.forms import apply_changes

from .. import _, models
from ..validators import required_if
from .aliquot import filter_aliquot
from occams_studies import models as studies

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
        def box_position_open(form, field):
            """
                Validates the box grid positions already selected
                is not occupied
            """
            message = "Box grid position {row} {col} already occupied by \
                       Aliquot id {id}"
            box_query = (
                    db_session.query(models.Aliquot)
                    .filter(models.Aliquot.box == form.box.data)
                    .filter(models.Aliquot.box_row == str(form.box_row.data))
                    .filter(models.Aliquot.box_column == form.box_column.data)
                    .first()
                    )

            if box_query is not None:
                if (form.id.data != box_query.id):
                    raise wtforms.ValidationError(message.format(
                        row=form.box_row.data,
                        col=form.box_column.data,
                        id=box_query.id))

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
        box_row = wtforms.IntegerField(
            validators=[wtforms.validators.optional(),
                        wtforms.validators.NumberRange(min=1, max=9,
                            message="Please enter number between 1-9")])
        box_column = wtforms.StringField(
            validators=[wtforms.validators.optional(),
                        wtforms.validators.Regexp('[abcdefghi]',
                        message= "Please enter lower case letter between a-i")])
        box = wtforms.StringField(
            validators=[wtforms.validators.optional(), box_position_open])
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

@view_config(
    route_name='lims.boxes_json',
    permission='view',
    renderer='../templates/checked-in/modal-boxes-json.pt')
def box_grid(context, request):
    """
        Creates a template return view to host box grid/AJAX html
    """
    dummy_view = ''

    return {
        'data': dummy_view
    }

# AJAX data for box grid modal (modal-boxes-json.pt)
@view_config(
    route_name='lims.boxes_ajax',
    permission='view',
    renderer='json')
def box_ajax(context, request):
    db_session = request.db_session
    box_query = (
        db_session.query(models.Aliquot)
        .filter(models.Aliquot.box != sa.null())
        .filter(models.Aliquot.box_row != sa.null())
        .filter(models.Aliquot.box_column != sa.null())
        )

    def aliquot_abbrev(aliquot_id):
        """
            Creates abbrevation of aliquot type for box grid fill
            See /lims/settings under setup cog
        """
        abbrvs = { 1: 'pbmc', 2: 'plsm', 3: 'WB', 4: 'Ur',
                   5: 'Swb', 6: 'BldSpt', 7: 'BdPlsm',
                   8: 'swbcvf', 9: 'swbmb', 10: 'swbvm',
                   11: 'swbCAll', 12: 'swbwck'}

        return abbrvs[aliquot_id]

    def patient_id(specimen_id):
        """
            Find the patient OUR by cross referencing parent specimen
        """

        # get target specimen
        specimen_query = (
            db_session.query(models.Specimen)
            .filter_by(id=specimen_id)
            .one())

        # get patient id
        patient_id = specimen_query.patient_id

        # get patient our
        patient_our = (
            db_session.query(studies.Patient)
            .filter_by(id=patient_id)
            .one())

        our = patient_our.pid

        return our

    assign_aliquot = box_query.all()
    aliquot_dict = {}

    # Build dict for ajax return
    for aliquot in assign_aliquot:
        our = patient_id(aliquot.specimen_id)
        aliquot_type = aliquot.aliquot_type_id
        aliquot_abbr = aliquot_abbrev(aliquot_type)

        abbr = ''.join([our, ' ', aliquot_abbr])

        aliquot_dict[aliquot.id] = {
                'box'     : aliquot.box,
                'box_row' : aliquot.box_row,
                'box_col' : aliquot.box_column,
                'abbr'    : abbr
                }

    # Accessed in modal-boxes-json.pt for js box-grid functions
    return { 'aliquot' : aliquot_dict }

