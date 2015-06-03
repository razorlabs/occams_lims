from datetime import date

from pyramid.httpexceptions import HTTPFound, HTTPOk, HTTPForbidden
from pyramid.view import view_config
from pyramid.session import check_csrf_token
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from wtforms.ext.dateutil.fields import DateField
from wtforms_components import TimeField

from occams.utils.forms import apply_changes
from occams.utils.pagination import Pagination

from .. import _, models, Session
from ..labels import (
    printLabelSheet,
    LabeledSpecimen,
    SPECIMEN_LABEL_SETTINGS,
    LabeledAliquot,
    ALIQUOT_LABEL_SETTINGS)

SPECIMEN_LABEL_QUEUE = 'specimen_label_queue'
ALIQUOT_LABEL_QUEUE = 'aliquot_label_queue'


@view_config(
    route_name='lims.main',
    permission='view',
    renderer='../templates/lab/list.pt')
def list_(context, request):
    """
    Displays available labs to the authenticated user

    XXX: We are currently relying on the fact that locations
         assigned to a site can manage samples through OCCAMS.
         All other locations will also be listed only in sample
         destination options when editing.
    """

    # We need to know which sites the user has access
    sites = Session.query(models.Site)
    site_ids = [s.id for s in sites if request.has_permission('view', s)]

    query = (
        Session.query(models.Location)
        .filter_by(active=True)
        .filter(models.Location.sites.any(
            models.Site.id.in_(site_ids)))
        .order_by(models.Location.title))

    return {
        'labs': query
    }


def get_processing_location(context):
    """
    This is a stupid hack to get this launched already
    the original version depends on having a default destination
    """

    if 'aeh' in Session.bind.url.database:
        processing_location_name = {
            'richman lab': 'richman lab',
            'avrc': 'richman lab'
        }.get(context.name)
    elif 'cctg' in Session.bind.url.database:
        processing_location_name = {
            'harbor-ucla-clinic': 'harbor-ucla-clinic',
            'long-beach-clinic': 'long_beach_lab',
            'long-beach-lab': 'long_beach_lab',
            'usc-clinic': 'usc-lab',
            'usc-lab': 'usc-lab',
            'avrc': 'avrc',
        }.get(context.name)
    elif 'mhealth' in Session.bind.url.database:
        processing_location_name = {
            'avrc': 'avrc',
        }.get(context.name)
    else:
        processing_location_name = None

    if processing_location_name:
        return (
            Session.query(models.Location)
            .filter_by(name=processing_location_name)
            .one())


