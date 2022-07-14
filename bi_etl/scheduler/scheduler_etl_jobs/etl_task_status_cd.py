"""
Created on Aug 28, 2014

@author: Derek Wood
"""
from bi_etl.components.table import Table
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base, BI_ETL_Config_Base_From_Ini_Env
from bi_etl.scheduler.task import ETLTask, Status


class ETL_Task_Status_CD(ETLTask):
    def __init__(self,
                 task_id=None,
                 parent_task_id=None,
                 root_task_id=None,
                 scheduler=None,
                 task_rec=None,
                 config: BI_ETL_Config_Base = None,
                 ):
        if config is None:
            config = BI_ETL_Config_Base_From_Ini_Env()
        super().__init__(
            config=config,
            task_id=task_id,
            parent_task_id=parent_task_id,
            root_task_id=root_task_id,
            scheduler=scheduler,
            task_rec=task_rec,
        )
        assert isinstance(self.config, BI_ETL_Config_Base)

    def depends_on(self):
        return [
        ]

    def load(self):
        log = self.log

        log.info("Connecting to scheduler database")
        database = self.get_database_metadata(self.config.bi_etl.scheduler.db)

        with Table(self,
                   database,
                   'etl_task_status_cd',
                   delete_flag='delete_flag',
                   track_source_rows=True,
                   ) as etl_task_status_cd:
            # cdlist.trace = True
            # etl_task_status_cd.trace_data = True
            etl_task_status_cd.fill_cache()

            iteration_header = etl_task_status_cd.full_iteration_header
            for status in Status:
                row = etl_task_status_cd.Row(iteration_header=iteration_header)
                row['status_id'] = status.value
                status_name = status.name.replace('_', ' ').title()
                status_name = status_name.replace('Cpu', 'CPU')
                row['status_name'] = status_name
                # Add delete_flag to source
                row['delete_flag'] = 'N'

                # etl_task_status_cd.trace_data = True
                # self.debug_sql(True)
                etl_task_status_cd.upsert(
                    row,
                )

            etl_task_status_cd.commit()

            # Process deletes
            log.info("Checking for deletes")
            logically_deleted = etl_task_status_cd.Row()
            logically_deleted['delete_flag'] = 'Y'
            etl_task_status_cd.update_not_processed(logically_deleted)

            etl_task_status_cd.commit()
        log.info("Done")


if __name__ == '__main__':
    task = ETL_Task_Status_CD()
    task.run(suppress_notifications=True)
