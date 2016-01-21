import pytest


@pytest.yield_fixture
def check_csrf_token():
    import mock
    name = 'occams_lims.views.aliquot.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class TestSettings:

    def _call_fut(self, *args, **kw):
        from occams_lims.views.settings import settings as view
        return view(*args, **kw)

    def test_add_specimen_type(self, req, db_session, factories):
        """
        It should add a add_specimen_type to the database
        """
        import mock
        from webob.multidict import MultiDict
        from occams_lims import models

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('title', 'test_title'),
            ('description', 'test_description'),
            ('tube_type', ''),
            ('default_tubes', '2'),
            ('specimen-type-add-form', '1')
        ])

        context = mock.Mock()
        context.request = req
        self._call_fut(context, req)

        specimen = db_session.query(models.SpecimenType).one()

        assert specimen.title == u'test_title'
        assert specimen.description == u'test_description'
        assert specimen.tube_type == u''
        assert specimen.default_tubes == 2

    def test_add_specimen_type_duplicate_error(self, req, db_session,
                                               factories):
        """
        It should include a flash message of indicating Form Errors
        and the error type in the form
        """
        import mock
        from webob.multidict import MultiDict

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('title', 'test_title'),
            ('description', 'test_description'),
            ('tube_type', ''),
            ('default_tubes', '2'),
            ('specimen-type-add-form', '1')
        ])

        context = mock.Mock()
        context.request = req
        self._call_fut(context, req)
        # call view 2nd time with same post data...this is the duplicate
        duplicate = self._call_fut(context, req)

        assert u'Form errors' in req.session['_f_danger'][0]
        assert u'similar name' in duplicate['specimen_type_add_form']['title'].error

