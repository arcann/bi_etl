import toml

from bi_etl.utility.package_root import get_package_root_path

package_root = get_package_root_path()
poetry_config = toml.load(package_root.joinpath('pyproject.toml'))

full_version = poetry_config['tool']['poetry']['version']

version_parts = full_version.split('.')

version_1 = '.'.join(version_parts[:1])
version_1_2 = '.'.join(version_parts[:2])
