from setuptools import setup, find_packages
import sys, os

version = '0.0.1'

setup(name='periodo_reconciler',
      version=version,
      description="Python wrapper around Open Refine reconciliation service for PeriodO data",
      long_description="""\
Open Refine reconciliation service for PeriodO data""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='utilities',
      author='Raymond Yee',
      author_email='raymond.yee@gmail.com',
      url='https://github.com/rdhyee/periodo-reconciler-py',
      license='Apache 2.0',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )