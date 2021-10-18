"""
Created on Sept 12 2016

@author: Derek
"""
import hashlib
import os.path
import re

from typing import Union

from CaseInsensitiveDict import CaseInsensitiveDict

import sqlparse

from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.database import DatabaseMetadata
from bi_etl.scheduler.task import ETLTask
from bi_etl.timer import Timer


class RunSQLScript(ETLTask):
    def __init__(self,
                 datbase_entry: Union[str, DatabaseMetadata],
                 script_path: str,
                 script_name: str,
                 sql_replacements: dict = None,
                 task_id=None,
                 parent_task_id=None,
                 root_task_id=None,
                 scheduler=None,
                 task_rec=None,
                 config=None
                 ):
        super().__init__(task_id=task_id,
                         parent_task_id=parent_task_id,
                         root_task_id=root_task_id,
                         scheduler=scheduler,
                         task_rec=task_rec,
                         config=config)
        self.datbase_entry = datbase_entry
        self.script_path = script_path
        self.script_name = script_name
        self.sql_replacements = sql_replacements

        root_path, _ = os.path.split(os.getcwd())
        paths_tried = list()
        while not os.path.exists(self.script_path):
            self.script_path = os.path.join(root_path, script_path)
            if not os.path.exists(self.script_path):
                paths_tried.append(self.script_path)
                root_path, _ = os.path.split(root_path)
                _, root_no_drive = os.path.splitdrive(root_path)
                if root_no_drive in {'', '\\', os.path.sep}:
                    raise ValueError("RunSQLScript could not find script_path {}".format(paths_tried))

    def __getstate__(self):
        odict = super().__getstate__()
        odict['datbase_entry'] = self.datbase_entry
        odict['script_path'] = self.datbase_entry
        odict['script_name'] = self.script_name
        return odict

    def __setstate__(self, odict):
        self.__init__(
            datbase_entry=odict['datbase_entry'],
            script_path=odict['script_path'],
            script_name=odict['script_name'],
            task_id=odict['task_id'],
            parent_task_id=odict['parent_task_id'],
            root_task_id=odict['root_task_id'],
            # We don't pass scheduler or config from the Scheduler to the running instance
            # scheduler= odict['scheduler']
        )
        self._parameter_dict = CaseInsensitiveDict(odict['_parameter_dict'])

    def depends_on(self):
        return []

    @property
    def name(self):
        return 'run_sql_script.' + self.script_name.replace('/', '.').replace('\\', '.')

    @property
    def script_full_name(self):
        return os.path.join(self.script_path, self.script_name)

    def get_sha1_hash(self):
        block_size = 65536
        hasher = hashlib.sha1()
        with open(self.script_full_name, 'rb') as afile:
            buf = afile.read(block_size)
            while len(buf) > 0:
                # Ignore newline differences by converting all to \n
                buf = buf.replace(b'\r\n', b'\n')
                buf = buf.replace(b'\r', b'\n')
                hasher.update(buf)
                buf = afile.read(block_size)
        return hasher.hexdigest()

    def load(self):
        if isinstance(self.datbase_entry, DatabaseMetadata):
            database = self.datbase_entry
        else:
            database = self.get_database(self.datbase_entry)
        sql_replacements_str = self.config.get(database.database_name, 'SQL_Replacements', fallback='')
        if self.sql_replacements is None:
            sql_replacements = dict()
        else:
            sql_replacements = self.sql_replacements
        for replacement_line in sql_replacements_str.split('\n'):
            replacement_line = replacement_line.strip()
            if ':' in replacement_line:
                old, new = replacement_line.split(':')
                old = old.strip()
                new = new.strip()
                sql_replacements[old] = new
            elif replacement_line != '':
                self.log.error('Invalid SQL_Replacements entry {} line "{}"'.format(
                    sql_replacements_str,
                    replacement_line
                ))

        self.log.info("database={}".format(database))
        conn = database.bind.engine.raw_connection()
        try:
            try:
                conn.autocommit(True)
            except TypeError:
                conn.autocommit = True
            with conn.cursor() as cursor:
                script_full_name = self.script_full_name
                self.log.info("Running {}".format(script_full_name))
                with open(script_full_name, "rt", encoding="utf-8-sig") as sql_file:
                    sql = sql_file.read()

                for old, new in sql_replacements.items():
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
    config = BIConfigParser()
    config.read_config_ini()
    base_path = config['SQL Scripts']['path']
    script = RunSQLScript('BI_Cache', base_path, "bi/cd_indicator.sql")
    # script.load()
    print(f"Has is {script.get_sha1_hash()}")


if __name__ == '__main__':
    main()
