"""
Testing fixtures

To run the tests you'll then need to run the following command:

    py.test --db postgresql://user:pass@host/db --cov occams_lims tests

"""

import pytest

from sqlalchemy.schema import CreateTable
from sqlalchemy.ext.compiler import compiles


REDIS_URL = 'redis://localhost/9'

USERID = 'test_user'


def pytest_addoption(parser):
    """
    Registers a command line argument for a database URL connection string
    """
    parser.addoption('--db', action='store', help='db string for testing')


@compiles(CreateTable, 'postgresql')
def compile_unlogged(create, compiler, **kwargs):
    """
    Updates the CREATE TABLE construct for PostgreSQL to UNLOGGED

    The benefit of this is faster writes for testing, at the cost of
    slightly slower table creation.

    See: http://www.postgresql.org/docs/9.1/static/sql-createtable.html

    :param create:      the sqlalchemy CREATE construct
    :param compiler:    the current dialect compiler

    :return: the compiled SQL string

    """
    if 'UNLOGGED' not in create.element._prefixes:
        create.element._prefixes.append('UNLOGGED')
        return compiler.visit_create_table(create)


@pytest.yield_fixture(scope='session', autouse=True)
def create_tables(request):
    """
    Creates the database tables for the entire testing session

    :param request: the testing context
    """
    import os
    from sqlalchemy import create_engine
    from occams_datastore import models as datastore
    from occams_studies import Session, models
    from occams_lims import models as lims
    from occams_roster import models as roster, Session as RosterSession

    db = request.config.getoption("--db")

    engine = create_engine(db)
    url = engine.url

    Session.configure(bind=engine)

    datastore.DataStoreModel.metadata.create_all(engine)
    models.Base.metadata.create_all(engine)
    lims.Base.metadata.create_all(engine)

    roster_engine = create_engine('sqlite://')
    RosterSession.configure(bind=roster_engine)
    roster.Base.metadata.create_all(RosterSession.bind)

    yield

    if url.drivername == 'sqlite' and url.database not in ('', ':memory:'):
        os.unlink(url.database)
    else:
        lims.Base.metadata.drop_all(engine)
        models.Base.metadata.drop_all(engine)
        datastore.DataStoreModel.metadata.drop_all(engine)


@pytest.yield_fixture
def config():
    from pyramid import testing
    import transaction
    from occams_forms import models, Session

    testconfig = testing.setUp()

    blame = models.User(key=u'tester')
    Session.add(blame)
    Session.flush()
    Session.info['blame'] = blame

    yield testconfig

    testing.tearDown()
    transaction.abort()
    Session.remove()


@pytest.yield_fixture
def app(request):

    import tempfile
    import six
    import transaction
    from webtest import TestApp
    from zope.sqlalchemy import mark_changed

    from occams import main, Session

    # The pyramid_who plugin requires a who file, so let's create a
    # barebones files for it...
    who_ini = tempfile.NamedTemporaryFile()
    who = six.moves.configparser.ConfigParser()
    who.add_section('general')
    who.set('general', 'request_classifier',
            'repoze.who.classifiers:default_request_classifier')
    who.set('general', 'challenge_decider',
            'repoze.who.classifiers:default_challenge_decider')
    who.set('general', 'remote_user_key', 'REMOTE_USER')
    who.write(who_ini)
    who_ini.flush()

    testapp = TestApp(main({}, **{
        'redis.url': REDIS_URL,
        'redis.sessions.secret': 'sekrit',

        'who.config_file': who_ini.name,
        'who.identifier_id': '',

        # Enable regular error messages so we can see useful traceback
        'debugtoolbar.enabled': True,
        'pyramid.debug_all': True,

        'webassets.debug': False,
        'webassets.auto_build': False,

        'occams.apps': 'occams_lims',

        'occams.db.url': Session.bind,
        'occams.groups': [],

        'roster.db.url': 'sqlite://',
    }))

    yield testapp

    with transaction.manager:
        # DELETE is significantly faster than TRUNCATE
        # http://stackoverflow.com/a/11423886/148781
        # We also have to do this as a raw query becuase SA does
        # not have a way to invoke server-side cascade
        Session.execute('DELETE FROM "location" CASCADE')
        Session.execute('DELETE FROM "site" CASCADE')
        Session.execute('DELETE FROM "study" CASCADE')
        Session.execute('DELETE FROM "specimentype" CASCADE')
        Session.execute('DELETE FROM "user" CASCADE')
        mark_changed(Session())
    Session.remove()
    who_ini.close()


def make_environ(userid=USERID, properties={}, groups=()):
    """
    Creates dummy environ variables for mock-authentication

    :param userid:      The currently authenticated userid
    :param properties:  Additional identity properties
    :param groups:      Optional group memberships
    """
    if userid:
        return {
            'REMOTE_USER': userid,
            'repoze.who.identity': {
                'repoze.who.userid': userid,
                'properties': properties,
                'groups': groups}}


def get_csrf_token(app, environ=None):
    """
    Request the app so csrf cookie is available

    :param app:     The testing application
    :param environ: The environ variables (if the user is logged in)
                    Default: None
    """
    app.get('/', extra_environ=environ)

    return app.cookies['csrf_token']
