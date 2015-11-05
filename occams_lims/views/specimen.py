import six
from pyramid.httpexceptions import HTTPFound, HTTPOk, HTTPForbidden
from pyramid.response import FileIter
from pyramid.view import view_config
from pyramid.session import check_csrf_token
import sqlalchemy as sa
import wtforms
from wtforms.ext.dateutil.fields import DateField
from wtforms_components import TimeField

from occams.utils.forms import apply_changes
from occams.utils.pagination import Pagination

from .. import _, models
from ..labels import printLabelSheet


SPECIMEN_LABEL_QUEUE = 'specimen_label_queue'


class SPECIMEN_LABEL_SETTINGS:

    page_height = 11.0
    page_width = 8.5

    top_margin = 0.5
    side_margin = 0.187

    vert_pitch = 1.0
    horz_pitch = 2.75

    label_height = 1.0
    label_width = 2.625
    label_round = 0.1

    no_across = 3
    no_down = 10


@view_config(
    route_name='lims.specimen',
    permission='view',
    renderer='../templates/specimen/specimen.pt')
def specimen(context, request):
    db_session = request.db_session

    vals = filter_specimen(context, request, state=u'pending-draw')
    specimen = vals['specimen']

    # override specimen with default processing locations
    processing_location_name = None
    processing_location = None

    if 'aeh' in db_session.bind.url.database:
        processing_location_name = {
            'richman lab': 'richman lab',
            'avrc': 'richman lab'
        }.get(context.name)
    elif 'cctg' in db_session.bind.url.database:
        processing_location_name = {
            'harbor-ucla-clinic': 'harbor-ucla-clinic',
            'long-beach-clinic': 'long_beach_lab',
            'long-beach-lab': 'long_beach_lab',
            'usc-clinic': 'usc-lab',
            'usc-lab': 'usc-lab',
            'avrc': 'avrc',
        }.get(context.name)
    elif 'mhealth' in db_session.bind.url.database:
        processing_location_name = {
            'avrc': 'avrc',
        }.get(context.name)
    else:
        processing_location_name = None

    if processing_location_name:
        processing_location = (
            db_session.query(models.Location)
            .filter_by(name=processing_location_name)
            .one())

    overriden_specimen = [{
        'id': s.id,
        'tubes': s.tubes,
        'collect_date': s.collect_date,
        'collect_time': s.collect_time,
        'location_id': processing_location and processing_location.id,
        'notes': s.notes
    } for s in specimen if s]

    Form = build_crud_form(context, request)
    form = Form(request.POST, specimen=overriden_specimen)

    label_queue = request.session.setdefault(SPECIMEN_LABEL_QUEUE, set())

    if (request.method == 'POST'
            and check_csrf_token(request)
            and form.validate()):

        if not request.has_permission('process'):
            raise HTTPForbidden

        if 'save' in request.POST:
            updated_count = 0
            for i, subform in enumerate(form.specimen.entries):
                if apply_changes(subform.form, specimen[i]):
                    updated_count += 1
            db_session.flush()
            if updated_count:
                request.session.flash(u'Changes saved', 'success')
            else:
                request.session.flash(u'No changes were saved', 'warning')
            return HTTPFound(location=request.current_route_path())

        if 'queue' in request.POST:
            queue_count = 0
            for i, subform in enumerate(form.specimen.entries):
                apply_changes(subform.form, specimen[i])
                if subform.ui_selected.data:
                    queue_count += 1
                    specimen_id = subform['id'].data
                    if specimen_id in label_queue:
                        label_queue.discard(specimen_id)
                    else:
                        label_queue.add(specimen_id)
            request.session.changed()
            if queue_count:
                request.session.flash(
                    u'Specimen print queue has changed.', 'success')
            else:
                request.session.flash(u'Please select specimen', 'warning')
            return HTTPFound(location=request.current_route_path())

        for state_name in ('cancel-draw', 'pending-aliquot'):
            if state_name in request.POST:
                state = (
                    db_session.query(models.SpecimenState)
                    .filter_by(name=state_name)
                    .one())
                transitioned_count = 0
                updated_count = 0
                for i, subform in enumerate(form.specimen.entries):
                    if subform.ui_selected.data:
                        specimen[i].state = state
                        transitioned_count += 1
                    if apply_changes(subform.form, specimen[i]):
                        updated_count += 1
                db_session.flush()
                if transitioned_count:
                    request.session.flash(
                        u'%d Specimen have been changed to the status of %s.'
                        % (transitioned_count, state.title),
                        'success')
                else:
                    request.session.flash(u'Please select specimen', 'warning')
                return HTTPFound(location=request.current_route_path())

    vals.update({
        'form': form,
        'has_labels_queued': len(label_queue),
        'label_queue': label_queue,
    })

    return vals


def make_specimen_label(specimen):
    pid = specimen.patient.pid
    collect_date = specimen.collect_date
    study_label = specimen.cycle.study.short_title
    cycle_label = specimen.cycle.week or specimen.cycle.title
    type_ = specimen.specimen_type
    barcode = -1
    lines = [
        u'{}   {}'.format(pid, collect_date.strftime('%m/%d/%Y')),
        u'{} - {}'.format(study_label, cycle_label),
        u'{}'.format(type_.name)
    ]
    return barcode, lines


