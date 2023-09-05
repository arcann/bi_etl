from pathlib import Path


def pytest_cmdline_main(config):
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
