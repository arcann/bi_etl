import random
from datetime import datetime, timedelta

from bi_etl.components.csvreader import CSVReader
from bi_etl.components.table import Table
from examples.example_etl_base import ExampleETLTaskBase


class ExampleETL2(ExampleETLTaskBase):
    def load(self):
        target_database = self.get_target_database_metadata()

        ddl = """
        CREATE TABLE IF NOT EXISTS example_2_table (
            id           INTEGER,
            name         VARCHAR(50),
            balance      FLOAT,
            last_updated DATETIME
        )
        """

        target_database.execute(ddl)

        # From https://1000randomnames.com/
        names = [
            'Adalee Meadows',
            'Wayne Ali',
            'Zelda Santiago',
            'Beckham Cabrera',
            'Daleyza Wilkerson',
            'Carmelo Hawkins',
            'Ariel Becker',
            'Lawson Knapp',
            'Linda Correa',
            'Zakai Shannon',
        ]

        with Table(
            self,
            target_database,
            'example_2_table'
        ) as target_table:
            # Row iteration header stores the column definitions once centrally to save time
            row_iteration_header = target_table.generate_iteration_header()

            last_updated = datetime(year=2021, month=1, day=1)
            time_increment = timedelta(hours=12)

            self.log.info(f"Generating {self.config.row_generator.rows_to_generate:,} rows")

            for row_number in range(self.config.row_generator.rows_to_generate):
                row = target_table.Row(
                    iteration_header=row_iteration_header,
                    data=dict(
                        id=row_number,
                        name=random.choice(names),
                        balance=random.betavariate(15, 5),
                        last_updated=last_updated,
                        # Extra column not in the target.  This will generate a Sanity Check warning.
                        extra='This value has nowhere to go',
                    )
                )
                # NOTE: This way of setting row values also works
                # row['id'] = row_number
                # row['name'] = random.choice(names)
                # row['balance'] = random.betavariate(15, 5)
                # row['last_updated'] = last_updated

                last_updated += time_increment
                target_table.insert(row)
            target_table.commit()


if __name__ == '__main__':
    ExampleETL2().run()
