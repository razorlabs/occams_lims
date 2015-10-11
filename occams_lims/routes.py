# flake8: NOQA
# This module breaks my OCD-ness in favor of readability
from datetime import datetime
from . import log

from . import models


def includeme(config):
    """
    Helper method to configure available routes for the application
    """

    config.add_static_view('/lims/static',               'occams_lims:static', cache_max_age=3600)

    config.add_route('lims.main',                         '/lims',                                 factory=models.LabFactory)
    config.add_route('lims.lab',                          '/lims/{lab}',                           factory=models.LabFactory, traverse='/{lab}')
    # XXX: no edit yet becuase locations are hard-coded...
    config.add_route('lims.lab_edit',                     '/lims/{lab}/edit',                      factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.lab_specimen_add',             '/lims/{lab}/addspecimen',               factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.lab_specimen_labels',          '/lims/{lab}/specimen_labels',           factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.lab_aliquot_labels',           '/lims/{lab}/aliquot_labels',            factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.lab_ready',                    '/lims/{lab}/ready',                     factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.lab_checkout',                 '/lims/{lab}/checkout',                  factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.lab_checkout_update',          '/lims/{lab}/bulkupdate',                factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.lab_checkout_receipt',         '/lims/{lab}/checkoutreceipt',           factory=models.LabFactory, traverse='/{lab}')
    config.add_route('lims.lab_checkin',                  '/lims/{lab}/checkin',                   factory=models.LabFactory, traverse='/{lab}')

    log.debug('Routes configured')
