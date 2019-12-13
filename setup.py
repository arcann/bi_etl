import os

from setuptools import setup, find_packages

import bi_etl.version

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

install_requires = [
    'SQLAlchemy',
    'semidbm',
    'sortedcontainers',
    'psutil >= 5.2.2',
    'openpyxl',
    'psutil',
    'pyodbc',
    'CaseInsensitiveDict',
    'pyramid',
    # For Docs build
    'sphinx',
    'sphinx-autodoc-annotation',
    'btrees',
    'gevent',
    ]

extras_require = {
        'mem_debug': ['pympler'],
        'password_mgt': ['keyring'],
    }

tests_require = [
    'pytest',
    'coverage',
    'pytest-cov',
]

setup(name='bi_etl',
      version=bi_etl.version.full_version,
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
