import pytest

from occams.testing import make_environ, USERID, get_csrf_token


@pytest.fixture(autouse=True)
def transact(app, db_session, factories):
    import transaction

    # Any view-dependent data goes here
    # Webtests will use a different scope for its transaction
    with transaction.manager:
        db_session.info['blame'] = factories.UserFactory.create(key=USERID)
        db_session.flush()

        factories.LocationFactory.create(
            name='test_location',
            sites=[factories.SiteFactory.build()])

        factories.PatientFactory.create()

        cycle = factories.CycleFactory(
            name=u'test_cycle',
            study=factories.StudyFactory.build())
        factories.SpecimenTypeFactory.create(
            studies=set([cycle.study]),
            cycles=set([cycle]))

        db_session.flush()


@pytest.mark.parametrize('group', [
    'administrator', 'manager',
    'test_location:worker', 'test_location:member',
    None])
def test_lims_view_list(app, group):
    url = '/lims'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ)
    assert res.status_code == 200


def test_not_authenticated(app):
    url = '/lims'
    res = app.get(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager',
    'test_location:worker', 'test_location:member'])
def test_lims_lab_view(app, group):
    url = '/lims/test_location'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 200


@pytest.mark.parametrize('group', ['fake_location:member'])
def test_not_allowed_lims_lab_view(app, group):
    url = '/lims/test_location'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 403


def test_not_authenticated_lims_lab_view(app):
    url = '/lims/test_location'
    res = app.get(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker'])
def test_lims_lab_post(app, group):
    url = '/lims/test_location'

    environ = make_environ(userid=USERID, groups=[group])
    csrf_token = get_csrf_token(app, environ)

    res = app.post(
        url,
        extra_environ=environ,
        status='*',
        headers={
            'X-CSRF-Token': csrf_token,
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        })

    assert res.status_code == 200


@pytest.mark.parametrize('group', [
    'test_location:member', 'fake_location:member'])
def test_not_allowed_lims_lab_post(app, group):
    url = '/lims/test_location'

    environ = make_environ(userid=USERID, groups=[group])
    csrf_token = get_csrf_token(app, environ)

    res = app.post(
        url,
        extra_environ=environ,
        status='*',
        headers={
            'X-CSRF-Token': csrf_token,
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        })

    assert res.status_code == 403


def test_not_authenticated_lims_lab_post(app):
    url = '/lims/test_location'
    res = app.post(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker'])
def test_specimen_add(app, db_session, group):
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

    res = app.post_json(
        url,
        extra_environ=environ,
        status='*',
        headers={
            'X-CSRF-Token': csrf_token,
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        },
        params=data)

    assert res.status_code == 200


@pytest.mark.parametrize('group', [
    'test_location:member', 'fake_location:worker'])
def test_not_allowed_specimen_add(app, db_session, group):
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

    res = app.post_json(
        url,
        extra_environ=environ,
        status='*',
        headers={
            'X-CSRF-Token': csrf_token,
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        },
        params=data)

    assert res.status_code == 403


def test_not_authenticated_specimen_add(app):
    url = '/lims/test_location/addspecimen'
    app.post(url, status=401)


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker',
    'test_location:member'])
def test_specimen_labels(app, group):
    url = '/lims/test_location/specimen_labels'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 200


@pytest.mark.parametrize('group', ['fake_location:worker'])
def test_not_allowed_specimen_labels(app, group):
    url = '/lims/test_location/specimen_labels'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 403


def test_not_authenticated_specimen_labels(app):
    url = '/lims/test_location/specimen_labels'
    res = app.get(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker'])
def test_specimen_labels_post(app, group):
    url = '/lims/test_location/specimen_labels'
    environ = make_environ(userid=USERID, groups=[group])
    csrf_token = get_csrf_token(app, environ)
    res = app.post(
        url,
        extra_environ=environ,
        status='*',
        headers={
            'X-CSRF-Token': csrf_token,
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        })
    assert res.status_code == 200


@pytest.mark.parametrize('group', [
    'test_location:member', 'fake_location:member'])
def test_not_allowed_specimen_labels_post(app, group):
    url = '/lims/test_location/specimen_labels'
    environ = make_environ(userid=USERID, groups=[group])
    csrf_token = get_csrf_token(app, environ)
    res = app.post(
        url,
        extra_environ=environ,
        status='*',
        headers={
            'X-CSRF-Token': csrf_token,
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        })
    assert res.status_code == 403


def test_not_authenticated_specimen_labels_post(app):
    url = '/lims/test_location/specimen_labels'
    res = app.post(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker',
    'test_location:member'])
