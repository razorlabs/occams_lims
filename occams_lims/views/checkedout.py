from pyramid.view import view_config

from .aliquot import filter_aliquot


@view_config(
    route_name='lims.checked-out',
    permission='process',
    renderer='../templates/checked-out/checked-out.pt')
def checked_out(context, request):
    vals = filter_aliquot(context, request, state='checked-out')
    return vals
