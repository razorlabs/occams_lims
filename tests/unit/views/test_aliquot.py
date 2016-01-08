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


class Test_make_aliquot_label:

    def _call_fut(self, *args, **kw):
        from occams_lims.views.aliquot import make_aliquot_label
        return make_aliquot_label(*args, **kw)

    def test_add_enrollment_number(self, db_session, factories):
        aliquot = factories.AliquotFactory.create()
        enrollment = factories.EnrollmentFactory.create(
            patient=aliquot.specimen.patient,
            study=aliquot.specimen.cycle.study,
            consent_date=aliquot.specimen.collect_date)
        db_session.flush()

        res = self._call_fut(aliquot)
        assert enrollment.reference_number in res[1][1]

    def test_ignore_multiple_enrollment_numbers(self, db_session, factories):
        from datetime import timedelta
        aliquot = factories.AliquotFactory.create()
        enrollment1 = factories.EnrollmentFactory.create(
            patient=aliquot.specimen.patient,
            study=aliquot.specimen.cycle.study,
            consent_date=aliquot.specimen.collect_date)
        enrollment2 = factories.EnrollmentFactory.create(
            patient=aliquot.specimen.patient,
            study=aliquot.specimen.cycle.study,
            consent_date=aliquot.specimen.collect_date + timedelta(days=1))
        db_session.flush()

        res = self._call_fut(aliquot)
        assert enrollment2.reference_number not in res[1][1]
        assert enrollment1.reference_number not in res[1][1]


class Test_filter_aliquot:

    def _call_fut(self, *args, **kw):
        from occams_lims.views.aliquot import filter_aliquot as view
        return view(*args, **kw)

    def test_filter_by_pid_found(self, req, db_session, factories):
        from webob.multidict import MultiDict

        pid = u'XXX-XXX-XX'
        # Samole must be from the current working location
        location = factories.LocationFactory.create()
        factories.AliquotFactory.create(
            state__name='pending',
            location=location,
            specimen__patient__pid=pid,
            specimen__location=location,
            specimen__state__name='complete'
        )
        db_session.flush()

        req.GET = MultiDict([('pid', pid)])
        res = self._call_fut(location, req, state='pending')

        assert res['has_aliquot']

    def test_filter_by_pid_not_found(self, req, db_session, factories):
        from webob.multidict import MultiDict

        pid = u'XXX-XXX-XX'
        # Sample must be from the current working location
        location = factories.LocationFactory.create()
        factories.AliquotFactory.create(
            state__name='pending',
            location=location,
            specimen__patient__pid=pid,
            specimen__location=location,
            specimen__state__name='complete'
        )
        db_session.flush()

        req.GET = MultiDict([('pid', u'YYY-YYY-YY')])
        res = self._call_fut(location, req, state='state')

        assert not res['has_aliquot']


class Test_aliquot:

    def _call_fut(self, *args, **kw):
        from occams_lims.views.aliquot import aliquot as view
        return view(*args, **kw)

    def test_default_view(self, req, db_session, factories):
        """
        It should display pending samples by default
        """

        from webob.multidict import MultiDict

        specimen_complete = factories.SpecimenStateFactory.create(
            name='complete'
        )
        location = factories.LocationFactory.create()
        aliquot1 = factories.AliquotFactory.create(
            specimen__location=location,
            specimen__state=specimen_complete,
            location=location,
            state__name='pending',
        )
        factories.AliquotFactory.create(
            specimen__location=location,
            specimen__state=specimen_complete,
            location=location,
            state__name='checked-in')
        db_session.flush()

        req.GET = MultiDict()
        req.POST = MultiDict()
        context = location
        context.request = req
        res = self._call_fut(context, req)

        assert len(res['aliquot']) == 1
        assert res['aliquot'][0] == aliquot1

    def test_validate_template_form(self, req, db_session, factories):
        """
        It should ignore aliquot form when validating the template form
        """
        from webob.multidict import MultiDict

        location = factories.LocationFactory.create()
        specimen_state = factories.SpecimenStateFactory.create(
            name='pending-aliquot'
        )
        aliquot_state = factories.AliquotStateFactory.create(
            name='pending'
        )
        aliquot = factories.AliquotFactory.create(
            specimen__state=specimen_state,
            specimen__location=location,
            state=aliquot_state,
            location=location,
        )
        db_session.flush()

        req.GET = MultiDict()
        req.POST = MultiDict([('template-form', '1')])
        req.method = 'POST'
        context = location
        context.request = req
        res = self._call_fut(context, req)

        assert res['aliquot_form'].data['aliquot'][0]['id'] == aliquot.id

    def test_validate_aliquot_form(self, req, db_session, factories):
        """
        It should ignore template form when validating the aliquot form
        """
        from webob.multidict import MultiDict

        location = factories.LocationFactory.create()
        specimen_state = factories.SpecimenStateFactory.create(
            name='pending-aliquot'
        )
        aliquot_state = factories.AliquotStateFactory.create(
            name='pending'
        )
        aliquot = factories.AliquotFactory.create(
            specimen__state=specimen_state,
            specimen__location=location,
            state=aliquot_state,
            location=location,
        )
        db_session.flush()

        req.GET = MultiDict()
        req.POST = MultiDict([('aliquot-form', '1')])
        req.method = 'POST'
        context = location
        context.request = req
        res = self._call_fut(context, req)

        assert len(res['specimen_form']['specimen'].entries) == 1

    def test_no_required_data(self, req, db_session, factories):
        """
        It should not require input for collect_date and collect_time and
        location_id when data is saved
        """
        import mock
        from webob.multidict import MultiDict

        specimen = factories.SpecimenFactory.create(
            state__name='pending-aliquot',
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
