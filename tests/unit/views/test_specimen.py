import pytest


@pytest.yield_fixture
def check_csrf_token():
    import mock
    name = 'occams_lims.views.specimen.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class Test_build_crud_form:

    def _make_one(self, *args, **kw):
        from occams_lims.views.specimen import build_crud_form
        return build_crud_form(*args, **kw)

    def test_collect_time_validate_24_hour(self, req, db_session):
        from datetime import time
        from webob.multidict import MultiDict

        Form = self._make_one(None, req)

        payload = MultiDict([
            ('specimen-0-collect_time', '13:00')
        ])

        form = Form(payload)
        form.validate()

        assert form.data['specimen'][0]['collect_time'] == time(13, 0)

    def test_collect_time_single_digit_hour(self, req, db_session):
        from datetime import time
        from webob.multidict import MultiDict

        Form = self._make_one(None, req)

        payload = MultiDict([
            ('specimen-0-collect_time', '1:00')
        ])

        form = Form(payload)
        form.validate()

        assert form.data['specimen'][0]['collect_time'] == time(1, 0)


class Test_filter_specimen:

    def _call_fut(self, *args, **kw):
        from occams_lims.views.specimen import filter_specimen as view
        return view(*args, **kw)

    def test_filter_by_pid_found(self, req, db_session, factories):
        from webob.multidict import MultiDict

        pid = u'XXX-XXX-XX'
        state = u'pending'
        # Sample must be from the current working location
        location = factories.LocationFactory.create()
        factories.SpecimenFactory.create(
            state__name=state,
            patient__pid=pid,
            location=location)
        db_session.flush()

        req.GET = MultiDict([('pid', pid)])
        res = self._call_fut(location, req, state)

        assert res['has_specimen']

    def test_filter_by_pid_not_found(self, req, db_session, factories):
        from webob.multidict import MultiDict

        pid = u'XXX-XXX-XX'
        state = u'pending'
        # Sample must be from the current working location
        location = factories.LocationFactory.create()
        factories.SpecimenFactory.create(
            state__name=state,
            patient__pid=pid,
            location=location)
        db_session.flush()

        req.GET = MultiDict([('pid', u'YYY-YYY-YY')])
        res = self._call_fut(location, req, state)

        assert not res['has_specimen']
