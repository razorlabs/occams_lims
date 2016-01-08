import pytest


@pytest.yield_fixture
def check_csrf_token():
    import mock
    name = 'occams_lims.views.checkin.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class Test_checkin:

    def _call_fut(self, *args, **kw):
        from occams_lims.views.checkin import checkin as view
        return view(*args, **kw)

    def test_no_required_data(self, req, db_session, factories):
        """
        It should not require input for collect_date and collect_time and
        location_id when data is saved
        """
        import mock
        from webob.multidict import MultiDict

        aliquot = factories.AliquotFactory.create(
            specimen__state__name='complete',
            state__name='checked-out',
            amount=None
        )

        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('aliquot-0-ui_selected', 'false'),
            ('aliquot-0-id', str(aliquot.id)),
            ('aliquot-0-amount', ''),
            ('save', '1')
        ])
        context = aliquot.location
        context.request = req
        res = self._call_fut(context, req)

        assert res.status_code == 302, 'Should be status code 302'

    def test_required_on_transition(self, req, db_session, factories):
        """
        It should require amount on state transition
        """
        import mock
        from webob.multidict import MultiDict

        aliquot = factories.AliquotFactory.create(
            specimen__state__name='complete',
            state__name='checked-out',
            amount=None
        )

        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('aliquot-0-ui_selected', 'true'),
            ('aliquot-0-id', str(aliquot.id)),
            ('aliquot-0-amount', ''),
            ('checkin', '1')
        ])
        context = aliquot.location
        context.request = req
        res = self._call_fut(context, req)

        assert 'required' in res['form'].aliquot.entries[0].amount.errors[0]
