"""
Created on Aug 28, 2014

@author: Derek Wood
"""

from bi_etl.scheduler.task import ETLTask, Status
from bi_etl.components.table import Table

class ETL_Task_Status_CD(ETLTask):

    def depends_on(self):
        return [ 
               ]

    def load(self):
        log = self.log
        
        log.info('testing unicode logging support: ü µ σ 泽 \u2013')
               
        log.info("Connecting to database")
        database_name = self.config.get('Scheduler', 'database')
        schema = self.config.get('Scheduler', 'schema', fallback=None)
        database = self.get_database(database_name, schema=schema)
        
        with Table(self,
                   database,
                   'etl_task_status_cd',
                   delete_flag = 'delete_flag',
                   track_source_rows=True,
                   ) as etl_task_status_cd:
            # cdlist.trace = True
            # etl_task_status_cd.trace_data = True
            etl_task_status_cd.fill_cache()
            
            for status in Status:
                row = etl_task_status_cd.Row(logical_name='Status')
                row['status_id'] = status.value
                status_name = status.name.replace('_',' ').title()
                status_name = status_name.replace('Cpu','CPU')
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
            etl_task_status_cd.update_not_processed(logically_deleted,)
    
            etl_task_status_cd.commit()
        log.info("Done")


if __name__ == '__main__':
    task = ETL_Task_Status_CD()
    task.run(suppress_notifications= True)