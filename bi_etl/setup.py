"""
Created on Mar 26, 2015

@author: woodd
"""
import os
import sys
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

install_requires = [
    'SQLAlchemy',    
    'semidbm',
    'sortedcontainers',
    'psutil >= 2.0.0',
    'openpyxl',
    'psutil',
    'sortedcontainers',
    'CaseInsensitiveDict',
    'pytest',
    ]

if sys.version_info[0] < 3:
    install_requires.append('faulthandler')
    install_requires.append('enum34')

extras_require = {
        'mem_debug':  ['pympler'],
    }

setup(name='bi_etl',
      # TODO: Increment this version
      version='0.7',
      description='ETL (Extract Transform Load) framework geared towards BI database in particular.',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries",
        ],
      author='Derek Wood',
      author_email='',
      url='',
      keywords='etl bi database',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      extras_require=extras_require,
      tests_require=['pytest',
                     'mock',
                     'coverage',
                     ],
      )
