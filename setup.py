from setuptools import setup, find_packages
import sys
import os

version = '0.1.18'

requirements = [
    'requests',
    'click'
]


setup(name='periodo_reconciler',
      version=version,
      description="""\
      Python wrapper around Open Refine reconciliation service
      for PeriodO data""",
      long_description="""\
Open Refine reconciliation service for PeriodO data""",
      classifiers=[],
      keywords='utilities',
      author='Raymond Yee',
      author_email='raymond.yee@gmail.com',
      url='https://github.com/rdhyee/periodo-reconciler-py',
      license='Apache 2.0',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requirements,
      extras_require={
          'dev': [
              'pytest',
              'pytest-pep8',
              'pytest-cov',
              'jinja2',
              'pycodestyle',
              'jupyter',
              'pandas'
          ]
      },
      scripts=['bin/periodo-reconciler-py'],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
