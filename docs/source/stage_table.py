from bi_etl.components.csvreader import CSVReader
from bi_etl.components.table import Table
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base_From_Ini_Env
from bi_etl.scheduler.task import ETLTask


class STAGE_TABLE(ETLTask):

    def load(self):
        # get_database is a method of ETLTask that will get a connected
        # database instance. See docs.
        target_database = self.get_database('EXAMPLE_DB')

        # Make an ETL Component to read the source file
        with CSVReader(
                self,
                filedata=r"E:\Data\training\ExampleData1-a.csv",
                ) as source_file:

            # Make an ETL Component to write the target dimension data.
            with Table(
                    task=self,
                    database=target_database,
                    table_name='example_1',
                    ) as target_table:

                # Truncate the table before load
                target_table.truncate()

                # Start looping through source data
                for row in source_file:
                    target_table.insert(row)

                # Issue a commit at the end.
                # If your database needs more frequent commits, that can be done as well.
                target_table.commit()

                self.log.info("Done")


# Code to run the load when run directly
if __name__ == '__main__':
    config = BI_ETL_Config_Base_From_Ini_Env()
    STAGE_TABLE(config=config).run(suppress_notifications=True)
