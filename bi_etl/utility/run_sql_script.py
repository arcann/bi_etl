"""
Created on Sept 12 2016

@author: Derek
"""
import hashlib
import os.path

from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.scheduler.task import ETLTask
from bi_etl.timer import Timer


class RunSQLScript(ETLTask):
    def __init__(self,
                 datbase_entry: str,
                 script_path: str,
                 script_name: str,
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

    def depends_on(self):
        return []

    @property
    def name(self):
        return 'run_sql_script.' + self.script_name

    @property
    def script_full_name(self):
        return os.path.join(self.script_path, self.script_name)

    def get_sha1_hash(self):
        block_size = 65536
        hasher = hashlib.sha1()
        with open(self.script_full_name, 'rb') as afile:
            buf = afile.read(block_size)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(block_size)
        return hasher.hexdigest()

    def load(self):
        database = self.get_database(self.datbase_entry)
        sql_replacements_str = self.config.get(self.datbase_entry, 'SQL_Replacements', fallback='')
        sql_replacements = dict()
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
            conn.autocommit(True)
            cursor = conn.cursor()

            script_full_name = self.script_full_name
            self.log.info("Running {}".format(script_full_name))
            with open(script_full_name, "rt", encoding="utf-8-sig") as sql_file:
                sql = sql_file.read()

            for old, new in sql_replacements.items():
                if old in sql:
                    self.log.info('replacing "{}" with "{}"'.format(old, new))
                    sql = sql.replace(old, new)

            parts = sql.split("\nGO\n")
            for part_sql in parts:
                if part_sql.endswith('GO'):
                    part_sql = part_sql[:-2]
                self.log.debug("Executing SQL:\n" + part_sql)
                timer = Timer()

                # noinspection PyBroadException
                try:
                    cursor.execute(part_sql)
                except Exception as e:
                    self.log.error(part_sql)
                    raise e

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
        finally:
            conn.close()


def main():
    config = BIConfigParser()
    config.read_config_ini()
    base_path = config['SQL Scripts']['path']
    script = RunSQLScript('BI_Cache', base_path, "bi/cd_indicator.sql")
    script.load()


if __name__ == '__main__':
    main()
