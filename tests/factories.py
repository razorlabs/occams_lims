"""
Automated fake data factories declarations

Auto-populates data structures with fake data for testing.
Note that dependent structures are only implemented minimally.

Do not import this module directly, we've setup a fixture for this.
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory

from occams_datastore import models as datastore
from occams_studies import models as studies
from occams_lims import models


class FakeDescribable(factory.Factory):
    # It's really diffcult to generate a slug from a title in a random
    # test so just make a trully random name for the record
    name = factory.Faker('uuid4')
    title = factory.Faker('word')
    description = factory.Faker('paragraph')


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = datastore.User
    key = factory.Faker('email')


class SiteFactory(SQLAlchemyModelFactory, FakeDescribable):
    class Meta:
        model = studies.Site
    title = factory.Faker('city')


class PatientFactory(SQLAlchemyModelFactory):
    class Meta:
        model = studies.Patient
    site = factory.SubFactory(SiteFactory)
    pid = factory.Faker('uuid4')


class StudyFactory(SQLAlchemyModelFactory, FakeDescribable):
    class Meta:
        model = studies.Study
    short_title = factory.Faker('word')
    code = factory.Faker('credit_card_security_code')
    consent_date = factory.Faker('date_time_this_year')


class CycleFactory(SQLAlchemyModelFactory, FakeDescribable):
    class Meta:
        model = studies.Cycle
    title = factory.Faker('word')
    study = factory.SubFactory(StudyFactory)
    week = factory.Faker('pyint')


class EnrollmentFactory(SQLAlchemyModelFactory):
    class Meta:
        model = studies.Enrollment
    patient = factory.SubFactory(PatientFactory)
    study = factory.SubFactory(StudyFactory)
    reference_number = factory.Faker('ean8')
    consent_date = factory.Faker('date_time_this_year')
    latest_consent_date = factory.LazyAttribute(lambda o: o.consent_date)


class LocationFactory(SQLAlchemyModelFactory, FakeDescribable):
    class Meta:
        model = models.Location

    is_enabled = True
    active = True
    long_title1 = factory.Faker('company')
    long_title2 = factory.Faker('bs')
    address_street = factory.Faker('street_address')
    address_zip = factory.Faker('zipcode_plus4')
    phone_number = factory.Faker('phone_number')
    fax_number = factory.Faker('phone_number')


class SpecimenTypeFactory(SQLAlchemyModelFactory, FakeDescribable):
    class Meta:
        model = models.SpecimenType

    tube_type = factory.Faker('word')
    default_tubes = factory.Faker('pyint')
    # studies
    # cycles within study


class SpecimenStateFactory(SQLAlchemyModelFactory, FakeDescribable):
    class Meta:
        model = models.SpecimenState


class SpecialInstructionFactory(SQLAlchemyModelFactory, FakeDescribable):
    class Meta:
        model = models.SpecialInstruction


class SpecimenFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Specimen
    specimen_type = factory.SubFactory(SpecimenTypeFactory)
    patient = factory.SubFactory(PatientFactory)
    cycle = factory.SubFactory(CycleFactory)
    state = factory.SubFactory(SpecimenStateFactory)
    collect_date = factory.Faker('date_time_this_year')
    collect_time = factory.Faker('time')
    location = factory.SubFactory(LocationFactory)
    previous_location = factory.SubFactory(LocationFactory)
    tubes = factory.Faker('pyint')
    notes = factory.Faker('sentence')


class AliquotTypeFactory(SQLAlchemyModelFactory, FakeDescribable):
    class Meta:
        model = models.AliquotType
    specimen_type = factory.SubFactory(SpecimenTypeFactory)
    units = factory.Faker('random_element', elements=[u'mL', u'x10^6'])


class AliquotStateFactory(SQLAlchemyModelFactory, FakeDescribable):
    class Meta:
        model = models.AliquotState


class AliquotFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Aliquot
    specimen = factory.SubFactory(SpecimenFactory)
    aliquot_type = factory.SubFactory(AliquotTypeFactory)
    state = factory.SubFactory(AliquotStateFactory)
    labbook = factory.Faker('ean8')
    amount = factory.Faker('pydecimal')
    store_date = factory.Faker('date_time_this_year')
    freezer = factory.Faker('random_digit')
    rack = factory.Faker('random_digit')
    box = factory.Faker('random_digit')
    location = factory.SubFactory(LocationFactory)
    previous_location = factory.SubFactory(LocationFactory)
    thawed_num = factory.Faker('pyint')
    inventory_date = factory.LazyAttribute(lambda o: o.store_date)
    sent_date = factory.LazyAttribute(lambda o: o.store_date)
    sent_name = factory.Faker('name')
    sent_notes = factory.Faker('paragraph')
    special_instruction = factory.SubFactory(SpecialInstructionFactory)
