from pathlib import Path

import toml

package_root = Path(__file__).parent.parent.absolute()
poetry_config = toml.load(str(package_root / 'pyproject.toml'))

full_version = poetry_config['tool']['poetry']['version']

version_parts = full_version.split('.')

version_1 = '.'.join(version_parts[:1])
version_1_2 = '.'.join(version_parts[:2])
