from pathlib import Path

import toml

package_root = Path(__file__).parent.parent.absolute()
pyproject_data = toml.load(str(package_root / 'pyproject.toml'))

full_version = pyproject_data['project']['version']

version_parts = full_version.split('.')

version_1 = '.'.join(version_parts[:1])
version_1_2 = '.'.join(version_parts[:2])
