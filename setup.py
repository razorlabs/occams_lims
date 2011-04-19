from setuptools import setup, find_packages
import os

version = '0.1'

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
        'collective.autopermission',        # Schema permissions
        'plone.app.dexterity',              # Plone 4 FTI libraries
        'plone.app.intid',
        'plone.app.portlets',
        'plone.namedfile[blobs]',
        'plone.principalsource',
        'z3c.schema',
        'z3c.saconfig',                     # Database connectivity
        'reportlab',                        # PDF label generator
        'avrc.data.store',                  # EAV Back-end
        'avrc.data.registry',               # OUR number generator
        'xlutils',                          # Excel Export          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      setup_requires=["PasteScript"],
      paster_plugins=["ZopeSkel"],
      )
