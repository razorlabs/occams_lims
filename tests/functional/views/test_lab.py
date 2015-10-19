import pytest

from occams.testing import make_environ, USERID, get_csrf_token


class TestPermissions:

    @pytest.fixture(autouse=True)
    def transact(self, app, db_session):

        from datetime import date

        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from occams_lims import models as lims

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today()
            )

            db_session.add(lims.Location(
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

            db_session.add(studies.Enrollment(
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

            db_session.add(lims.SpecimenType(
                name=u'test_specimen',
                title=u'test_specimen',
                studies=set([study]),
                cycles=set([cycle])
            ))

            db_session.add(visit)

            db_session.flush()

    @pytest.mark.parametrize('group', [
        'administrator', 'manager',
        'test_location:worker', 'test_location:member',
        None])
    def test_lims_view_list(self, app, group):
        url = '/lims'

        environ = make_environ(userid=USERID, groups=[group])
        response = app.get(url, extra_environ=environ)

        assert response.status_code == 200

    def test_not_authenticated(self, app):
        url = '/lims'

        response = app.get(url, status='*')

        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager',
        'test_location:worker', 'test_location:member'])
    def test_lims_lab_view(self, app, group):
        url = '/lims/test_location'

        environ = make_environ(userid=USERID, groups=[group])
        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 200

    @pytest.mark.parametrize('group', ['fake_location:member'])
    def test_not_allowed_lims_lab_view(self, app, group):
        url = '/lims/test_location'

        environ = make_environ(userid=USERID, groups=[group])
        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 403

    def test_not_authenticated_lims_lab_view(self, app):
        url = '/lims/test_location'

        response = app.get(url, status='*')
        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker'])
    def test_lims_lab_post(self, app, group):
        url = '/lims/test_location'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        response = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        assert response.status_code == 200

    @pytest.mark.parametrize('group', [
        'test_location:member', 'fake_location:member'])
    def test_not_allowed_lims_lab_post(self, app, group):
        url = '/lims/test_location'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        response = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        assert response.status_code == 403

    def test_not_authenticated_lims_lab_post(self, app):
        url = '/lims/test_location'

        response = app.post(url, status='*')
        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker'])
    def test_specimen_add(self, app, db_session, group):
        from occams_studies import models as studies
        from occams_lims import models as lims

        url = '/lims/test_location/addspecimen'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        cycle_id = db_session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'test_cycle').scalar()

        specimen_id = db_session.query(lims.SpecimenType.id).filter(
            lims.SpecimenType.name == u'test_specimen').scalar()

        data = {
            'pid': u'123',
            'cycle_id': cycle_id,
            'specimen_type_id': specimen_id
        }

        response = app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert response.status_code == 200

    @pytest.mark.parametrize('group', [
        'test_location:member', 'fake_location:worker'])
    def test_not_allowed_specimen_add(self, app, db_session, group):
        from occams_studies import models as studies
        from occams_lims import models as lims

        url = '/lims/test_location/addspecimen'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        cycle_id = db_session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'test_cycle').scalar()

        specimen_id = db_session.query(lims.SpecimenType.id).filter(
            lims.SpecimenType.name == u'test_specimen').scalar()

        data = {
            'pid': u'123',
            'cycle_id': cycle_id,
            'specimen_type_id': specimen_id
        }

        response = app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert response.status_code == 403

    def test_not_authenticated_specimen_add(self, app):
        url = '/lims/test_location/addspecimen'

        app.post(url, status=401)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker',
        'test_location:member'])
    def test_specimen_labels(self, app, group):
        url = '/lims/test_location/specimen_labels'

        environ = make_environ(userid=USERID, groups=[group])
        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 200

    @pytest.mark.parametrize('group', ['fake_location:worker'])
    def test_not_allowed_specimen_labels(self, app, group):
        url = '/lims/test_location/specimen_labels'

        environ = make_environ(userid=USERID, groups=[group])
        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 403

    def test_not_authenticated_specimen_labels(self, app):
        url = '/lims/test_location/specimen_labels'

        response = app.get(url, status='*')

        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker'])
    def test_specimen_labels_post(self, app, group):
        url = '/lims/test_location/specimen_labels'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        response = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        assert response.status_code == 200

    @pytest.mark.parametrize('group', [
        'test_location:member', 'fake_location:member'])
    def test_not_allowed_specimen_labels_post(self, app, group):
        url = '/lims/test_location/specimen_labels'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        response = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        assert response.status_code == 403

    def test_not_authenticated_specimen_labels_post(self, app):
        url = '/lims/test_location/specimen_labels'

        response = app.post(url, status='*')

        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker',
        'test_location:member'])
    def test_aliquot_labels(self, app, group):
        url = '/lims/test_location/aliquot_labels'

        environ = make_environ(userid=USERID, groups=[group])
        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 200

    @pytest.mark.parametrize('group', ['fake_location:worker'])
    def test_not_allowed_aliquot_labels(self, app, group):
        url = '/lims/test_location/aliquot_labels'

        environ = make_environ(userid=USERID, groups=[group])
        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 403

    def test_not_authenticated_aliquot_labels(self, app):
        url = '/lims/test_location/aliquot_labels'

        response = app.get(url, status='*')

        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker'])
    def test_aliquot_labels_post(self, app, group):
        url = '/lims/test_location/aliquot_labels'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        response = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        assert response.status_code == 200

    @pytest.mark.parametrize('group', [
        'test_location:member', 'fake_location:member'])
    def test_not_allowed_aliquot_labels_post(self, app, group):
        url = '/lims/test_location/aliquot_labels'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        response = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })

        assert response.status_code == 403

    def test_not_authenticated_aliquot_labels_post(self, app):
        url = '/lims/test_location/aliquot_labels'

        response = app.post(url, status='*')

        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker'])
    def test_lab_ready(self, app, group):
        url = '/lims/test_location/ready'

        environ = make_environ(userid=USERID, groups=[group])

        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 200

    @pytest.mark.parametrize('group', [
        'test_location:member', 'fake_location:worker'])
    def test_not_allowed_lab_ready(self, app, group):
        url = '/lims/test_location/ready'

        environ = make_environ(userid=USERID, groups=[group])

        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 403

    def test_not_authenticated_lab_ready(self, app):
        url = '/lims/test_location/ready'

        response = app.get(url, status='*')

        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker'])
    def test_lab_checkout(self, app, group):
        url = '/lims/test_location/checkout'

        environ = make_environ(userid=USERID, groups=[group])

        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 200

    @pytest.mark.parametrize('group', [
        'test_location:member', 'fake_location:worker'])
    def test_not_allowed_lab_checkout(self, app, group):
        url = '/lims/test_location/checkout'

        environ = make_environ(userid=USERID, groups=[group])

        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 403

    def test_not_authenticated_lab_checkout(self, app):
        url = '/lims/test_location/checkout'

        response = app.get(url, status='*')

        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker'])
    def test_lab_checkout_update(self, app, group):
        url = '/lims/test_location/bulkupdate'

        environ = make_environ(userid=USERID, groups=[group])

        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 200

    @pytest.mark.parametrize('group', [
        'test_location:member', 'fake_location:worker'])
    def test_not_allowed_lab_checkout_update(self, app, group):
        url = '/lims/test_location/bulkupdate'

        environ = make_environ(userid=USERID, groups=[group])

        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 403

    def test_not_authenticated_lab_checkout_update(self, app):
        url = '/lims/test_location/bulkupdate'

        response = app.get(url, status='*')

        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker'])
    def test_lab_checkout_receipt(self, app, group):
        url = '/lims/test_location/checkoutreceipt'

        environ = make_environ(userid=USERID, groups=[group])

        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 200

    @pytest.mark.parametrize('group', [
        'test_location:member', 'fake_location:member'])
    def test_not_allowed_lab_checkout_receipt(self, app, group):
        url = '/lims/test_location/checkoutreceipt'

        environ = make_environ(userid=USERID, groups=[group])

        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 403

    def test_not_authenticated_lab_checkout_receipt(self, app):
        url = '/lims/test_location/checkoutreceipt'

        response = app.get(url, status='*')

        assert response.status_code == 401

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'test_location:worker'])
    def test_lab_checkin(self, app, group):
        url = '/lims/test_location/checkin'

        environ = make_environ(userid=USERID, groups=[group])

        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 200

    @pytest.mark.parametrize('group', [
        'test_location:member', 'fake_location:worker'])
    def test_not_allowed_lab_checkin(self, app, group):
        url = '/lims/test_location/checkin'

        environ = make_environ(userid=USERID, groups=[group])

        response = app.get(url, extra_environ=environ, status='*')

        assert response.status_code == 403

    def test_not_authenticated_lab_checkin(self, app):
        url = '/lims/test_location/checkin'

        response = app.get(url, status='*')

        assert response.status_code == 401
