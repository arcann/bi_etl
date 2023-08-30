"""
Created on Sept 12 2016

@author: Derek
"""
from bi_etl.components.readonlytable import ReadOnlyTable
from bi_etl.database.database_metadata import DatabaseMetadata
from bi_etl.scheduler.task import ETLTask


class CopyTableData(ETLTask):
    def depends_on(self):
        return []

    def load(self):
        database = self.get_parameter('database')
        assert isinstance(database, DatabaseMetadata)
        source_table_name = self.get_parameter('source_table')
        target_table_name = self.get_parameter('target_table')

        with ReadOnlyTable(
                self,
                database,
                source_table_name,
                ) as source_data:
            with ReadOnlyTable(
                    self,
                    database,
                    target_table_name,
                    ) as target_tbl:
                target_column_set = set(target_tbl.column_names)
                common_columns = list()
                for source_col in source_data.column_names:
                    if source_col in target_column_set:
                        common_columns.append(source_col)

                cols = ""
                sep = ""
                for column in common_columns:
                    cols += sep
                    cols += column
                    sep = ","

                sql = (
                    f"INSERT INTO {target_table_name} ({cols}) "
                    f"SELECT {cols} FROM {source_table_name}"
                )

                self.log.debug(sql)

                database.execute(sql, transaction=True)

        self.log.info("Done")
