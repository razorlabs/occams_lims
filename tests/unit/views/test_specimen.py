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
