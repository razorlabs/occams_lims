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
        # Sample must be from the current working location
        location = factories.LocationFactory.create()
        factories.SpecimenFactory.create(
            state__name='pending-draw',
            patient__pid=pid,
            location=location)
        db_session.flush()

        req.GET = MultiDict([('pid', pid)])
        res = self._call_fut(location, req, state='pending-draw')

        assert res['has_specimen']

    def test_filter_by_pid_not_found(self, req, db_session, factories):
        from webob.multidict import MultiDict

        pid = u'XXX-XXX-XX'
        # Sample must be from the current working location
        location = factories.LocationFactory.create()
        factories.SpecimenFactory.create(
            state__name='pending-draw',
            patient__pid=pid,
            location=location)
        db_session.flush()

        req.GET = MultiDict([('pid', u'YYY-YYY-YY')])
        res = self._call_fut(location, req, state='pending-draw')

        assert not res['has_specimen']


class Test_specimen:

    def _call_fut(self, *args, **kw):
        from occams_lims.views.specimen import specimen as view
        return view(*args, **kw)

    def test_default_view(self, req, db_session, factories):
        """
        It should only display "pending-draw" specimen by default
        """
        from webob.multidict import MultiDict

        location = factories.LocationFactory.create()
        specimen1 = factories.SpecimenFactory.create(
            location=location,
            state__name='pending-draw',
        )
        factories.SpecimenFactory.create(
            location=location,
            state__name='pending-aliquot',
        )
        db_session.flush()

        req.GET = MultiDict()
        req.POST = MultiDict()
        context = specimen1.location
        context.request = req
        res = self._call_fut(context, req)

        assert len(res['specimen']) == 1
        assert res['specimen'][0] == specimen1

    def test_move_location_on_complete(self, req, db_session, factories):
        """
        It should move the specimen to the next location on complete.

        Presumably this is location at which the sample will be "processed".
        This was previously the "batched view" that was deprecated.
        """
        import mock
        from webob.multidict import MultiDict

        specimen = factories.SpecimenFactory.create(
            state__name='pending-draw',
        )
        next_location = factories.LocationFactory.create(
            is_enabled=True,
            active=True,
        )
        factories.SpecimenStateFactory.create(name='pending-aliquot')
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('specimen-0-ui_selected', '1'),
            ('specimen-0-id', str(specimen.id)),
            ('specimen-0-tubes', str(specimen.tubes)),
            ('specimen-0-collect_date', str(specimen.collect_date)),
            ('specimen-0-collect_time', '00:00'),
            ('specimen-0-location_id', str(next_location.id)),
            ('pending-aliquot', '1')
        ])

        context = specimen.location
        context.request = req
        res = self._call_fut(context, req)

        db_session.refresh(specimen)
        assert res.status_code == 302
        assert specimen.state.name == 'pending-aliquot'
        assert specimen.location == next_location

    def test_require_fields_on_complete(self, req, db_session, factories):
        """
        It should validate required fields when "completing" a sample
        """
        import mock
        from webob.multidict import MultiDict

        specimen = factories.SpecimenFactory.create(
            state__name='pending-draw',
        )
        next_location = factories.LocationFactory.create(
            is_enabled=True,
            active=True,
        )
        factories.SpecimenStateFactory.create(name='pending-aliquot')
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('specimen-0-ui_selected', '1'),
            ('specimen-0-id', str(specimen.id)),
            ('specimen-0-tubes', str(specimen.tubes)),
            ('specimen-0-collect_date', str(specimen.collect_date)),
            ('specimen-0-collect_time', ''),
            ('specimen-0-location_id', str(next_location.id)),
            ('pending-aliquot', '1')
        ])

        context = specimen.location
        context.request = req
        res = self._call_fut(context, req)

        db_session.refresh(specimen)

        assert isinstance(res, dict), 'Did not return tempalate values'
        assert 'required' in \
            res['form']['specimen'].entries[0]['collect_time'].errors[0]

    def test_no_required_data(self, req, db_session, factories):
        """
        It should not require input for collect_date and collect_time and
        location_id when data is saved
        """
        import mock
        from webob.multidict import MultiDict

        specimen = factories.SpecimenFactory.create(
            state__name='pending-draw',
        )

        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('specimen-0-ui_selected', '0'),
            ('specimen-0-id', str(specimen.id)),
            ('specimen-0-tubes', str(specimen.tubes)),
            ('specimen-0-collect_date', ''),
            ('specimen-0-collect_time', ''),
            ('specimen-0-location_id', ''),
            ('save', '1')
        ])

        context = specimen.location
        context.request = req
        res = self._call_fut(context, req)

        db_session.refresh(specimen)

        assert res.status_code == 302, 'Should be status code 302'
