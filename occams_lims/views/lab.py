from pyramid.view import view_config

from .. import models


@view_config(
    route_name='lims.index',
    permission='view',
    renderer='../templates/lab/index.pt')
def index(context, request):
    """
    Displays available labs to the authenticated user
    """
    db_session = request.db_session

    query = (
        db_session.query(models.Location)
        .filter_by(is_enabled=True)
        .order_by(models.Location.title))

    locations_count = query.count()

    return {
        'labs': query,
        'labs_count': locations_count
    }
