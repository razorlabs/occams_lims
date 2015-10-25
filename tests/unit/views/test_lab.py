import pytest


@pytest.yield_fixture
def check_csrf_token():
    import mock
    name = 'occams_lims.views.lab.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class Test_build_crud_form:

    def _make_one(self, *args, **kw):
        from occams_lims.views.lab import build_crud_form
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


class Test_aliquot_labels:

    def _call_fut(self, *args, **kw):
        from occams_lims.views.lab import aliquot_labels as view
        return view(*args, **kw)

    def test_print_when_not_allowed(
            self, req, db_session, config, factories, check_csrf_token):
        from pyramid.httpexceptions import HTTPForbidden
        from webob.multidict import MultiDict

        context = None
        config.testing_securitypolicy(permissive=False)
        req.method = 'POST'
        req.POST = MultiDict()

        with pytest.raises(HTTPForbidden):
            self._call_fut(context, req)

    def test_print_when_allowed(
            self, req, db_session, config, factories, check_csrf_token):
        from webob.multidict import MultiDict
        from occams_lims.views.lab import ALIQUOT_LABEL_QUEUE

        aliquot = factories.AliquotFactory.create()
        db_session.flush()

        context = aliquot.location
        config.testing_securitypolicy(permissive=True)
        req.session[ALIQUOT_LABEL_QUEUE] = set([aliquot.id])
        req.method = 'POST'
        req.POST = MultiDict([('print', '')])
        res = self._call_fut(context, req)

        assert res.content_type == 'application/pdf'
        assert len(req.session[ALIQUOT_LABEL_QUEUE]) == 0
