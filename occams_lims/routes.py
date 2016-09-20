# flake8: NOQA
# This module breaks my OCD-ness in favor of readability
from datetime import datetime
from . import log

from . import models


def includeme(config):
    """
    Helper method to configure available routes for the application
    """

    config.add_static_view(path='occams_lims:static', name='/static', cache_max_age=3600)

    config.add_route('lims.index',              '',                        factory=models.LabFactory)
    config.add_route('lims.settings',           '/settings')  # Use OCCAMS's root factory

    config.add_route('lims.specimen',           '/{lab}',                  factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.specimen_labels',    '/{lab}/specimen_labels',  factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.add',                '/{lab}/add',              factory=models.LabFactory, traverse='/{lab}')

    config.add_route('lims.aliquot',            '/{lab}/aliquot',          factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.aliquot_labels',     '/{lab}/aliquot_labels',   factory=models.LabFactory, traverse='/{lab}')

    config.add_route('lims.checkout',           '/{lab}/checkout',         factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.checked-out',        '/{lab}/checked-out',       factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.checkout_update',    '/{lab}/bulkupdate',       factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.checkout_receipt',   '/{lab}/checkoutreceipt',  factory=models.LabFactory, traverse='/{lab}')

    config.add_route('lims.checkin',            '/{lab}/checkin',          factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.checked-in',         '/{lab}/checked-in',       factory=models.LabFactory, traverse='/{lab}')

    log.debug('Routes configured')
