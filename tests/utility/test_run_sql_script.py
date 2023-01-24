import os
import unittest
from pathlib import Path

from config_for_tests import build_config
from bi_etl.utility.run_sql_script import RunSQLScript


class TestRunSQLScript(unittest.TestCase):

    def setUp(self):
        self.config = build_config()

    def test_init_various_cwd(self):
        package_path = Path(__file__).parents[2]
        save_cwd = Path.cwd()
        
        expected_hash = '287c93bd3035ce1c7755432d5ed2a5c4f203c218'
        expected_name = 'run_sql_script.tests.sql.test1.sql'

        try:
            for cwd in [
                package_path,
                package_path / 'tests',
                package_path / 'tests' / 'etl_jobs',
                # Path outside the script path ancestry
                package_path / 'docs',
            ]:
                os.chdir(cwd)
                print(f"Test from {cwd}")

                # Test with various
                for script_path, script_name in [
                    ('tests', "sql/test1.sql"),
                    ('tests/sql', "test1.sql"),
                    (None, "tests/sql/test1.sql"),
                    ('.', "tests/sql/test1.sql"),
                ]:
                    print(f"--Test with path name combo of {script_path} and {script_name}")
                    script = RunSQLScript(
                        config=self.config,
                        database_entry='target_database',
                        script_path=script_path,
                        script_name=script_name,
                    )

                    self.assertEqual(expected_name, f"{script}")
                    self.assertEqual(expected_name, script.name)
                    self.assertTrue(script.script_full_name.is_file())
                    self.assertEqual(expected_hash, script.get_sha1_hash())

                # Test with absolute path instead of relative
                script2 = RunSQLScript(
                    config=self.config,
                    database_entry='target_database',
                    script_name=script.script_full_name,
                    # script_path not provided (same as providing None)
                )
                # Script2 name will vary based on CWD, so we just test the expected begin and ending of the name
                self.assertTrue(
                    f"{script2}".startswith('run_sql_script'),
                    f"script2 as str {script2} does not start with run_sql_script"
                )
                self.assertTrue(
                    f"{script2}".endswith('test1.sql'),
                    f"script2 as str {script2} does not end with test1.sql"
                )
                self.assertTrue(
                    script2.name.startswith('run_sql_script'),
                    f"script2.name {script2.name} does not start with run_sql_script"
                )
                self.assertTrue(
                    script2.name.endswith('test1.sql'),
                    f"script2.name {script2.name} does not end with test1.sql"
                )
                self.assertTrue(script2.script_full_name.is_file())
                self.assertEqual(expected_hash, script2.get_sha1_hash())
        finally:
            os.chdir(save_cwd)
