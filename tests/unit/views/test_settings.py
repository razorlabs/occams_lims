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

        type_ = db_session.query(models.SpecimenType).one()

        assert type_.title == u'test_title'
        assert type_.description == u'test_description'
        assert type_.tube_type == u''
        assert type_.default_tubes == 2

    def test_add_specimen_type_duplicate_error(self, req, db_session,
                                               factories):
        """
        It should include a flash message of indicating Form Errors
        and the error type in the form
        """
        import mock
        from slugify import slugify
        from webob.multidict import MultiDict

        title = 'Pre Existing Type'

        factories.SpecimenTypeFactory.create(
            name=slugify(title), title=title)
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        # Attemp to create a new type with the same title
        req.POST = MultiDict([
            ('title', title),
            ('specimen-type-add-form', '1'),
        ])

        context = mock.Mock()
        context.request = req
        res = self._call_fut(context, req)

        assert u'Form errors' in req.session.pop_flash('danger')[0]
        assert u'similar name' in \
            res['specimen_type_add_form']['title'].errors[0]

    def test_crud_specimen_type(self, req, db_session, factories):
        """
        It should let the user edit types in the CRUD form
        """
        import mock
        from webob.multidict import MultiDict
        from occams_lims import models

        factories.SpecimenTypeFactory.create()
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        # Attemp to create a new type with the same title
        req.POST = MultiDict([
            ('types-0-title', 'New title'),
            ('specimen-type-crud-form', '1'),
            ('save', '1'),
        ])

        context = mock.Mock()
        context.request = req
        self._call_fut(context, req)

        type_ = db_session.query(models.SpecimenType).one()

        assert type_.title == 'New title'

    def test_crud_validate_specimen_type(self, req, db_session, factories):
        """
        It should validate the form to avoid duplicates
        """
        import mock
        from webob.multidict import MultiDict

        factories.SpecimenTypeFactory.create(name='type-0', title='Type 0')
        factories.SpecimenTypeFactory.create(name='type-1', title='Type 1')

        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        # Attemp to set the first entry the same as the second
        req.POST = MultiDict([
            ('types-0-title', 'Type 1'),
            ('specimen-type-crud-form', '1'),
            ('save', '1'),
        ])

        context = mock.Mock()
        context.request = req
        res = self._call_fut(context, req)

        assert u'Form errors' in req.session.pop_flash('danger')[0]
        assert u'similar name' in \
            res['specimen_type_crud_form'].types.entries[0].title.errors[0]

    def test_crud_delete_specimen_type(self, req, db_session, factories):
        """
        It should allow the deletion of unused types
        """
        import mock
        from webob.multidict import MultiDict
        from occams_lims import models

        type_ = factories.SpecimenTypeFactory.create()
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        # Attemp to create a new type with the same title
        req.POST = MultiDict([
            ('types-0-ui_selected', 'true'),
            ('types-0-id', str(type_.id)),
            ('specimen-type-crud-form', '1'),
            ('delete', '1'),
        ])

        context = mock.Mock()
        context.request = req
        self._call_fut(context, req)

        count = db_session.query(models.SpecimenType).count()

        assert count == 0

    def test_crud_fail_delete_used_specimen_type(
            self, req, db_session, factories):
        """
        It should fail to delete a specimen type that is in use
        """
        import mock
        from webob.multidict import MultiDict

        specimen = factories.SpecimenFactory.create()
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        # Attemp to create a new type with the same title
        req.POST = MultiDict([
            ('types-0-ui_selected', 'true'),
            ('types-0-id', str(specimen.specimen_type.id)),
            ('specimen-type-crud-form', '1'),
            ('delete', '1'),
        ])

        context = mock.Mock()
        context.request = req
        self._call_fut(context, req)

        assert u'already have specimen collected' \
            in req.session.pop_flash('danger')[0]

    def test_add_aliquot_type(self, req, db_session, factories):
        """
        It should add a aliquot type to the database
        """
        import mock
        from webob.multidict import MultiDict
        from occams_lims import models

        specimen_type = factories.SpecimenTypeFactory.create()
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('title', 'test_title'),
            ('description', 'test_description'),
            ('specimen_type_id', str(specimen_type.id)),
            ('units', 'ea'),
            ('aliquot-type-add-form', '1')
        ])

        context = mock.Mock()
        context.request = req
        self._call_fut(context, req)

        type_ = db_session.query(models.AliquotType).one()

        assert type_.title == u'test_title'
        assert type_.description == u'test_description'
        assert type_.units == 'ea'

    def test_add_aliquot_type_duplicate_error(
            self, req, db_session, factories):
        """
        It should include a flash message of indicating Form Errors
        and the error type in the form
        """
        import mock
        from slugify import slugify
        from webob.multidict import MultiDict

        specimen_type = factories.SpecimenTypeFactory.create()

        title = 'Pre Existing Type'

        factories.AliquotTypeFactory.create(name=slugify(title), title=title)
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        # Attemp to create a new type with the same title
        req.POST = MultiDict([
            ('title', title),
            ('specimen_type_id', str(specimen_type.id)),
            ('units', u'ea'),
            ('aliquot-type-add-form', '1'),
        ])

        context = mock.Mock()
        context.request = req
        res = self._call_fut(context, req)

        assert u'Form errors' in req.session.pop_flash('danger')[0]
        assert u'similar name' in \
            res['aliquot_type_add_form']['title'].errors[0]

    def test_crud_aliquot_type(self, req, db_session, factories):
        """
        It should let the user edit types in the CRUD form
        """
        import mock
        from webob.multidict import MultiDict
        from occams_lims import models

        specimen_type = factories.SpecimenTypeFactory.create()

        type_ = factories.AliquotTypeFactory.create()
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        # Attemp to create a new type with the same title
        req.POST = MultiDict([
            ('types-0-title', 'New title'),
            ('types-0-specimen_type_id', str(specimen_type.id)),
            ('types-0-units', 'ea'),
            ('aliquot-type-crud-form', '1'),
            ('save', '1'),
        ])

        context = mock.Mock()
        context.request = req
        self._call_fut(context, req)

        type_ = db_session.query(models.AliquotType).one()

        assert type_.title == 'New title'

    def test_crud_validate_aliquot_type(self, req, db_session, factories):
        """
        It should validate the form to avoid duplicates
        """
        import mock
        from webob.multidict import MultiDict

        factories.AliquotTypeFactory.create(name='type-0', title='Type 0')
        factories.AliquotTypeFactory.create(name='type-1', title='Type 1')

        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        # Attemp to set the first entry the same as the second
        req.POST = MultiDict([
            ('types-0-title', 'Type 1'),
            ('aliquot-type-crud-form', '1'),
            ('save', '1'),
        ])

        context = mock.Mock()
        context.request = req
        res = self._call_fut(context, req)

        assert u'Form errors' in req.session.pop_flash('danger')[0]
        assert u'similar name' in \
            res['aliquot_type_crud_form'].types.entries[0].title.errors[0]

    def test_crud_delete_aliquot_type(self, req, db_session, factories):
        """
        It should allow the deletion of unused types
        """
        import mock
        from webob.multidict import MultiDict
        from occams_lims import models

        type_ = factories.AliquotTypeFactory.create()
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        # Attemp to create a new type with the same title
        req.POST = MultiDict([
            ('types-0-ui_selected', 'true'),
            ('types-0-id', str(type_.id)),
            ('aliquot-type-crud-form', '1'),
            ('delete', '1'),
        ])

        context = mock.Mock()
        context.request = req
        self._call_fut(context, req)

        count = db_session.query(models.AliquotType).count()

        assert count == 0

    def test_crud_fail_delete_used_aliquot_type(
            self, req, db_session, factories):
        """
        It should fail to delete an aliquot type that is in use
        """
        import mock
        from webob.multidict import MultiDict

        aliquot = factories.AliquotFactory.create()
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        # Attemp to create a new type with the same title
        req.POST = MultiDict([
            ('types-0-ui_selected', 'true'),
            ('types-0-id', str(aliquot.aliquot_type.id)),
            ('aliquot-type-crud-form', '1'),
            ('delete', '1'),
        ])

        context = mock.Mock()
        context.request = req
        self._call_fut(context, req)

        assert u'already have aliquot collected' \
            in req.session.pop_flash('danger')[0]

    def test_add_lab(self, req, db_session, factories):
        """
        It should add a lab
        """
        import mock
        from webob.multidict import MultiDict

        from occams_lims import models

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('name', 'test_name'),
            ('title', 'test_title'),
            ('is_enabled', 'checked'),
            ('active', 'checked'),
            ('lab-add-form', '')
        ])

        context = mock.Mock()
        context.request = req

        self._call_fut(context, req)

        location = (
            db_session.query(models.Location.id)
            .filter_by(title='test_title')
            .scalar())

        assert location is not None

    def test_add_lab_w_errors(self, req, db_session, factories):
        """
        It should not add a lab and show errors notification message
        """
        import mock
        from webob.multidict import MultiDict

        from occams_lims import models

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('title', 'test_title'),
            ('lab-add-form', '')
        ])

        context = mock.Mock()
        context.request = req

        self._call_fut(context, req)

        location = (
            db_session.query(models.Location.id)
            .filter_by(title='test_title')
            .scalar())

        # This should fail because not all required form data was posted
        assert 'Form errors' in req.session.pop_flash('danger')[0]
        assert location is None

    def test_delete_lab(self, req, db_session, factories):
        """
        It should delete a lab
        """
        import mock
        from webob.multidict import MultiDict

        from occams_lims import models

        lab = factories.LocationFactory.create(
            name=u'test_name',
            title=u'test_title'
        )
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('types-0-ui_selected', 'true'),
            ('lab-type-crud-form', ''),
            ('delete', '1')
        ])

        context = mock.Mock()
        context.request = req

        self._call_fut(context, req)

        location_exists = (
            db_session.query(models.Location.id)
            .filter_by(id=lab.id)
            .scalar())

        assert location_exists is None

    def test_delete_lab_none_selected(self, req, db_session, factories):
        """
        It should provide a message indicating no labs selected
        """
        import mock
        from webob.multidict import MultiDict

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('lab-type-crud-form', ''),
            ('delete', '1')
        ])

        context = mock.Mock()
        context.request = req

        self._call_fut(context, req)

        assert 'No labs selected' in req.session.pop_flash('warning')[0]

    def test_edit_lab(self, req, db_session, factories):
        """
        It should update the edited data
        """
        import mock
        from webob.multidict import MultiDict

        from occams_lims import models

        lab = factories.LocationFactory.create(
            name=u'test_name',
            title=u'test_title'
        )
        db_session.flush()

        req.current_route_path = mock.Mock()
        req.method = 'POST'
        req.GET = MultiDict()
        req.POST = MultiDict([
            ('types-0-id', str(lab.id)),
            ('types-0-name', 'test_name'),
            ('types-0-title', 'test_new_title'),
            ('types-0-is_enabled', 'checked'),
            ('types-0-active', 'checked'),
            ('lab-type-crud-form', ''),
            ('save', '1')
        ])

        context = mock.Mock()
        context.request = req

        self._call_fut(context, req)

        location = (
            db_session.query(models.Location.id)
            .filter_by(title='test_new_title')
            .scalar())

        assert location is not None
