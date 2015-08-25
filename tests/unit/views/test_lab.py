
class Test_inbox:

    def test_24_hour_collect_time(self, config):

        from pyramid import testing
        from occams_lims import Session, models
        from occams_lims.views.lab import inbox as view

        location = models.Location(
            name=u'some_location',
            title=u'Some Location'
        )

        Session.add(location)
        Session.flush()

        request = testing.DummyRequest()

        response = view(location, request)

        assert False
