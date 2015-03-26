"""
Pyramid-specific events
"""

from pyramid.events import subscriber, NewResponse, NewRequest, BeforeRender

from . import Session, models
from .views import lab as lab_views


@subscriber(NewResponse)
def vary_json(event):
    """
    Prevent browser from overwriting HTML with JSON from the same URL.
    More info: http://stackoverflow.com/a/1975677/148781
    """
    if event.request.is_xhr:
        event.response.vary = 'Accept'


@subscriber(NewRequest)
def track_user_on_request(event):
    """
    Annotates the database session with the current user.
    """
    request = event.request

    # Keep track of the request so we can generate model URLs
    Session.info['request'] = request

    if request.authenticated_userid is not None:
        Session.info['blame'] = (
            Session.query(models.User)
            .filter_by(key=request.authenticated_userid)
            .one())

    # Store the CSRF token in a cookie since we'll need to sent it back
    # frequently in single-page views.
    # https://docs.djangoproject.com/en/dev/ref/contrib/csrf/
    # The attacker cannot read or change the value of the cookie due to the
    # same-origin policy, and thus cannot guess the right GET/POST parameter
    request.response.set_cookie('csrf_token', request.session.get_csrf_token())


@subscriber(BeforeRender)
def add_labs(event):
    """
    Inject studies listing into Chameleon template variables to render menu.
    """
    if event['renderer_info'].type != '.pt':
        return

    if 'labs' not in event:
        request = event['request']
        context = models.LabFactory(request)
        event['available_labs'] = lab_views.list_(context, request)['labs']
