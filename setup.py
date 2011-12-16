from setuptools import setup, find_packages
import os

version = '0.4.5'

setup(
    name='hive.lab',
    version=version,
    description="Lab Inventory management",
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
    keywords='',
    author='BEAST Core Development Team',
    author_email='beast@ucsd.edu',
    url='https://github.com/beastcore/hive.lab',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['hive'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'collective.autopermission', # Schema permissions
        'collective.beaker', # for session support
        'plone.app.dexterity [grok]', # Dexterity FTI
        'plone.behavior',
        'plone.app.registry', # For registering the behaviors
        'reportlab', # PDF label generator
        'xlutils', # Excel Export
        'z3c.form >= 2.4.1', # For attributes to work correctly

        'avrc.aeh',
        'avrc.data.store', # EAV Back-end
        'beast.browser', # Tools for browser displays
        ],
    extras_require=dict(
        test=['plone.app.testing'],
        ),
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
    )
