# flake8: NOQA
# This module breaks my OCD-ness in favor of readability
from datetime import datetime
from . import log

from . import models


def includeme(config):
    """
    Helper method to configure available routes for the application
    """

    config.add_static_view('/lims/static',      'occams_lims:static', cache_max_age=3600)

    config.add_route('lims.index',              '/lims',                        factory=models.LabFactory)

    config.add_route('lims.specimen',           '/lims/{lab}',                  factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.specimen_labels',    '/lims/{lab}/specimen_labels',  factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.add',                '/lims/{lab}/add',              factory=models.LabFactory, traverse='/{lab}')

    config.add_route('lims.aliquot',            '/lims/{lab}/aliquot',          factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.aliquot_labels',     '/lims/{lab}/aliquot_labels',   factory=models.LabFactory, traverse='/{lab}')

    config.add_route('lims.checkout',           '/lims/{lab}/checkout',         factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.checkout_update',    '/lims/{lab}/bulkupdate',       factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.checkout_receipt',   '/lims/{lab}/checkoutreceipt',  factory=models.LabFactory, traverse='/{lab}')

    config.add_route('lims.checkin',            '/lims/{lab}/checkin',          factory=models.LabFactory, traverse='/{lab}')

    log.debug('Routes configured')
