from ddt import ddt, data

from tests import FunctionalFixture, USERID


@ddt
class TestLims(FunctionalFixture):

    def setUp(self):
        super(TestLims, self).setUp()

        from datetime import date

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from occams_lims import models as lims

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today()
            )

            Session.add(lims.Location(
                name=u'test_location',
                title=u'test_location_title',
                description=u'test_description',
                create_date=date.today(),
                sites=[site]
            ))

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12)
            )

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

            cycle = studies.Cycle(
                name=u'test_cycle',
                title=u'test_cycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            Session.add(lims.SpecimenType(
                name=u'test_specimen',
                title=u'test_specimen',
                studies=set([study]),
                cycles=set([cycle])
            ))

            Session.add(visit)

            Session.flush()

    @data('administrator', 'manager',
          'test_location:worker', 'test_location:member', None)
    def test_lims_view_list(self, group):
        url = '/lims'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ)

        self.assertEquals(200, response.status_code)

    def test_not_authenticated(self):
        url = '/lims'

        response = self.app.get(url, status='*')

        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker', 'test_location:member')
    def test_lims_lab_view(self, group):
        url = '/lims/test_location'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('fake_location:member')
    def test_not_allowed_lims_lab_view(self, group):
        url = '/lims/test_location'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_lims_lab_view(self):
        url = '/lims/test_location'

        response = self.app.get(url, status='*')
        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker')
    def test_lims_lab_post(self, group):
        url = '/lims/test_location'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        self.assertEquals(200, response.status_code)

    @data('test_location:member', 'fake_location:member')
    def test_not_allowed_lims_lab_post(self, group):
        url = '/lims/test_location'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_lims_lab_post(self):
        url = '/lims/test_location'

        response = self.app.post(url, status='*')
        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager', 'test_location:worker')
    def test_specimen_add(self, group):
        from occams import Session
        from occams_studies import models as studies
        from occams_lims import models as lims

        url = '/lims/test_location/addspecimen'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        cycle_id = Session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'test_cycle').scalar()

        specimen_id = Session.query(lims.SpecimenType.id).filter(
            lims.SpecimenType.name == u'test_specimen').scalar()

        data = {
            'pid': u'123',
            'cycle_id': cycle_id,
            'specimen_type_id': specimen_id
        }

        response = self.app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data('test_location:member', 'fake_location:worker')
    def test_not_allowed_specimen_add(self, group):
        from occams import Session
        from occams_studies import models as studies
        from occams_lims import models as lims

        url = '/lims/test_location/addspecimen'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        cycle_id = Session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'test_cycle').scalar()

        specimen_id = Session.query(lims.SpecimenType.id).filter(
            lims.SpecimenType.name == u'test_specimen').scalar()

        data = {
            'pid': u'123',
            'cycle_id': cycle_id,
            'specimen_type_id': specimen_id
        }

        response = self.app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_specimen_add(self):
        url = '/lims/test_location/addspecimen'

        self.app.post(url, status=401)

    @data('administrator', 'manager',
          'test_location:worker', 'test_location:member')
    def test_specimen_labels(self, group):
        url = '/lims/test_location/specimen_labels'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('fake_location:worker')
    def test_not_allowed_specimen_labels(self, group):
        url = '/lims/test_location/specimen_labels'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_specimen_labels(self):
        url = '/lims/test_location/specimen_labels'

        response = self.app.get(url, status='*')

        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker')
    def test_specimen_labels_post(self, group):
        url = '/lims/test_location/specimen_labels'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        self.assertEquals(200, response.status_code)

    @data('test_location:member', 'fake_location:member')
    def test_not_allowed_specimen_labels_post(self, group):
        url = '/lims/test_location/specimen_labels'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_specimen_labels_post(self):
        url = '/lims/test_location/specimen_labels'

        response = self.app.post(url, status='*')

        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker', 'test_location:member')
    def test_aliquot_labels(self, group):
        url = '/lims/test_location/aliquot_labels'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('fake_location:worker')
    def test_not_allowed_aliquot_labels(self, group):
        url = '/lims/test_location/aliquot_labels'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_aliquot_labels(self):
        url = '/lims/test_location/aliquot_labels'

        response = self.app.get(url, status='*')

        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker')
    def test_aliquot_labels_post(self, group):
        url = '/lims/test_location/aliquot_labels'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        self.assertEquals(200, response.status_code)

    @data('test_location:member', 'fake_location:member')
    def test_not_allowed_aliquot_labels_post(self, group):
        url = '/lims/test_location/aliquot_labels'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_aliquot_labels_post(self):
        url = '/lims/test_location/aliquot_labels'

        response = self.app.post(url, status='*')

        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker')
    def test_lab_batched(self, group):
        url = '/lims/test_location/batched'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('test_location:member', 'fake_location:worker')
    def test_not_allowed_lab_batched(self, group):
        url = '/lims/test_location/batched'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_batched(self):
        url = '/lims/test_location/batched'

        response = self.app.get(url, status='*')

        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker')
    def test_lab_ready(self, group):
        url = '/lims/test_location/ready'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('test_location:member', 'fake_location:worker')
    def test_not_allowed_lab_ready(self, group):
        url = '/lims/test_location/ready'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_lab_ready(self):
        url = '/lims/test_location/ready'

        response = self.app.get(url, status='*')

        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker')
    def test_lab_checkout(self, group):
        url = '/lims/test_location/checkout'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('test_location:member', 'fake_location:worker')
    def test_not_allowed_lab_checkout(self, group):
        url = '/lims/test_location/checkout'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_lab_checkout(self):
        url = '/lims/test_location/checkout'

        response = self.app.get(url, status='*')

        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker')
    def test_lab_checkout_update(self, group):
        url = '/lims/test_location/bulkupdate'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('test_location:member', 'fake_location:worker')
    def test_not_allowed_lab_checkout_update(self, group):
        url = '/lims/test_location/bulkupdate'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_lab_checkout_update(self):
        url = '/lims/test_location/bulkupdate'

        response = self.app.get(url, status='*')

        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker')
    def test_lab_checkout_receipt(self, group):
        url = '/lims/test_location/checkoutreceipt'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('test_location:member', 'fake_location:member')
    def test_not_allowed_lab_checkout_receipt(self, group):
        url = '/lims/test_location/checkoutreceipt'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_lab_checkout_receipt(self):
        url = '/lims/test_location/checkoutreceipt'

        response = self.app.get(url, status='*')

        self.assertEquals(401, response.status_code)

    @data('administrator', 'manager',
          'test_location:worker')
    def test_lab_checkin(self, group):
        url = '/lims/test_location/checkin'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('test_location:member', 'fake_location:worker')
    def test_not_allowed_lab_checkin(self, group):
        url = '/lims/test_location/checkin'

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(url, extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_lab_checkin(self):
        url = '/lims/test_location/checkin'

        response = self.app.get(url, status='*')

        self.assertEquals(401, response.status_code)
