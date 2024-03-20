from bi_etl.components.csvreader import CSVReader
from bi_etl.components.table import Table
from examples.example_etl_base import ExampleETLTaskBase


class ExampleETL1(ExampleETLTaskBase):
    def load(self):
        target_database = self.get_target_database_metadata()
        with CSVReader(
                self,
                filedata=self.package_path / 'tests' / 'test_files' / 'utf8_with_header.csv',
                encoding='utf-8',
        ) as source_data:
            ddl = """
            CREATE TABLE IF NOT EXISTS example_1_table (
                str     VARCHAR(50),
                int     INTEGER,
                float   FLOAT,
                date    DATETIME,
                unicode TEXT 
            )
            """

            target_database.execute(ddl)

            with Table(
                self,
                target_database,
                'example_1_table'
            ) as target_table:
                for row in source_data:
                    target_table.insert(row)


if __name__ == '__main__':
    ExampleETL1().run()