def build_crud_form(context, request):

    # We can send to any location, we don't need access
    locations_query = (
        Session.query(models.Location)
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

        collect_time = TimeField(
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


@view_config(
    route_name='lims.lab',
    permission='view',
    renderer='../templates/lab/inbox.pt')
def inbox(context, request):

    vals = filter_specimen(context, request, state=u'pending-draw')
    specimen = vals['specimen']

    # override specimen with default processing locations
    processing_location = get_processing_location(context)
    overriden_specimen = [{
        'id': s.id,
        'tubes': s.tubes,
        'collect_date': s.collect_date,
        'collect_time': s.collect_time,
        'location_id':
            processing_location.id
            if (processing_location
                and s.location == context
                and not s.previous_location)
            else context.id,
        'notes': s.notes} for s in specimen if s]

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
            Session.flush()
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

        for state_name in ('cancel-draw', 'complete'):
            if state_name in request.POST:
                state = (
                    Session.query(models.SpecimenState)
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
                Session.flush()
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


@view_config(
    route_name='lims.lab_specimen_labels',
    permission='view',
    renderer='../templates/lab/modal-labels.pt')
def specimen_labels(context, request):

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
                    Session.query(models.Specimen)
                    .filter(models.Specimen.id.in_(label_queue))
                    .order_by(
                        models.Specimen.patient_id,
                        models.Specimen.specimen_type_id,
                        models.Specimen.id))

                printables = [
                    LabeledSpecimen(s)
                    for s in query
                    for i in range(s.tubes)
                    if s.tubes]

                content = printLabelSheet(
                    context,
                    printables,
                    SPECIMEN_LABEL_SETTINGS,
                    form.startcol.data,
                    form.startrow.data)

                request.session[SPECIMEN_LABEL_QUEUE] = set()
                request.session.changed()

                response = request.response
                response.content_type = 'application/pdf'
                response.content_disposition = 'attachment;filename=labels.pdf'
                response.body = content
                return response

        elif 'clear' in request.POST:
            request.session[SPECIMEN_LABEL_QUEUE] = set()
            request.session.changed()
            request.session.flash(u'Your Queue has been cleared', 'info')
            next = request.current_route_path(_route_name='lab')
            if request.is_xhr:
                return HTTPOk(json={'__next__': next})
            else:
                return HTTPFound(location=next)

    return {
        'form': form,
        'count': len(label_queue)
    }


@view_config(
    route_name='lims.lab_aliquot_labels',
    permission='view',
    renderer='../templates/lab/modal-labels.pt')
def aliquot_labels(context, request):

    label_queue = request.session.setdefault(ALIQUOT_LABEL_QUEUE, set())

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
            raise HTTPForbidden

        if 'print' in request.POST and form.validate():
            if label_queue:
                query = (
                    Session.query(models.Aliquot)
                    .join(models.Specimen)
                    .filter(models.Aliquot.id.in_(label_queue))
                    .order_by(
                        models.Specimen.patient_id,
                        models.Aliquot.aliquot_type_id,
                        models.Aliquot.id))

                printables = [LabeledAliquot(s) for s in query]

                content = printLabelSheet(
                    context,
                    printables,
                    ALIQUOT_LABEL_SETTINGS,
                    form.startcol.data,
                    form.startrow.data)

                request.session[ALIQUOT_LABEL_QUEUE] = set()
                request.session.changed()

                response = request.response
                response.content_type = 'application/pdf'
                response.content_disposition = 'attachment;filename=labels.pdf'
                response.body = content
                return response

        elif 'clear' in request.POST:
            request.session[ALIQUOT_LABEL_QUEUE] = set()
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


def build_add_form(context, request):

    cycles_query = (
        Session.query(models.Cycle)
        .join(models.Study)
        .filter(models.Study.start_date != sa.null())
        .order_by(
            models.Study.title,
            models.Cycle.week.asc().nullsfirst()))

    cycles = [(0, u'Please select a cycle')] \
        + [(c.id, c.title) for c in cycles_query]

    types_query = (
        Session.query(models.SpecimenType)
        .order_by(
            models.SpecimenType.title))

    types = [(0, u'Please select a type')] \
        + [(t.id, t.title) for t in types_query]

    def check_patient_exists(form, field):
        pid = field.data
        exists = (
            Session.query(
                Session.query(models.Patient)
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
            Session.query(
                Session.query(models.Visit)
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


@view_config(
    route_name='lims.lab_specimen_add',
    permission='process',
    renderer='../templates/lab/modal-specimen-add.pt')
def add(context, request):
    Form = build_add_form(context, request)
    form = Form(request.POST)

    if (request.method == 'POST'
            and check_csrf_token(request)
            and form.validate()):
        state = (
            Session.query(models.SpecimenState)
            .filter_by(name=u'pending-draw')
            .one())
        patient = (
            Session.query(models.Patient)
            .filter_by(pid=form.pid.data)
            .one())
        cycle = Session.query(models.Cycle).get(form.cycle_id.data)
        type_ = \
            Session.query(models.SpecimenType).get(form.specimen_type_id.data)
        visit = (
            Session.query(models.Visit)
            .filter(models.Visit.patient_id == patient.id)
            .filter(models.Visit.cycles.any(id=form.cycle_id.data))
            .one())
        Session.add(models.Specimen(
            patient=patient,
            cycle=cycle,
            specimen_type=type_,
            state=state,
            collect_date=visit.visit_date,
            location=context,
            tubes=type_.default_tubes))
        Session.flush()
        request.session.flash(
            _(u'Specimen added for ${pid}', mapping={'pid': form.pid.data}),
            'success')
        url = request.current_route_path(_route_name='lims.lab')
        return HTTPOk(json={'__next__': url})

    return {
        'form': form
    }


def filter_specimen(context, request, state, page_key='page', omit=None):

    omit = set(omit or [])

    types_query = Session.query(models.SpecimenType).order_by('title')
    available_types = [(t.id, t.title) for t in types_query]

    states_query = Session.query(models.SpecimenState).order_by('title')
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
        Session.query(models.Specimen)
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


def filter_aliquot(context, request, state, page_key='page', omit=None):

    omit = set(omit or [])

    types_query = Session.query(models.AliquotType).order_by('title')
    available_types = [(t.id, t.title) for t in types_query]

    states_query = Session.query(models.AliquotState).order_by('title')
    available_states = [(s.id, s.title) for s in states_query]

    class FilterForm(wtforms.Form):

        pid = wtforms.StringField(
            _(u'PID'),
            validators=[wtforms.validators.Optional()])

        aliquot_types = wtforms.SelectMultipleField(
            _(u'Aliquot Types'),
            choices=available_types,
            coerce=int,
            validators=[wtforms.validators.Optional()])

        aliquot_states = wtforms.SelectMultipleField(
            _(u'Aliquot States'),
            choices=available_states,
            coerce=int,
            validators=[wtforms.validators.Optional()])

        from_ = DateField(
            _(u'From Date'),
            validators=[wtforms.validators.Optional()])

        to = DateField(
            _(u'To Date'),
            validators=[wtforms.validators.Optional()])

        freezer = wtforms.StringField(
            _(u'Freezer'),
            validators=[wtforms.validators.Optional()])

        rack = wtforms.StringField(
            _(u'Rack'),
            validators=[wtforms.validators.Optional()])

        box = wtforms.StringField(
            _(u'Box'),
            validators=[wtforms.validators.Optional()])

    filter_form = FilterForm(request.GET)

    for name in omit:
        del filter_form[name]

    # TODO: There is a possibility that the listing might get
    #       updated between requests, we need to make sure the same
    #       listing is repeatable...
    query = (
        Session.query(models.Aliquot)
        .join(models.Aliquot.specimen)
        .join(models.Specimen.patient)
        .join(models.Aliquot.aliquot_type)
        .join(models.Aliquot.state)
        .filter(
            (models.Aliquot.location == context)
            | (models.Aliquot.previous_location == context))
        .order_by(
            models.Patient.pid,
            models.AliquotType.title,
            models.Aliquot.id))

    if 'pid' not in omit and filter_form.pid.data:
        query = query.filter(
            models.Patient.pid.ilike('%s%%' % filter_form.pid.data))

    if 'aliquot_types' not in omit and filter_form.aliquot_types.data:
        query = query.filter(
            models.Aliquot.aliquot_type_id.in_(filter_form.aliquot_types.data))

    if 'aliquot_states' not in omit and filter_form.aliquot_states.data:
        query = query.filter(
            models.Aliquot.state_id.in_(filter_form.aliquot_states.data))
    else:
        query = query.filter(models.AliquotState.name == state)

    if 'from_' not in omit and filter_form.from_.data:
        query = query.filter(
            (models.Aliquot.store_date >= filter_form.from_.data)
            | (models.Aliquot.inventory_date >= filter_form.from_.data))

    if 'to' not in omit and filter_form.to.data:
        query = query.filter(
            (models.Aliquot.store_date <= filter_form.to.data)
            | (models.Aliquot.inventory_date <= filter_form.to.data))

    if 'freezer' not in omit and filter_form.freezer.data:
        query = query.filter(models.Aliquot.freezer == filter_form.freezer.data)

    if 'rack' not in omit and filter_form.rack.data:
        query = query.filter(models.Aliquot.rack == filter_form.rack.data)

    if 'box' not in omit and filter_form.box.data:
        query = query.filter(models.Aliquot.box == filter_form.box.data)

    total_count = query.count()
    pager = Pagination(request.GET.get(page_key), 20, total_count)

    aliquot = query.offset(pager.offset).limit(pager.per_page).all()

    return {
        'filter_form': filter_form,
        'full_query': query,
        'aliquot': aliquot,
        'has_aliquot': len(aliquot) > 0,
        'pager': pager,
    }


@view_config(
    route_name='lims.lab_batched',
    permission='process',
    renderer='../templates/lab/batched.pt')
def batched(context, request):

    vals = filter_specimen(context, request, state='complete')
    specimen = vals['specimen']

    class BatchSpecimenForm(wtforms.Form):
        ui_selected = wtforms.BooleanField()

    class CrudForm(wtforms.Form):
        specimen = wtforms.FieldList(wtforms.FormField(BatchSpecimenForm))

    form = CrudForm(request.POST, specimen=specimen)

    if (request.method == 'POST'
            and check_csrf_token(request)
            and form.validate()):

        for state_name in ('cancel-draw', 'pending-aliquot'):
            if state_name in request.POST:
                state = (
                    Session.query(models.SpecimenState)
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
                Session.flush()
                if transitioned_count:
                    request.session.flash(
                        u'%d Specimen have been changed to the status of %s.'
                        % (transitioned_count, state.title),
                        'success')
                else:
                    request.session.flash(u'Please select specimen', 'warning')
                return HTTPFound(location=request.current_route_path())

    vals.update({
        'form': form
    })

    return vals


@view_config(
    route_name='lims.lab_ready',
    permission='process',
    renderer='../templates/lab/ready.pt')
def ready(context, request):
    specimen_vals = filter_specimen(context, request, page_key='specimenpage', state='pending-aliquot')
    specimen = specimen_vals['specimen']

    aliquot_vals = filter_aliquot(context, request, page_key='aliquotpage', state='pending')
    aliquot = aliquot_vals['aliquot']

    available_instructions = [
        (i.id, i.title)
        for i in Session.query(models.SpecialInstruction).order_by('title')]

    label_queue = request.session.setdefault(ALIQUOT_LABEL_QUEUE, set())

    class AliquotForm(wtforms.Form):
        ui_selected = wtforms.BooleanField()
        id = wtforms.IntegerField(
            widget=wtforms.widgets.HiddenInput())
        aliquot_type_id = wtforms.SelectField(
            coerce=int,
            validators=[wtforms.validators.Optional()])
        volume = wtforms.DecimalField(
            places=1,
            validators=[wtforms.validators.Optional()])
        cell_amount = wtforms.DecimalField(
            places=1,
            validators=[wtforms.validators.Optional()])
        store_date = DateField(
            default=date.today(),
            validators=[wtforms.validators.Optional()])
        freezer = wtforms.StringField(
            validators=[wtforms.validators.Optional()])
        rack = wtforms.StringField(
            validators=[wtforms.validators.Optional()])
        box = wtforms.StringField(
            validators=[wtforms.validators.Optional()])
        special_instruction = wtforms.SelectField(
            choices=available_instructions,
            coerce=int,
            validators=[wtforms.validators.Optional()])
        notes = wtforms.TextAreaField(
            validators=[wtforms.validators.Optional()])

        def __init__(self, *args, **kw):
            super(AliquotForm, self).__init__(*args, **kw)

            if 'obj' in kw:
                obj = kw['obj']
                if isinstance(obj, models.Specimen):
                    specimen = obj
                elif isinstance(obj, models.Aliquot):
                    specimen = obj.specimen
                else:
                    specimen = None

            if specimen:
                self.aliquot_type_id.choices = [
                    (t.id, t.title)
                    for t in specimen.specimen_type.aliquot_types.values()]

    class SpecimenAliquotForm(AliquotForm):
        count = wtforms.IntegerField(
            validators=[wtforms.validators.Optional()])

    class SpecimenCrudForm(wtforms.Form):
        specimen = wtforms.FieldList(wtforms.FormField(SpecimenAliquotForm))

    class AliquotCrudForm(wtforms.Form):
        aliquot = wtforms.FieldList(wtforms.FormField(AliquotForm))

    specimen_form = SpecimenCrudForm(request.POST, specimen=specimen)
    aliquot_form = AliquotCrudForm(request.POST, aliquot=aliquot)

    def update_print_queue():
        queued = 0
        for entry in aliquot_form.aliquot:
            subform = entry.form
            if subform.ui_selected.data:
                id = subform.id.data
                if id in label_queue:
                    queued += 1
                    label_queue.add(id)
                else:
                    label_queue.discard(id)
                request.session.changed()
        return queued

    if request.method == 'POST' and check_csrf_token(request):

        if 'aliquot' in request.POST and specimen_form.validate():
            state = (
                Session.query(models.AliquotState)
                .filter_by(name='pending')
                .one())
            location = context
            processed_count = 0

            for i, entry in enumerate(specimen_form.specimen.entries):
                subform = entry.form

                # Yes, you are reading this correctly, the original
                # code said it needs to be selected AND set
                if not (subform.ui_selected.data and subform.count.data):
                    continue

                kw = subform.data
                kw['specimen'] = specimen[i]
                kw['state'] = state
                kw['location'] = location
                kw['inventory_date'] = kw['store_date']
                kw['previous_location'] = location

                # clean up the dictionary
                for field in ['id', 'ui_selected', 'count']:
                    if field in kw.keys():
                        del kw[field]

                count = subform.count.data
                samples = [models.Aliquot(**kw) for i in range(count)]
                Session.add_all(aliquot)
                Session.flush()

                processed_count += len(samples)
                label_queue.update(s.id for s in samples)

            if processed_count:
                request.session.changed()
                request.session.flash(
                    _(u'Successfully created %d Aliquot' % processed_count),
                    'success')
            else:
                request.session.flash(_(u'No Aliquot created.'), 'warning')
            return HTTPFound(location=request.current_route_path())

        elif 'aliquoted' in request.POST:
            state_name = 'aliquoted'
            state = (
                Session.query(models.SpecimenState)
                .filter_by(name=state_name)
                .one())
            transitioned_count = 0
            for i, subform in enumerate(specimen_form.specimen.entries):
                if subform.ui_selected.data:
                    specimen[i].state = state
                    transitioned_count += 1
            if transitioned_count:
                Session.flush()
                request.session.flash(
                    _(u'${count} specimen have been changed to the status of ${state}.',
                        mapping={'count': transitioned_count,
                                 'state': state.title}),
                    'success')
            else:
                request.session.flash(u'Please select specimen', 'warning')
            return HTTPFound(location=request.current_route_path())

        elif 'save' in request.POST and aliquot_form.validate():
            updated_count = 0
            for i, entry in enumerate(aliquot_form.aliquot.entries):
                if apply_changes(entry.form, aliquot[i]):
                    updated_count += 1
            if updated_count:
                request.session.flash(
                    _(u'Updated ${count} aliquot',
                        mapping={'count': updated_count}),
                    'success')
            else:
                request.session.flash(_(u'No changes made'), 'warning')
            return HTTPFound(location=request.current_route_path())

        elif 'queue' in request.POST and aliquot_form.validate():
            for i, subform in enumerate(aliquot_form.aliquot.entries):
                apply_changes(subform.form, aliquot[i])
            queue_count = update_print_queue()
            if queue_count:
                request.session.flash(
                    u'Aliquot print queue has changed.', 'success')
            else:
                request.session.flash(u'Please select aliquot', 'warning')
            return HTTPFound(location=request.current_route_path())

        elif 'checkin' in request.POST and aliquot_form.validate():
            transitioned_count = 0
            state = (
                Session.query(models.AliquotState)
                .filter_by(name='checked-in')
                .one())
            for i, entry in enumerate(aliquot_form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
                if entry.ui_selected.data:
                    aliquot[i].state = state
                    transitioned_count += 1
            update_print_queue()
            if transitioned_count > 0:
                request.session.flash(
                    _(u'${count} aliquot have been changed to the status of ${state}.',
                        mapping={'count': transitioned_count,
                                 'state': state.title}),
                    'success')
            else:
                request.session.flash(u'Please select aliquot', 'warning')
            return HTTPFound(location=request.current_route_path())

        elif 'checkout' in request.POST and aliquot_form.validate():
            state = (
                Session.query(models.AliquotState)
                .filter_by(name='pending-checkout')
                .one())
            transitioned_count = 0
            for i, entry in enumerate(aliquot_form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
                if entry.ui_selected.data:
                    transitioned_count += 1
                    aliquot[i].state = state
            update_print_queue()
            if transitioned_count > 0:
                request.session.flash(
                    _(u'${count} aliquot have been changed to the status of ${state}.',
                        mapping={'count': transitioned_count,
                                 'state': state.title}),
                    'success')
            else:
                request.session.flash(u'Please select aliquot', 'warning')
            return HTTPFound(location=request.current_route_path())

        elif 'delete' in request.POST and aliquot_form.validate():
            deleted_count = 0
            for i, entry in enumerate(aliquot_form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
                if entry.ui_selected.data:
                    deleted_count += 1
                    Session.delete(aliquot[i])
            update_print_queue()
            if deleted_count > 0:
                request.session.flash(
                    _(u'${count} aliquot have been deleted.',
                        mapping={'count': deleted_count}),
                    'success')
            else:
                request.session.flash(
                    _(u'Please select Aliquot'),
                    'warning')
            return HTTPFound(location=request.current_route_path())

    return {
        'filter_form': aliquot_vals['filter_form'],
        'has_aliquot': aliquot_vals['has_aliquot'],
        'aliquot': aliquot_vals['aliquot'],
        'aliquot_pager': aliquot_vals['pager'],
        'aliquot_form': aliquot_form,

        'has_labels_queued': len(label_queue),
        'label_queue': label_queue,

        'has_specimen': specimen_vals['has_specimen'],
        'specimen': specimen_vals['specimen'],
        'specimen_pager': specimen_vals['pager'],
        'specimen_form': specimen_form,
    }


@view_config(
    route_name='lims.lab_checkout',
    permission='process',
    renderer='../templates/lab/checkout.pt')
def checkout(context, request):
    vals = filter_aliquot(context, request, state='pending-checkout')
    aliquot = vals['aliquot']

    available_locations = [
        (l.id, l.title)
        for l in Session.query(models.Location).order_by('title')]

    # TODO: the values in this form really should be in the crud form
    # since the receipt depends on the sent loation being unique.
    # If we ever do this, "bulk update" button won't be needed anymore
    class CheckoutForm(wtforms.Form):
        ui_selected = wtforms.BooleanField()
        id = wtforms.IntegerField(
            widget=wtforms.widgets.HiddenInput())
        location_id = wtforms.SelectField(
            choices=available_locations,
            coerce=int,
            validators=[
                wtforms.validators.DataRequired()])
        sent_date = DateField(
            validators=[wtforms.validators.Optional()])
        sent_name = wtforms.StringField(
            validators=[wtforms.validators.Optional()])
        sent_notes = wtforms.TextAreaField(
            validators=[wtforms.validators.Optional()])

    class CrudForm(wtforms.Form):
        aliquot = wtforms.FieldList(wtforms.FormField(CheckoutForm))

    form = CrudForm(request.POST, aliquot=aliquot)

    if request.method == 'POST' and check_csrf_token(request):

        if 'save' in request.POST and form.validate():
            for i, entry in enumerate(form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
            request.session.flash(_(u'Changed saved'), 'success')
            return HTTPFound(location=request.current_route_path())

        elif 'return' in request.POST and form.validate():
            state = (
                Session.query(models.AliquotState)
                .filter_by(name='checked-in')
                .one())
            updated_count = 0
            for i, entry in enumerate(form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
                if entry.ui_selected.data:
                    aliquot[i].location = context
                    aliquot[i].state = state
                    updated_count += 1
            Session.flush()
            if updated_count:
                request.session.flash(
                    _(u'${count} aliquot have been changed to the status of ${state}',
                        mapping={'count': updated_count, 'state': state.title}),
                    'success')
            else:
                request.session.flash(_(u'Please select Aliquot'), 'warning')
            return HTTPFound(location=request.current_route_path())

        elif 'complete' in request.POST and form.validate():
            state = (
                Session.query(models.AliquotState)
                .filter_by(name='checked-out')
                .one())
            updated_count = 0
            for i, entry in enumerate(form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
                if entry.ui_selected.data:
                    aliquot[i].state = state
                    updated_count += 1
            Session.flush()
            if updated_count:
                request.session.flash(
                    _(u'${count} aliquot have been changed to the status of ${state}',
                        mapping={'count': updated_count, 'state': state.title}),
                    'success')
            else:
                request.session.flash(_(u'Please select Aliquot'), 'warning')
            return HTTPFound(location=request.current_route_path())

    vals.update({
        'form': form,
    })

    return vals


@view_config(
    route_name='lims.lab_checkout_update',
    permission='process',
    renderer='../templates/lab/modal-checkout-bulk-update.pt')
def checkout_update(context, request):
    vals = filter_aliquot(context, request, state='pending-checkout')

    available_locations = [
        (l.id, l.title)
        for l in Session.query(models.Location).order_by('title')]

    class CheckoutForm(wtforms.Form):
        location_id = wtforms.SelectField(
            _('Lab Location'),
            description=_('The location of the aliquot'),
            choices=available_locations,
            coerce=int,
            validators=[
                wtforms.validators.DataRequired()])
        sent_date = DateField(
            _(u'Sent Date'),
            description=_(u'Date sent for analysis.'),
            validators=[wtforms.validators.Optional()])
        sent_name = wtforms.StringField(
            _(u'Sent Name '),
            description=_(u'The name of the aliquot\'s receiver.'),
            validators=[wtforms.validators.Optional()])
        sent_notes = wtforms.TextAreaField(
            _(u'Sent Notes '),
            description=_(u'Notes about this aliquot\'s destination'),
            validators=[wtforms.validators.Optional()])

    form = CheckoutForm(request.POST, location_id=context.id)

    if request.method == 'POST' and check_csrf_token(request):

        if 'save' in request.POST and form.validate():
            for sample in vals['full_query']:
                apply_changes(form, sample)
            request.session.flash(_(u'Changed saved'), 'success')
            return HTTPOk(json={
                '__next__': request.current_route_path(
                    _route_name='lims.lab_checkout')
            })

    vals.update({
        'form': form
    })

    return vals


@view_config(
    route_name='lims.lab_checkout_receipt',
    permission='process',
    renderer='../templates/lab/receipt.pt')
def checkout_receipt(context, request):
    vals = filter_aliquot(context, request, state='pending-checkout')

    try:
        sent_name = (
            Session.query(sa.distinct(models.Aliquot.sent_name))
            .select_from(vals['full_query'].subquery())
            .scalar())
    except orm.exc.MultipleResultsFound:
        sent_name = None

    try:
        location = (
            Session.query(models.Location)
            .join(vals['full_query'].subquery(), models.Location.aliquot)
            .one())
    except orm.exc.NoResultFound:
        location = None
    except orm.exc.MultipleResultsFound:
        location = None

    vals.update({
        'sent_name': sent_name,
        'location': location
    })

    return vals


@view_config(
    route_name='lims.lab_checkin',
    permission='process',
    renderer='../templates/lab/checkin.pt')
def checkin(context, request):
    vals = filter_aliquot(context, request, state='checked-out')
    aliquot = vals['aliquot']

    available_locations = [
        (l.id, l.title)
        for l in Session.query(models.Location).order_by('title')]

    class CheckinForm(wtforms.Form):
        ui_selected = wtforms.BooleanField()
        id = wtforms.IntegerField(
            widget=wtforms.widgets.HiddenInput())
        volume = wtforms.DecimalField(
            places=1,
            validators=[wtforms.validators.Optional()])
        cell_amount = wtforms.DecimalField(
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
                Session.query(models.AliquotState)
                .filter_by(name='checked-in')
                .one())
            updated_count = 0
            for i, entry in enumerate(form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
                if entry.ui_selected.data:
                    aliquot[i].location = context
                    aliquot[i].state = state
                    updated_count += 1
            Session.flush()
            if updated_count:
                request.session.flash(
                    _(u'${count} aliquot have been changed to the status of ${state}',
                        mapping={'count': updated_count, 'state': state.title}),
                    'success')
            else:
                request.session.flash(_(u'Please select Aliquot'), 'warning')
            return HTTPFound(location=request.current_route_path())

    vals.update({
        'form': form,
    })

    return vals
