import os
from subprocess import Popen, PIPE
from setuptools import setup, find_packages
from setuptools.command.develop import develop as _develop
import sys

HERE = os.path.abspath(os.path.dirname(__file__))

REQUIRES = [
    'alembic',                          # Database table upgrades
    'humanize',                         # human readable measurements
    'reportlab',
    'six',                              # Py 2 & 3 compatibilty

    'occams',
    'occams_studies'
]

EXTRAS = {
    'test': [
        'nose',
        'nose-testconfig',
        'coverage',
        'WebTest',
        'beautifulsoup4',
        'mock',
        'ddt'],
}


def get_version():
    version_file = os.path.join(HERE, 'VERSION')

    # read fallback file
    try:
        with open(version_file, 'r+') as fp:
            version_txt = fp.read().strip()
    except:
        version_txt = None

    # read git version (if available)
    try:
        version_git = (
            Popen(['git', 'describe'], stdout=PIPE, stderr=PIPE, cwd=HERE)
            .communicate()[0]
            .strip()
            .decode(sys.getdefaultencoding()))
    except:
        version_git = None

    version = version_git or version_txt or '0.0.0'

    # update fallback file if necessary
    if version != version_txt:
        with open(version_file, 'w') as fp:
            fp.write(version)

    return version


class _custom_develop(_develop):
    def run(self):
        _develop.run(self)
        self.execute(_post_develop, [], msg="Running post-develop task")


def _post_develop():
    from subprocess import call
    call(['bower', 'install'], cwd=HERE)

setup(
    name='occams_lims',
    version=get_version(),
    description="Lab Inventory management",
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    keywords='',
    author='BEAST Core Development Team',
    author_email='bitcore@ucsd.edu',
    url='https://bitbucket.org/ucsdbitcore/occams_lims',
    license='GPL',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    extras_require=EXTRAS,
    tests_require=EXTRAS['test'],
    test_suite='nose.collector',
    cmdclass={'develop': _custom_develop},
)
