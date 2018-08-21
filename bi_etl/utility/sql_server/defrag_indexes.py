"""
Created on Sept 12 2016

@author: Derek
"""
from argparse import ArgumentParser

from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.components.sqlquery import SQLQuery
from bi_etl.scheduler.task import ETLTask


class DefragIndexes(ETLTask):
    def depends_on(self):
        return []

    def load(self):
        db_name = self.get_parameter('database', default='BI_Cache')
        database = self.get_database(db_name)
        self.log.info("Defragmenting indexes in {} = {}".format(db_name, database))
        # (user_id, password) = self.config.get_database_connection_tuple('BI_Cache', 'systemBI')

        sql = """
                SELECT
                       rtrim(ltrim(ns.name)) + '.' + nt.name AS table_name,
                       ni.name AS index_name,
                       index_type_desc,
                       avg_fragmentation_in_percent,
                       fragment_count,
                       page_count,
                       avg_page_space_used_in_percent,
                       record_count
                FROM   sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, NULL) s
                       INNER JOIN
                       sys.tables nt
                        ON s.object_id = nt.object_id
                       INNER JOIN
                       sys.indexes ni
                        ON ni.index_id = s.index_id
                        AND ni.object_id = s.object_id
                        join sys.schemas ns on ns.schema_id = nt.schema_id
                WHERE avg_fragmentation_in_percent > 20
                  AND index_type_desc IN('CLUSTERED INDEX', 'NONCLUSTERED INDEX')
                  AND ni.name not in ('PK_BigFatTable')
                ORDER BY avg_fragmentation_in_percent DESC
                """
        with SQLQuery(self, database, sql, logical_name="fragged_indexes") as fragged_indexes:
            for row in fragged_indexes:
                self.log.info("Rebuilding {index} ON {table} which is {pct:5.1f}% fragmented".format(
                    index=row['index_name'],
                    table=row['table_name'],
                    pct=row['avg_fragmentation_in_percent']
                ))
                rebuild_sql = "ALTER INDEX [{index}] ON {table} REBUILD WITH (SORT_IN_TEMPDB = ON)".format(
                    index=row['index_name'],
                    table=row['table_name'],
                )
                database.execute_direct(rebuild_sql)

            self.log.info("-" * 80)


if __name__ == '__main__':
    parser = ArgumentParser(description="Run ETL")
    parser.add_argument('--database', type=str, help='Database entry in config.ini to use', default='BI_Cache')
    args = parser.parse_args()
    config = BIConfigParser()
    config.read_config_ini()
    df = DefragIndexes()
    df.add_parameter("database", args.database)
    df.run()
