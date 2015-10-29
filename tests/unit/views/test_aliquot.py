import pytest


@pytest.yield_fixture
def check_csrf_token():
    import mock
    name = 'occams_lims.views.aliquot.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class Test_aliquot_labels:

    def _call_fut(self, *args, **kw):
        from occams_lims.views.aliquot import aliquot_labels as view
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
        from occams_lims.views.aliquot import ALIQUOT_LABEL_QUEUE

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


class Test_filter_aliquot:

    def _call_fut(self, *args, **kw):
        from occams_lims.views.aliquot import filter_aliquot as view
        return view(*args, **kw)

    def test_filter_by_pid_found(self, req, db_session, factories):
        from webob.multidict import MultiDict

        pid = u'XXX-XXX-XX'
        state = u'pending'
        # Samole must be from the current working location
        location = factories.LocationFactory.create()
        factories.AliquotFactory.create(
            state__name=state,
            location=location,
            specimen__patient__pid=pid,
            specimen__location=location)
        db_session.flush()

        req.GET = MultiDict([('pid', pid)])
        res = self._call_fut(location, req, state)

        assert res['has_aliquot']

    def test_filter_by_pid_not_found(self, req, db_session, factories):
        from webob.multidict import MultiDict

        pid = u'XXX-XXX-XX'
        state = u'pending'
        # Sample must be from the current working location
        location = factories.LocationFactory.create()
        factories.AliquotFactory.create(
            state__name=state,
            location=location,
            specimen__patient__pid=pid,
            specimen__location=location)
        db_session.flush()

        req.GET = MultiDict([('pid', u'YYY-YYY-YY')])
        res = self._call_fut(location, req, state)

        assert not res['has_aliquot']