@view_config(
    route_name='lims.specimen_labels',
    permission='view',
    renderer='../templates/modal-labels.pt')
def specimen_labels(context, request):
    db_session = request.db_session

    label_queue = request.session.setdefault(SPECIMEN_LABEL_QUEUE, set())

    class PrintForm(wtforms.Form):
        startcol = wtforms.IntegerField(
            u'Starting Column Position',
            default=1,
            validators=[wtforms.validators.InputRequired()])
        startrow = wtforms.IntegerField(
            u'String Row Position',
            default=1,
            validators=[wtforms.validators.InputRequired()])

    form = PrintForm(request.POST)

    if request.method == 'POST' and check_csrf_token(request):
        if not request.has_permission('process'):
            raise HTTPForbidden()

        if 'print' in request.POST and form.validate():
            if label_queue:
                query = (
                    db_session.query(models.Specimen)
                    .filter(models.Specimen.id.in_(label_queue))
                    .order_by(
                        models.Specimen.patient_id,
                        models.Specimen.specimen_type_id,
                        models.Specimen.id))

                printables = iter(
                    make_specimen_label(s)
                    for s in query
                    for i in six.moves.range(s.tubes)
                    if s.tubes)

                stream = six.StringIO()
                printLabelSheet(
                    stream,
                    u'{} labels'.format(context.title),
                    printables,
                    SPECIMEN_LABEL_SETTINGS,
                    form.startcol.data,
                    form.startrow.data)
                stream.flush()
                stream.seek(0)

                request.session[SPECIMEN_LABEL_QUEUE] = set()
                request.session.changed()

                response = request.response
                response.content_type = 'application/pdf'
                response.content_disposition = 'attachment;filename=labels.pdf'
                response.app_iter = FileIter(stream)
                return response

        elif 'clear' in request.POST:
            request.session[SPECIMEN_LABEL_QUEUE] = set()
            request.session.changed()
            request.session.flash(u'Your Queue has been cleared', 'info')
            next = request.current_route_path(_route_name='lims.lab')
            if request.is_xhr:
                return HTTPOk(json={'__next__': next})
            else:
                return HTTPFound(location=next)

    return {
        'form': form,
        'count': len(label_queue)
    }


@view_config(
    route_name='lims.add',
    permission='process',
    renderer='../templates/specimen/modal-specimen-add.pt')
def add(context, request):
    db_session = request.db_session
    Form = build_add_form(context, request)
    form = Form(request.POST)

    if (request.method == 'POST'
            and check_csrf_token(request)
            and form.validate()):
        state = (
            db_session.query(models.SpecimenState)
            .filter_by(name=u'pending-draw')
            .one())
        patient = (
            db_session.query(models.Patient)
            .filter_by(pid=form.pid.data)
            .one())
        cycle = db_session.query(models.Cycle).get(form.cycle_id.data)
        type_ = \
            db_session.query(models.SpecimenType) \
            .get(form.specimen_type_id.data)
        visit = (
            db_session.query(models.Visit)
            .filter(models.Visit.patient_id == patient.id)
            .filter(models.Visit.cycles.any(id=form.cycle_id.data))
            .one())
        db_session.add(models.Specimen(
            patient=patient,
            cycle=cycle,
            specimen_type=type_,
            state=state,
            collect_date=visit.visit_date,
            location=context,
            tubes=type_.default_tubes))
        db_session.flush()
        request.session.flash(
            _(u'Specimen added for ${pid}', mapping={'pid': form.pid.data}),
            'success')
        url = request.current_route_path(_route_name='lims.specimen')
        return HTTPOk(json={'__next__': url})

    return {
        'form': form
    }


def build_crud_form(context, request):
    db_session = request.db_session

    # We can send to any location, we don't need access
    locations_query = (
        db_session.query(models.Location)
        .filter_by(active=True)
        .order_by(models.Location.title))

    locations = [(l.id, l.title) for l in locations_query]

    class SpecimenForm(wtforms.Form):

        ui_selected = wtforms.BooleanField()

        id = wtforms.IntegerField(widget=wtforms.widgets.HiddenInput())

        tubes = wtforms.IntegerField(
            validators=[
                wtforms.validators.Optional(),
                wtforms.validators.NumberRange(min=1)])

        collect_date = DateField(
            validators=[wtforms.validators.Optional()])

        # There doesn't seem to be a nice way to add the colon if the
        # user forgets to do so, might need to make our own Field type
        collect_time = TimeField(
            format='%H:%M',
            validators=[wtforms.validators.Optional()])

        location_id = wtforms.SelectField(
            choices=locations,
            coerce=int,
            validators=[wtforms.validators.InputRequired()])

        notes = wtforms.TextAreaField(
            validators=[wtforms.validators.Optional()])

    class CrudForm(wtforms.Form):
        specimen = wtforms.FieldList(wtforms.FormField(SpecimenForm))

    return CrudForm


