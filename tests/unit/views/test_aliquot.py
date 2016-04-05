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

    @pytest.mark.parametrize('state', [
        'pending',
        'checked-in',
        'checkout-out',
        'hold',
        'prepared',
        'incorrect',
        'pending-checkout',
        'queued',
        'missing',
        'destroyed'])
    def test_print_by_aliquot_all_states(
            self, req, db_session, config, factories, check_csrf_token, state):
        from webob.multidict import MultiDict
        from occams_lims.views.aliquot import ALIQUOT_LABEL_QUEUE

        location = factories.LocationFactory.create()
        specimen_state = factories.SpecimenStateFactory.create(
            name='complete'
        )
        aliquot_state = factories.AliquotStateFactory.create(
            name=state
        )
        aliquot = factories.AliquotFactory.create(
            specimen__state=specimen_state,
            specimen__location=location,
            state=aliquot_state,
            location=location,
        )
        db_session.flush()

        context = aliquot.location
        req.session[ALIQUOT_LABEL_QUEUE] = set([aliquot.id])
        req.method = 'POST'
        req.POST = MultiDict([('print', '')])
        res = self._call_fut(context, req)

        assert res.content_type == 'application/pdf'
        assert len(req.session[ALIQUOT_LABEL_QUEUE]) == 0

    @pytest.mark.parametrize('state', [
        'pending-draw',
        'cancel-draw',
        'pending-aliquot',
        'aliquoted',
        'rejected',
        'prepared-aliquot',
        'complete',
        'batched',
        'postponed'])
    def test_print_by_specimen_all_states(
            self, req, db_session, config, factories, check_csrf_token, state):
        from webob.multidict import MultiDict
        from occams_lims.views.aliquot import ALIQUOT_LABEL_QUEUE

        location = factories.LocationFactory.create()
        specimen_state = factories.SpecimenStateFactory.create(
            name=state
        )
        specimen = factories.SpecimenFactory.create(
            state=specimen_state,
            location=location
        )
        db_session.flush()

        context = specimen.location
        req.session[ALIQUOT_LABEL_QUEUE] = set([specimen.id])
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

    def test_collect_and_store_date(self, db_session, factories):
        import datetime
        aliquot = factories.AliquotFactory.create()
        factories.EnrollmentFactory.create(
            patient=aliquot.specimen.patient,
            study=aliquot.specimen.cycle.study,
            consent_date=aliquot.specimen.collect_date)
        db_session.flush()

        res = self._call_fut(aliquot)
        # these are label rows
        dates = res[1][2]

        assert dates[0:2] == u'C:'
        assert dates[14:16] == u'S:'

        collect_date = datetime.datetime.strptime(dates[3:13], '%m/%d/%Y')
        assert isinstance(collect_date, datetime.datetime) is True

        store_date = datetime.datetime.strptime(dates[17:27], '%m/%d/%Y')
        assert isinstance(store_date, datetime.datetime) is True

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
        """
        It should return aliquot matching the cycle filter criteria
        """
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
        """
        It should not return aliquot because filter criteria does not match
        any specimen
        """
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

    def test_filter_by_cycle_found(self, req, db_session, factories):
        """
        It should return aliquot matching the cycle filter criteria
        """
        from webob.multidict import MultiDict

        location = factories.LocationFactory.create()
        cycle = factories.CycleFactory.create(
            title=u'Week 52')
        specimen = factories.SpecimenFactory.create(
            cycle=cycle)
        factories.AliquotFactory.create(
            state__name='pending',
            location=location,
            specimen=specimen)
        db_session.flush()

        req.GET = MultiDict([(u'visit_cycles', cycle.id)])
        res = self._call_fut(location, req, state='pending')

        assert res['has_aliquot']

    def test_filter_by_cycle_not_found(self, req, db_session, factories):
        """
        It should not return aliquot because filter criteria does not match
        any specimen
        """
        from webob.multidict import MultiDict

        location = factories.LocationFactory.create()
        cycle = factories.CycleFactory.create(
            title=u'Week 52')
        cycle2 = factories.CycleFactory.create(
            title=u'Week 53')
        specimen = factories.SpecimenFactory.create(
            cycle=cycle,
            location=location)
        factories.AliquotFactory.create(
            state__name='pending',
            location=location,
            specimen=specimen)
        db_session.flush()

        req.GET = MultiDict([(u'visit_cycles', cycle2.id)])

        res = self._call_fut(location, req, state='pending')

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
        factories.AliquotFactory.create(
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

    def test_no_required_data_aliquot_create(self, req, db_session, factories):
        """
        It should not require input for amount, and store_date when
        aliquot is created
        """
        import mock
        from webob.multidict import MultiDict
        from occams_lims import models

        factories.AliquotStateFactory.create(name='pending')
        aliquot_type = factories.AliquotTypeFactory.create()
        specimen_type = aliquot_type.specimen_type
        specimen_pending = factories.SpecimenStateFactory.create(
            name='pending-aliquot'
        )
        specimen = factories.SpecimenFactory.create(
            state=specimen_pending,
            specimen_type=specimen_type
        )
        db_session.flush()

        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('specimen-0-ui_selected', '1'),
            ('specimen-0-count', '2'),
            ('specimen-0-aliquot_type_id', str(aliquot_type.id)),
            ('specimen-0-amount', ''),
            ('specimen-0-store_date', ''),
            ('template-form', '1'),
            ('create', '1')
        ])

        context = specimen.location
        context.request = req
        res = self._call_fut(context, req)

        aliquot_query = (
            db_session.query(models.Aliquot)
            .filter_by(specimen=specimen))

        assert aliquot_query.count() == 2
        assert res.status_code == 302, 'Should be status code 302'

    def test_no_required_data_aliquot_save(self, req, db_session, factories):
        """
        It should not require input for amount, and store_date when
        aliquot is saved (works in progress)
        """
        import mock
        from webob.multidict import MultiDict

        location = factories.LocationFactory.create()
        specimen_state = factories.SpecimenStateFactory.create(
            name='complete'
        )
        aliquot_pending = factories.AliquotStateFactory.create(name='pending')
        factories.AliquotStateFactory.create(name='checked-in')

        aliquot = factories.AliquotFactory.create(
            specimen__location=location,
            specimen__state=specimen_state,
            state=aliquot_pending,
            location=location,
        )
        db_session.flush()

        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('aliquot-0-ui_selected', ''),
            ('aliquot-0-amount', ''),
            ('aliquot-0-store_date', ''),
            ('aliquot-form', '1'),
            ('save', '1'),
        ])

        context = aliquot.location
        context.request = req
        res = self._call_fut(context, req)

        assert aliquot.store_date is None
        assert aliquot.amount is None
        assert res.status_code == 302, 'Should be status code 302'

    @pytest.mark.parametrize('button', ['queue', 'checkin', 'checkout'])
    def test_required_data_aliquot_on_button(
            self, req, db_session, factories, button):
        """
        It should not require input for amount, and store_date when
        aliquot is checked-in
        """
        import mock
        from webob.multidict import MultiDict

        location = factories.LocationFactory.create()
        specimen_state = factories.SpecimenStateFactory.create(
            name='complete'
        )
        aliquot_pending = factories.AliquotStateFactory.create(name='pending')
        factories.AliquotStateFactory.create(name='checked-in')

        factories.SpecimenFactory.create()

        aliquot = factories.AliquotFactory.create(
            specimen__state=specimen_state,
            state=aliquot_pending,
            location=location,
        )
        db_session.flush()

        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('aliquot-0-id', str(aliquot.id)),
            ('aliquot-0-ui_selected', 'true'),
            ('aliquot-0-aliquot_type_id', '56'),
            ('aliquot-0-amount', ''),
            ('aliquot-0-store_date', ''),
            ('aliquot-form', '1'),
            (button, '1'),
        ])

        context = aliquot.location
        context.request = req
        res = self._call_fut(context, req)

        assert 'required' in \
            res['aliquot_form'].errors['aliquot'][0]['store_date'][0]
        assert 'required' in \
            res['aliquot_form'].errors['aliquot'][0]['amount'][0]

    def test_view_and_process_permissions(self, req, config,
                                          db_session, factories):
        """
        It should raise a 403 if the user does not have process permissions
        """
        import mock
        from webob.multidict import MultiDict
        from pyramid.httpexceptions import HTTPForbidden

        location = factories.LocationFactory.create()
        specimen_state = factories.SpecimenStateFactory.create(
            name='complete'
        )
        aliquot_pending = factories.AliquotStateFactory.create(name='pending')
        factories.AliquotStateFactory.create(name='checked-in')

        aliquot = factories.AliquotFactory.create(
            specimen__location=location,
            specimen__state=specimen_state,
            state=aliquot_pending,
            location=location,
        )
        db_session.flush()

        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([])

        context = aliquot.location
        context.request = req

        # Should not be able to POST without 'process' permission
        config.testing_securitypolicy(permissive=False)
        with pytest.raises(HTTPForbidden):
            self._call_fut(context, req)

    def test_delete_aliquot(self, req, config, db_session, factories):
        """
        It should delete flagged aliquot from the system
        """
        import mock
        from webob.multidict import MultiDict

        from occams_lims import models

        location = factories.LocationFactory.create()
        specimen = factories.SpecimenFactory.create()
        aliquot_pending = factories.AliquotStateFactory.create(name='pending')

        aliquot = factories.AliquotFactory.create(
            specimen=specimen,
            state=aliquot_pending,
            location=location
        )
        db_session.flush()

        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('aliquot-0-id', str(aliquot.id)),
            ('aliquot-0-ui_selected', 'true'),
            ('aliquot-0-aliquot_type_id', aliquot.specimen.specimen_type_id),
            ('aliquot-0-amount', aliquot.amount),
            ('aliquot-0-store_date', aliquot.store_date.strftime('%Y-%m-%d')),
            ('aliquot-form', '1'),
            ('delete', '1'),
        ])

        context = aliquot.location
        context.request = req

        self._call_fut(context, req)

        aliquot_exists = (
            db_session.query(models.Aliquot.id)
            .filter_by(id=aliquot.id)
            .scalar())

        assert aliquot_exists is None
