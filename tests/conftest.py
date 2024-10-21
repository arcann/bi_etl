import os
from pathlib import Path

import pytest
from dotenv.main import DotEnv


def import_env():
    test_path = Path(__file__).parent.absolute()
    config_env_path = test_path / 'config.env'
    if config_env_path.exists():
        print(f"Loading environment variables from {config_env_path}")
        dotenv = DotEnv(config_env_path)
        dotenv.set_as_environment_variables()
        for k, v in dotenv.dict().items():
            setting_now = os.environ[k]
            print(f"  {k}: read= {v} setting= {setting_now}")
        print('--end of env--')
    else:
        print(f"environment variable file {config_env_path} not found")


@pytest.fixture(scope="session", autouse=True)
def execute_before_any_test():
    print("execute_before_any_test")

    import_env()


def pytest_cmdline_main(config):
    print("pytest_cmdline_main")

    import_env()

    # Fix for pycharm error that tries to run tests out of db_base_tests
    # 1st pass find DB
    db = None
    for arg in config.args:
        if 'Oracle' in arg:
            db = 'oracle'
        elif 'Postgres' in arg:
            db = 'postgres'
        elif 'Redshift' in arg:
            db = 'redshift'
        elif 'Sqlite' in arg:
            db = 'sqlite'

    # Then change the references to the base_test to be the db specific module
    new_args = list()
    changed = False
    for arg in config.args:
        if 'base_test_' in arg:
            arg = arg.replace('base_test_', 'test_').replace('.py', f"_{db}.py")
            changed = True
        new_args.append(arg)

    if changed:
        print(f"Remapped test {config.args} to {new_args}")
    config.args = new_args

    # Also change the path to be the DB specific one
    if changed:
        in_dir_str = str(config.invocation_params.dir)
        if 'db_base_tests' in in_dir_str:
            new_path = Path(in_dir_str.replace('db_base_tests', f"db_{db}"))
            print(f"Changed test dir from {in_dir_str} to {new_path}")
            # os.chdir(new_path)
            config.invocation_params = config.InvocationParams(
                args=config.invocation_params.args,
                plugins=config.invocation_params.plugins,
                dir=new_path,
            )
