from bi_etl.components.csvreader import CSVReader
from bi_etl.components.table import Table
from examples.example_etl_base import ExampleETLTaskBase


class ExampleETL1(ExampleETLTaskBase):
    def load(self):
        target_database = self.get_target_database_metadata()

        # Note: ExitStack automatically closes tables that are opened using the stack.
        with (self.ExitStack() as stack):
            source_data: CSVReader = stack.enter_context(
                CSVReader(
                    self,
                    filedata=self.package_path / 'tests' / 'test_files' / 'utf8_with_header.csv',
                    encoding='utf-8',
                )
            )
            target_table: Table = stack.enter_context(
                Table(
                    self,
                    target_database,
                    'example_1_table'
                )
            )

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

            for row in source_data:
                target_table.insert(row)


if __name__ == '__main__':
    ExampleETL1().run()
