import os
import toml
from bi_etl.bi_config_parser import BIConfigParser

package_root = BIConfigParser.get_package_root()
poetry_config = toml.load(os.path.join(package_root, 'pyproject.toml'))

full_version = poetry_config['tool']['poetry']['version']

version_parts = full_version.split('.')

version_1 = '.'.join(version_parts[:1])
version_1_2 = '.'.join(version_parts[:2])
