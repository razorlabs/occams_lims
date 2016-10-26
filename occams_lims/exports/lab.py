"""
Patient aliquot report.

Formerly: avrcdataexport/sql/additional/SpecimenAliquot.sql
"""


#
# BBB: Lab is not part of the studies app, but needs to be
#      generated anyway until we can implement LIMS, in which
#      case it'll have it's own export page/process in that app.
#


from sqlalchemy import func, null
from sqlalchemy.orm import aliased

from occams_studies.exports.plan import ExportPlan
from occams_studies.exports.codebook import row, types
from occams_studies import models as studies

from .. import models as lims


class LabPlan(ExportPlan):

    name = 'SpecimenAliquot'

    title = 'Specimen'

    def codebook(self):
        return iter([
            row('aliquot_type', self.name, types.STRING,
                is_required=True, is_system=True),
            row('store_date', self.name, types.DATE, is_system=True),
            row('amount', self.name, types.NUMBER, is_system=True),
            row('units', self.name, types.STRING, is_system=True),
            row('aliquot_location', self.name, types.STRING, is_system=True),
            row('freezer', self.name, types.STRING, is_system=True),
            row('rack', self.name, types.STRING, is_system=True),
            row('box', self.name, types.STRING, is_system=True),
            row('aliquot_count', self.name, types.NUMBER, decimal_places=0,
                is_required=True, is_system=True),
            row('aliquot_state', self.name, types.STRING,
                is_required=True, is_system=True),
            row('sent_date', self.name, types.DATE, is_system=True),
            row('sent_name', self.name, types.STRING, is_system=True),
            row('sent_notes', self.name, types.STRING, is_system=True),
            row('thawed_num', self.name, types.NUMBER, decimal_places=0,
                is_system=True),
            row('inventory_date', self.name, types.DATE, is_system=True),
            row('aliquot_notes', self.name, types.STRING, is_system=True),
            row('specimen_type', self.name, types.STRING,
                is_required=True, is_system=True),
            row('collect_time', self.name, types.TIME, is_system=True),
            row('collect_date', self.name, types.DATE, is_system=True),
            row('specimen_study', self.name, types.STRING, is_system=True),
            row('specimen_cycle', self.name, types.STRING, is_system=True),
            row('specimen_destination', self.name, types.STRING,
                is_system=True),
            row('specimen_state', self.name, types.STRING, is_system=True),
            row('tubes', self.name, types.NUMBER, decimal_places=0,
                is_system=True),
            row('tube_type', self.name, types.STRING, is_system=True),
            row('specimen_notes', self.name, types.STRING, is_system=True),
            row('site', self.name, types.STRING,
                is_required=True, is_system=True),
            row('pid', self.name, types.STRING,
                is_required=True, is_system=True),
            row('our', self.name, types.STRING,
                is_required=True, is_system=True),
            row('nurse_email', self.name, types.STRING, is_system=True),
            row('aeh_num', self.name, types.STRING, is_system=True)
            ])

    def data(self,
             use_choice_labels=False,
             expand_collections=False,
             ignore_private=True):

        session = self.db_session

        AliquotLocation = aliased(lims.Location)
        SpecimenLocation = aliased(lims.Location)

        query = (
            session.query(
                lims.AliquotType.title.label('aliquot_type'),
                lims.Aliquot.collect_date.label('store_date'),
                lims.Aliquot.amount.label('amount'),
                lims.AliquotType.units.label('units'),
                AliquotLocation.title.label('aliquot_location'),
                lims.Aliquot.freezer.label('freezer'),
                lims.Aliquot.rack.label('rack'),
                lims.Aliquot.box.label('box'),
                func.count().label('aliquot_count'),
                lims.AliquotState.title.label('aliquot_state'),
                lims.Aliquot.sent_date.label('sent_date'),
                lims.Aliquot.sent_name.label('sent_name'),
                lims.Aliquot.sent_notes.label('sent_notes'),
                lims.Aliquot.thawed_num.label('thawed_num'),
                lims.Aliquot.inventory_date.label('inventory_date'),
                lims.Aliquot.notes.label('aliquot_notes'),
                lims.SpecimenType.title.label('specimen_type'),
                lims.Specimen.collect_time.label('collect_time'),
                lims.Specimen.collect_date.label('collect_date'),
                studies.Study.title.label('specimen_study'),
                studies.Cycle.week.label('specimen_cycle'),
                SpecimenLocation.title.label('specimen_destination'),
                lims.SpecimenState.title.label('specimen_state'),
                lims.Specimen.tubes.label('tubes'),
                lims.SpecimenType.tube_type.label('tube_type'),
                lims.Specimen.notes.label('specimen_notes'),
                studies.Site.name.label('site'),
                studies.Patient.pid.label('pid'),
                studies.Patient.pid.label('our'),
                studies.Patient.nurse.label('nurse_email'),
                (session.query(studies.PatientReference.reference_number)
                 .join(studies.ReferenceType)
                 .filter(studies.ReferenceType.name == u'aeh_num')
                 .filter(
                    studies.PatientReference.patient_id == studies.Patient.id)
                 .limit(1)
                 .correlate(studies.Patient)
                 .as_scalar()
                 .label('aeh_num')))
            .select_from(lims.Aliquot)
            .join(lims.Aliquot.specimen)
            .outerjoin(lims.Aliquot.aliquot_type)
            .outerjoin(lims.Aliquot.state)
            .outerjoin(AliquotLocation, lims.Aliquot.location)
            .outerjoin(SpecimenLocation, lims.Specimen.location)
            .outerjoin(lims.Specimen.cycle)
            .outerjoin(studies.Cycle.study)
            .outerjoin(lims.Specimen.specimen_type)
            .outerjoin(lims.Specimen.state)
            .join(lims.Specimen.patient)
            .join(studies.Patient.site)
            .filter(lims.AliquotState.title != u'Aliquot Not used')
            .filter(func.coalesce(lims.Aliquot.freezer,
                                  lims.Aliquot.rack,
                                  lims.Aliquot.box) != null())
            .group_by(
                lims.AliquotType.title,
                lims.Aliquot.collect_date,
                lims.Aliquot.amount,
                lims.AliquotType.units,
                AliquotLocation.title,
                lims.Aliquot.freezer,
                lims.Aliquot.rack,
                lims.Aliquot.box,
                lims.AliquotState.title,
                lims.Aliquot.sent_date,
                lims.Aliquot.sent_name,
                lims.Aliquot.sent_notes,
                lims.Aliquot.thawed_num,
                lims.Aliquot.inventory_date,
                lims.Aliquot.notes,
                lims.SpecimenType.title,
                lims.Specimen.collect_time,
                lims.Specimen.collect_date,
                studies.Study.title,
                studies.Cycle.week,
                SpecimenLocation.title,
                lims.SpecimenState.title,
                lims.Specimen.tubes,
                lims.SpecimenType.tube_type,
                lims.Specimen.notes,
                studies.Patient.id,
                studies.Patient.pid,
                studies.Patient.nurse,
                'aeh_num',
                studies.Site.name))

        return query
