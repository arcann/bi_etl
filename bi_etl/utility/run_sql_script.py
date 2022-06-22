"""
Created on Sept 12 2016

@author: Derek
"""
import hashlib
import os
import re
from pathlib import Path
from typing import Union, Dict

import sqlparse
from pydicti import Dicti

from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base, BI_ETL_Config_Base_From_Ini_Env
from bi_etl.database import DatabaseMetadata
from bi_etl.scheduler.task import ETLTask
from bi_etl.timer import Timer


class RunSQLScript(ETLTask):
    def __init__(self,
                 config: BI_ETL_Config_Base,
                 database_entry: Union[str, DatabaseMetadata],
                 script_name: Union[str, Path],
                 script_path: Union[str, Path] = None,
                 sql_replacements: Dict[str, str] = None,
                 task_id=None,
                 parent_task_id=None,
                 root_task_id=None,
                 scheduler=None,
                 task_rec=None,
                 ):
        super().__init__(task_id=task_id,
                         parent_task_id=parent_task_id,
                         root_task_id=root_task_id,
                         scheduler=scheduler,
                         task_rec=task_rec,
                         config=config)
        self.database_entry = database_entry
        self.sql_replacements = sql_replacements
        self.script_name = Path(script_name)
        if script_path is None:
            self.script_path = None
        else:
            self.script_path = Path(script_path)

        paths_tried = list()
        paths_tried.append(self.script_full_name)
        if not self.script_full_name.exists():
            for path_to_try in Path.cwd().parents:
                if script_path:
                    self.script_path = path_to_try / script_path
                else:
                    self.script_path = path_to_try
                paths_tried.append(self.script_full_name)
                if self.script_full_name.exists():
                    break

        if not self.script_full_name.exists():
            raise ValueError(f"RunSQLScript could not find the script {self.script_name} tried {paths_tried}")

    def __getstate__(self):
        odict = super().__getstate__()
        odict['config'] = self.config
        odict['database_entry'] = self.database_entry
        odict['script_path'] = self.script_path
        odict['script_name'] = self.script_name
        return odict

    def __setstate__(self, odict):
        self.__init__(
            config=odict['config'],
            database_entry=odict['database_entry'],
            script_path=odict['script_path'],
            script_name=odict['script_name'],
            task_id=odict['task_id'],
            parent_task_id=odict['parent_task_id'],
            root_task_id=odict['root_task_id'],
            # We don't pass scheduler or config from the Scheduler to the running instance
            # scheduler= odict['scheduler']
        )
        self._parameter_dict = Dicti(odict['_parameter_dict'])

    def depends_on(self):
        return []

    @property
    def name(self):
        name = str(self.script_name).replace('/', '.').replace('\\', '.')
        return f"run_sql_script.{name}"

    @property
    def script_full_name(self) -> Path:
        if self.script_path is None:
            return self.script_name.resolve()
        else:
            return (self.script_path / self.script_name).resolve()

    def get_sha1_hash(self):
        block_size = 65536
        hasher = hashlib.sha1()
        with self.script_full_name.open('rb') as file:
            buf = file.read(block_size)
            while len(buf) > 0:
                # Ignore newline differences by converting all to \n
                buf = buf.replace(b'\r\n', b'\n')
                buf = buf.replace(b'\r', b'\n')
                hasher.update(buf)
                buf = file.read(block_size)
        return hasher.hexdigest()

    def load(self):
        if isinstance(self.database_entry, DatabaseMetadata):
            database = self.database_entry
        else:
            database = self.get_database(self.database_entry)
        if self.sql_replacements is None:
            self.sql_replacements = dict()

        self.log.info("database={}".format(database))
        conn = database.bind.engine.raw_connection()
        try:
            conn.autocommit = True
            with conn.cursor() as cursor:
                self.log.info(f"Running {self.script_full_name}")
                with self.script_full_name.open("rt", encoding="utf-8-sig") as sql_file:
                    sql = sql_file.read()

                for old, new in self.sql_replacements.items():
                    if old in sql:
                        self.log.info('replacing "{}" with "{}"'.format(old, new))
                        sql = sql.replace(old, new)

                go_pattern = re.compile('\nGO\n', flags=re.IGNORECASE)
                parts = go_pattern.split(sql)
                for go_part_sql in parts:
                    sub_parts = sqlparse.split(go_part_sql)
                    for part_sql in sub_parts:
                        part_sql = part_sql.strip()
                        if part_sql.upper().endswith('GO'):
                            part_sql = part_sql[:-2]
                        part_sql = part_sql.strip()
                        part_sql = part_sql.strip(';')
                        part_sql = part_sql.strip()
                        if part_sql != '':
                            timer = Timer()

                            if part_sql.startswith('EXEC') and database.bind.dialect.dialect_description == 'mssql+pyodbc':
                                sql_statement = sqlparse.parse(part_sql)[0]
                                procedure = None
                                procedure_args = list()
                                for token in sql_statement.tokens:
                                    if isinstance(token, sqlparse.sql.Identifier):
                                        procedure = token.value
                                    if isinstance(token, sqlparse.sql.IdentifierList):
                                        procedure_args_raw = token.value
                                        procedure_args_list = procedure_args_raw.split(',')
                                        for arg in procedure_args_list:
                                            arg = arg.strip()
                                            arg2 = arg.strip("'")
                                            procedure_args.append(arg2)
                                if procedure is None:
                                    raise ValueError(f"Error parsing procedure parts {sql_statement.tokens}")
                                self.log.debug(f"Executing Procedure: {procedure} with args {procedure_args}")
                                database.execute_procedure(procedure, *procedure_args, dpapi_connection=conn)
                                self.log.info("Procedure took {} seconds".format(timer.seconds_elapsed_formatted))
                            else:
                                self.log.debug(f"Executing SQL:\n{part_sql}\n--End SQL")

                                # noinspection PyBroadException
                                try:
                                    cursor.execute(part_sql)
                                except Exception as e:
                                    error_msg = str(e).lower()
                                    if ('buffer length (0)' in error_msg
                                            or "empty query" in error_msg):
                                        # Skip errors for blank SQL
                                        pass
                                    else:
                                        self.log.error(part_sql)
                                        raise

                                self.log.info("Statement took {} seconds".format(timer.seconds_elapsed_formatted))
                                # noinspection PyBroadException
                                try:
                                    row = cursor.fetchone()
                                    self.log.info("Results:")
                                    while row:
                                        self.log.info(row)
                                        row = cursor.fetchone()
                                except Exception:
                                    self.log.info("No results returned")
                                self.log.info("{:,} rows were affected".format(cursor.rowcount))
                                # self.log.info("Statement took {} seconds and affected {:,} rows"
                                #               .format(timer.seconds_elapsed_formatted, ret.rowcount))
                                # if ret.returns_rows:
                                #     self.log.info("Rows returned:")
                                #     for row in ret:
                                #         self.log.info(dict_to_str(row))
                                self.log.info("-" * 80)

            conn.commit()
        finally:
            conn.close()


def main():
    os.environ['notifiers_failures'] = ''
    os.environ['notifiers_failed_notifications'] = ''
    config = BI_ETL_Config_Base_From_Ini_Env()
    package_path = Path(__file__).parents[1]
    save_cwd = Path.cwd()
    try:
        for cwd in [
            package_path,
            package_path / 'tests',
            package_path / 'tests' / 'etl_jobs',
        ]:
            os.chdir(cwd)
            script = RunSQLScript(
                config=config,
                database_entry='target_database',
                script_path='tests',
                script_name="sql/test1.sql"
            )
            # script.load()
            print(f"{script} in {script.script_full_name} has hash {script.get_sha1_hash()}")

            script = RunSQLScript(
                config=config,
                database_entry='target_database',
                script_name="tests/sql/test1.sql",
            )
            print(f"{script} in {script.script_full_name} has hash {script.get_sha1_hash()}")

            script = RunSQLScript(
                config=config,
                database_entry='target_database',
                script_name="test1.sql",
                script_path='tests/sql',
            )
            print(f"{script} in {script.script_full_name} has hash {script.get_sha1_hash()}")
    finally:
        os.chdir(save_cwd)


if __name__ == '__main__':
    main()
