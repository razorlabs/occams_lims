from itertools import chain

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.platypus import \
    SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from pyramid.httpexceptions import HTTPFound, HTTPOk
from pyramid.response import FileIter
from pyramid.view import view_config
from pyramid.session import check_csrf_token
import six
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from wtforms.ext.dateutil.fields import DateField

from occams.utils.forms import apply_changes

from .. import _, models
from .aliquot import filter_aliquot


@view_config(
    route_name='lims.checkout',
    permission='process',
    renderer='../templates/checkout/checkout.pt')
def checkout(context, request):
    db_session = request.db_session
    vals = filter_aliquot(context, request, state='pending-checkout')
    aliquot = vals['aliquot']

    available_locations = [
        (l.id, l.title)
        for l in db_session.query(models.Location).order_by('title')]

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
                    _(u'${count} aliquot have been changed to the status '
                      u'of ${state}',
                        mapping={
                            'count': updated_count,
                            'state': state.title
                        }),
                    'success')
            else:
                request.session.flash(_(u'Please select Aliquot'), 'warning')
            return HTTPFound(location=request.current_route_path())

        elif 'complete' in request.POST and form.validate():
            state = (
                db_session.query(models.AliquotState)
                .filter_by(name='checked-out')
                .one())
            updated_count = 0
            for i, entry in enumerate(form.aliquot.entries):
                apply_changes(entry.form, aliquot[i])
                if entry.ui_selected.data:
                    aliquot[i].state = state
                    updated_count += 1
            db_session.flush()
            if updated_count:
                request.session.flash(
                    _(u'${count} aliquot have been changed to the status '
                      u'of ${state}',
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
    route_name='lims.checkout_update',
    permission='process',
    renderer='../templates/checkout/modal-checkout-bulk-update.pt')
def checkout_update(context, request):
    db_session = request.db_session
    vals = filter_aliquot(context, request, state='pending-checkout')

    available_locations = [
        (l.id, l.title)
        for l in db_session.query(models.Location).order_by('title')]

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
                    _route_name='lims.checkout')
            })

    vals.update({
        'form': form
    })

    return vals


@view_config(
    route_name='lims.checkout_receipt',
    permission='process')
def checkout_receipt(context, request):
    db_session = request.db_session
    results = filter_aliquot(context, request, state='pending-checkout')
    query = results['full_query']

    try:
        sent_name = (
            db_session.query(sa.distinct(models.Aliquot.sent_name))
            .select_from(query.subquery())
            .scalar())
    except orm.exc.MultipleResultsFound:
        sent_name = None

    try:
        location = (
            db_session.query(models.Location)
            .join(query.subquery(), models.Location.aliquot)
            .one())
    except orm.exc.NoResultFound:
        location = None
    except orm.exc.MultipleResultsFound:
        location = None

    fp = six.StringIO()

    doc = SimpleDocTemplate(
        fp,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=18)
    doc.pagesize = letter
    elements = []
    styles = getSampleStyleSheet()
    paragraph_style = styles['Normal']

    if location:
        elements.append(Paragraph(_('Send to:'), paragraph_style))
        if sent_name:
            elements.append(Paragraph(sent_name, paragraph_style))
        if location.long_title1:
            elements.append(Paragraph(location.long_title1, paragraph_style))
        if location.long_title2:
            elements.append(Paragraph(location.long_title2, paragraph_style))
        if location.address_street:
            elements.append(
                Paragraph(location.address_street, paragraph_style))
        if location.address_city and \
                location.address_state and location.address_zip:
            elements.append(Paragraph('{0}, {1} {2}'.format(
                location.address_city, location.address_state,
                location.address_zip), paragraph_style))
        if location.phone_number:
            elements.append(Paragraph(location.phone_number, paragraph_style))
        if location.fax_number:
            elements.append(Paragraph(location.fax_number, paragraph_style))
    else:
        elements.append(
            Paragraph(_(
                u'Multiple send locations were found. '
                u'Please update your aliquot, or change your filter.'
            ), paragraph_style))

    elements.append(Spacer(1, 12))

    # TODO: Get this line right instead of just copying it from the docs
    style = TableStyle([
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.green),
        ('INNERGRID', (0, 0), (-1, -1), 0.25,  colors.black),
        ('BOX', (0, 0), (-1, -1),  0.25,  colors.black),
    ])

    # Configure style and word wrap
    s = getSampleStyleSheet()
    s = s['BodyText']
    s.wordWrap = 'CJK'

    header = [[
        _(u'ID'), _(u'PID'), _(u'Study / Week'), _(u'Store Date'),
        _(u'Type'), _(u'Amount'), _(u'Notes')
    ]]

    rows = chain(header, iter([
        six.text_type(sample.id),
        six.text_type(sample.specimen.patient.pid),
        u'{0} - {1}'.format(
            sample.specimen.cycle.study.short_title,
            sample.specimen.cycle.week),
        sample.store_date.isoformat(),
        sample.aliquot_type.title,
        u'{0}{1}'.format(
            six.text_type(sample.amount or u'--'),
            sample.aliquot_type.units or u''),
        '{0}\n{1}'.format(sample.notes or '', sample.sent_notes or '')
        ] for sample in query
    ))

    data = [[Paragraph(cell, s) for cell in row] for row in rows]
    t = Table(data)
    t.setStyle(style)

    # Send the data and build the file
    elements.append(t)
    doc.build(elements)
    fp.flush()

    fp.seek(0)

    response = request.response
    response.content_type = 'application/pdf'
    response.content_disposition = 'attachment;filename=receipt.pdf'
    response.app_iter = FileIter(fp)
    return response
