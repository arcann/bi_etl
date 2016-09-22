"""
Created on Mar 26, 2015

@author: woodd
"""
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

install_requires = [
    'SQLAlchemy',
    'semidbm',
    'sortedcontainers',
    'psutil >= 2.0.0',
    'openpyxl',
    'psutil',
    'pyodbc',
    'CaseInsensitiveDict',
    'pyramid',
    ]

extras_require = {
        'mem_debug': ['pympler'],
        'password_mgt': ['keyring'],
    }

tests_require = [
    'nose',
    'coverage',
]

setup(name='bi_etl',
      version='0.3',
      description='ETL (Extract Transform Load) framework geared towards BI database in particular.',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries",
        ],
      author='Derek Wood',
      author_email='9jym-buur@spamex.com',
      url='',
      keywords='etl bi database',
      packages=find_packages(),
      install_requires=install_requires,
      extras_require=extras_require,
      tests_require=tests_require,
      )
