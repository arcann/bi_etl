from datetime import datetime
from io import BytesIO, StringIO
from urllib.request import urlopen
from zipfile import ZipFile

from config_wrangler.config_templates.logging_config import LoggingConfig

from bi_etl.components.csvreader import CSVReader
from bi_etl.components.data_analyzer import DataAnalyzer
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base, BI_ETL_Config_Section, Notifiers
from bi_etl.scheduler.task import ETLTask


class Analyzer(ETLTask):

    def load(self):
        with DataAnalyzer() as a:
            resp = urlopen('https://aidsinfo.unaids.org/documents/Estimates_2024_en.zip')
            myzip = ZipFile(BytesIO(resp.read()))
            source_files = myzip.namelist()

            for source_file in source_files:
                data_content = StringIO(myzip.open(source_file).read().decode('utf-8'))
                with CSVReader(self, data_content, encoding='utf8') as source_data:
                    for row in source_data:
                        a.analyze_row(row)
            print()
            print()
            print(f'Analysis for {source_files}')
            print(f'As of {datetime.now()}')
            a.print_analysis()
            print()
            print()

        self.log.info("Done")


if __name__ == '__main__':
    config = BI_ETL_Config_Base(
        logging=LoggingConfig(
            log_folder=None,
            log_levels={'root': 'INFO'},
        ),
        bi_etl=BI_ETL_Config_Section(
            environment_name='test'
        ),
        notifiers=Notifiers(
            failures=[],
        )
    )
    Analyzer(config).run()
