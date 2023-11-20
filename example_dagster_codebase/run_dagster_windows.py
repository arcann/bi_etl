import os
import subprocess
from typing import List


def run_dagster(args: List[str]):
    # subprocess.run("poetry install -E dagster", shell=True, check=True)

    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'
    os.environ['DAGSTER_HOME'] = str('/dagster_home')
    warnings_ignore_list = [
        'ignore:Classes should inherit from `BaseModel`',
        'ignore:Class `AutoMaterializePolicy`',
        'ignore:Class `FreshnessPolicy`',
        'ignore:Parameter `auto_materialize_policy`',
    ]
    os.environ['PYTHONWARNINGS'] = ','.join(warnings_ignore_list)

    # noinspection PyProtectedMember
    from dagster._cli import dev_command

    dev_command(args=args)


if __name__ == '__main__':
    run_dagster(
        [
            '-f', 'assets/simple_assets.py',
            '-f', 'assets/partitioned_assets.py',
        ]
    )
