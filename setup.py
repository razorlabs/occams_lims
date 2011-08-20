from setuptools import setup, find_packages
import os

version = '0.4.3'

setup(name='hive.lab',
      version=version,
      description="Lab Inventory management",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'':'src'},
      namespace_packages=['hive'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'collective.autopermission', # Schema permissions
        'plone.dexterity', # Dexterity FTI
        'plone.behavior',
        'plone.app.registry', # For registering the behaviors
        'reportlab', # PDF label generator
        'xlutils', # Excel Export
        'z3c.form >= 2.4.1', # For attributes to work correctly
        'sqlalchemy',
        'sqlalchemy-migrate',
        'avrc.aeh',
        'avrc.data.store', # EAV Back-end
        'avrc.data.registry', # OUR number generator
        'beast.browser', # Tools for browser displays
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      setup_requires=["PasteScript"],
      paster_plugins=["ZopeSkel"],
      )