def test_aliquot_labels(app, group):
    url = '/lims/test_location/aliquot_labels'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 200


@pytest.mark.parametrize('group', ['fake_location:worker'])
def test_not_allowed_aliquot_labels(app, group):
    url = '/lims/test_location/aliquot_labels'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 403


def test_not_authenticated_aliquot_labels(app):
    url = '/lims/test_location/aliquot_labels'
    res = app.get(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker'])
def test_aliquot_labels_post(app, group):
    url = '/lims/test_location/aliquot_labels'
    environ = make_environ(userid=USERID, groups=[group])
    csrf_token = get_csrf_token(app, environ)
    res = app.post(
        url,
        extra_environ=environ,
        status='*',
        headers={
            'X-CSRF-Token': csrf_token,
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        })
    assert res.status_code == 200


@pytest.mark.parametrize('group', [
    'test_location:member', 'fake_location:member'])
def test_not_allowed_aliquot_labels_post(app, group):
    url = '/lims/test_location/aliquot_labels'
    environ = make_environ(userid=USERID, groups=[group])
    csrf_token = get_csrf_token(app, environ)
    res = app.post(
        url,
        extra_environ=environ,
        status='*',
        headers={
            'X-CSRF-Token': csrf_token,
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        })
    assert res.status_code == 403


def test_not_authenticated_aliquot_labels_post(app):
    url = '/lims/test_location/aliquot_labels'
    res = app.post(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker'])
def test_lab_ready(app, group):
    url = '/lims/test_location/ready'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 200


@pytest.mark.parametrize('group', [
    'test_location:member', 'fake_location:worker'])
def test_not_allowed_lab_ready(app, group):
    url = '/lims/test_location/ready'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 403


def test_not_authenticated_lab_ready(app):
    url = '/lims/test_location/ready'
    res = app.get(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker'])
def test_lab_checkout(app, group):
    url = '/lims/test_location/checkout'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 200


@pytest.mark.parametrize('group', [
    'test_location:member', 'fake_location:worker'])
def test_not_allowed_lab_checkout(app, group):
    url = '/lims/test_location/checkout'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 403


def test_not_authenticated_lab_checkout(app):
    url = '/lims/test_location/checkout'
    res = app.get(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker'])
def test_lab_checkout_update(app, group):
    url = '/lims/test_location/bulkupdate'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 200


@pytest.mark.parametrize('group', [
    'test_location:member', 'fake_location:worker'])
def test_not_allowed_lab_checkout_update(app, group):
    url = '/lims/test_location/bulkupdate'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 403


def test_not_authenticated_lab_checkout_update(app):
    url = '/lims/test_location/bulkupdate'
    res = app.get(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker'])
def test_lab_checkout_receipt(app, group):
    url = '/lims/test_location/checkoutreceipt'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 200


@pytest.mark.parametrize('group', [
    'test_location:member', 'fake_location:member'])
def test_not_allowed_lab_checkout_receipt(app, group):
    url = '/lims/test_location/checkoutreceipt'

    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 403


def test_not_authenticated_lab_checkout_receipt(app):
    url = '/lims/test_location/checkoutreceipt'
    res = app.get(url, status='*')
    assert res.status_code == 401


@pytest.mark.parametrize('group', [
    'administrator', 'manager', 'test_location:worker'])
def test_lab_checkin(app, group):
    url = '/lims/test_location/checkin'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 200


@pytest.mark.parametrize('group', [
    'test_location:member', 'fake_location:worker'])
def test_not_allowed_lab_checkin(app, group):
    url = '/lims/test_location/checkin'
    environ = make_environ(userid=USERID, groups=[group])
    res = app.get(url, extra_environ=environ, status='*')
    assert res.status_code == 403


def test_not_authenticated_lab_checkin(app):
    url = '/lims/test_location/checkin'
    res = app.get(url, status='*')
    assert res.status_code == 401