def build_add_form(context, request):
    db_session = request.db_session

    cycles_query = (
        db_session.query(models.Cycle)
        .join(models.Study)
        .filter(models.Study.start_date != sa.null())
        .order_by(
            models.Study.title,
            models.Cycle.week.asc().nullsfirst()))

    cycles = [(0, u'Please select a cycle')] \
        + [(c.id, c.title) for c in cycles_query]

    types_query = (
        db_session.query(models.SpecimenType)
        .order_by(
            models.SpecimenType.title))

    types = [(0, u'Please select a type')] \
        + [(t.id, t.title) for t in types_query]

    def check_patient_exists(form, field):
        pid = field.data
        exists = (
            db_session.query(
                db_session.query(models.Patient)
                .filter_by(pid=pid)
                .exists())
            .scalar())
        if not exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Does not exist')))

    def check_has_visit(form, field):
        pid = form.pid.data
        cycle_id = form.cycle_id.data

        if not pid:
            return

        exists = (
            db_session.query(
                db_session.query(models.Visit)
                .filter(models.Visit.patient.has(pid=pid))
                .filter(models.Visit.cycles.any(id=cycle_id))
                .exists())
            .scalar())
        if not exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Patient does not have a visit for this cycle')))

    class SpecimenAddForm(wtforms.Form):

        pid = wtforms.StringField(
            _(u'Patient'),
            description=_(u'Patient\'s PID'),
            validators=[
                wtforms.validators.InputRequired(),
                check_patient_exists])

        cycle_id = wtforms.SelectField(
            _(u'Cycle'),
            description=_(
                u'Select the cycle for which this specimen will be collected'),
            choices=cycles,
            coerce=int,
            validators=[
                # check coerced values instead of raw data
                wtforms.validators.DataRequired(),
                check_has_visit])

        specimen_type_id = wtforms.SelectField(
            _(u'Specimen Type'),
            description=_(u'The Type of specimen to be added.'),
            choices=types,
            coerce=int,
            validators=[
                # check coerced values instead of raw data
                wtforms.validators.DataRequired()])

    return SpecimenAddForm


def filter_specimen(context, request, state, page_key='page', omit=None):
    db_session = request.db_session

    omit = set(omit or [])

    types_query = db_session.query(models.SpecimenType).order_by('title')
    available_types = [(t.id, t.title) for t in types_query]

    states_query = db_session.query(models.SpecimenState).order_by('title')
    available_states = [(s.id, s.title) for s in states_query]

    class FilterForm(wtforms.Form):

        pid = wtforms.StringField(
            _(u'PID'),
            validators=[wtforms.validators.Optional()])

        specimen_types = wtforms.SelectMultipleField(
            _(u'Specimen Types'),
            choices=available_types,
            coerce=int,
            validators=[wtforms.validators.Optional()])

        specimen_states = wtforms.SelectMultipleField(
            _(u'Specimen States'),
            choices=available_states,
            coerce=int,
            validators=[wtforms.validators.Optional()])

        from_ = DateField(
            _(u'From Date'),
            validators=[wtforms.validators.Optional()])

        to = DateField(
            _(u'To Date'),
            validators=[wtforms.validators.Optional()])

    filter_form = FilterForm(request.GET)

    for name in omit:
        del filter_form[name]

    # TODO: There is a possibility that the listing might get
    #       updated between requests, we need to make sure the same
    #       listing is repeatable...
    query = (
        db_session.query(models.Specimen)
        .filter(
            (models.Specimen.location == context)
            | (models.Specimen.previous_location == context))
        .order_by(
            models.Specimen.collect_date.desc().nullsfirst(),
            models.Specimen.patient_id,
            models.Specimen.specimen_type_id,
            models.Specimen.id))

    if 'pid' not in omit and filter_form.pid.data:
        query = query.filter(models.Specimen.patient.has(
            models.Patient.pid.ilike('%s%%' % filter_form.pid.data)))

    if 'specimen_types' not in omit and filter_form.specimen_types.data:
        query = query.filter(models.Specimen.specimen_type.has(
            models.SpecimenType.id.in_(filter_form.specimen_types.data)))

    if 'specimen_states' not in omit and filter_form.specimen_states.data:
        query = query.filter(models.Specimen.state.has(
            models.SpecimenState.id.in_(filter_form.specimen_states.data)))
    else:
        query = query.filter(models.Specimen.state.has(name=state))

    if 'from_' not in omit and filter_form.from_.data:
        query = query.filter(
            models.Specimen.collect_date >= filter_form.from_.data)

    if 'to' not in omit and filter_form.to.data:
        query = query.filter(
            models.Specimen.collect_date <= filter_form.to.data)

    total_count = query.count()
    pager = Pagination(request.GET.get(page_key), 10, total_count)

    specimen = query.offset(pager.offset).limit(pager.per_page).all()

    return {
        'filter_form': filter_form,
        'specimen': specimen,
        'has_specimen': len(specimen) > 0,
        'pager': pager,
    }
