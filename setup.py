import os
import re
from subprocess import Popen, PIPE
from setuptools import setup, find_packages
from setuptools.command.develop import develop as _develop
import sys


def yield_packages(path):
    """Simple parser for requirements.txt files"""
    with open(path) as requirements:
        for line in requirements:
            if re.match('^[a-zA-Z]', line):
                yield line.strip()


HERE = os.path.abspath(os.path.dirname(__file__))
REQUIRES = list(yield_packages(os.path.join(HERE, 'requirements.txt')))
DEVELOP = list(yield_packages(os.path.join(HERE, 'requirements-develop.txt')))


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
    author='The YoungLabs',
    author_email='younglabs@ucsd.edu',
    url='https://github.com/younglabs/occams_lims',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    extras_require={'develop': DEVELOP, 'test': DEVELOP},
    tests_require=DEVELOP,
    cmdclass={'develop': _custom_develop},
    entry_points="""\
    [console_scripts]
    """,
)
