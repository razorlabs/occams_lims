"""
Pyramid-specific events
"""

from pyramid.events import subscriber, BeforeRender

from . import models
from .views import lab


@subscriber(BeforeRender)
def add_labs(event):
    """
    Inject studies listing into Chameleon template variables to render menu.
    """
    if event['renderer_info'].type != '.pt':
        return

    if 'labs' not in event:
        request = event['request']
        if request is None:
            return
        context = models.LabFactory(request)
        event['available_labs'] = lab.index(context, request)['labs']
