from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.scheduler.task import ETLTask


class StaticReader(ETLComponent):
    ROWS = 10**6
    COLS = 100
    TEXT_COLS = 5
    INT_COLS = COLS - TEXT_COLS

    def _obtain_column_names(self):
        self._column_names = [f'x{i}' for i in range(self.COLS)]

    def _raw_rows(self):
        this_iteration_header = self.full_iteration_header
        for row_num in range(self.ROWS):
            row_list = [f'x{i}[{row_num}]' for i in range(self.TEXT_COLS)]
            row_list.extend([i + row_num for i in range(self.INT_COLS)])
            d = self.Row(data=row_list, iteration_header=this_iteration_header)
            yield d


class TestStaticReader(ETLTask):
    def depends_on(self):
        return []

    def load(self):
        budget_amount = 0
        with StaticReader(self) as source_data:
            for row in source_data:
                budget_amount += row['x6']

        self.log.info(budget_amount)

        self.log.info("Done")


if __name__ == '__main__':
    TestStaticReader(config=BI_ETL_Config_Base()).run()
