from bi_etl.components.readonlytable import ReadOnlyTable
from bi_etl.components.table import Table
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base_From_Ini_Env
from bi_etl.scheduler.task import ETLTask


class D_WBS(ETLTask):
    def load(self):
        # get_database is a method of ETLTask that will get a connected
        # database instance. See docs.
        source_database = self.get_database('WAREHOUSE')
        target_database = self.get_database('DATAMART')

        # Make an ETL Component to read the source view.
        with ReadOnlyTable(
                task=self,
                database=source_database,
                table_name='d_wbs_src_vw',
        ) as source_data:

            # Make an ETL Component to write
            # the target dimension data.
            with Table(
                    task=self,
                    database=target_database,
                    table_name='d_wbs',
            ) as target_table:

                # Enable option to generate a surrogate key value for
                # the primary key
                target_table.auto_generate_key = True

                # Specify the column to get the last update
                # date value (from system date)
                target_table.last_update_date = 'last_update_date'

                # Specify the column to get Y/N delete flag values.
                target_table.delete_flag = 'delete_flag'

                # Track rows processed for logically_delete_not_processed
                target_table.track_source_rows = True

                # Define an alternate key lookup using the
                # natural key column. If we don't, the
                # upsert process would try and use the primary key
                # which is the surrogate key.
                target_table.define_lookup('AK', ['wbs_natural_key'])

                # Fill the cache to improve performance
                target_table.fill_cache()

                # Log entry
                self.log.info(f"Processing rows from {source_data}")

                # Start looping through source data
                for row in source_data:
                    # Upsert (Update else Insert) each source row
                    target_table.upsert(
                        row,
                        # Use the alternate key define above
                        # to perform lookup for existing row
                        lookup_name='AK'
                    )
                target_table.commit()

                self.log.info(f"Processing deletes from {target_table}")
                target_table.logically_delete_not_processed()
                target_table.commit()

                self.log.info("Done")


# Code to run the load when run directly
if __name__ == '__main__':
    config = BI_ETL_Config_Base_From_Ini_Env()
    D_WBS(config=config).run(suppress_notifications=True)
