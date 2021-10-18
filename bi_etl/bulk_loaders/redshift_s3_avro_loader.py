# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import fastavro
import itertools
import os.path
import os.path
import typing
from tempfile import TemporaryDirectory

from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base

if typing.TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.task import ETLTask


class RedShiftS3AvroBulk(RedShiftS3Base):
    def __init__(self,
                 config: BIConfigParser,
                 config_section: str = 's3_bulk',
                 s3_user_id: typing.Optional[str] = None,
                 s3_keyring_password_section: typing.Optional[str] = None,
                 s3_bucket_name: typing.Optional[str] = None,
                 s3_folder: typing.Optional[str] = None,
                 s3_files_to_generate: typing.Optional[int] = None,
                 ):
        super().__init__(
            config=config,
            config_section=config_section,
            s3_user_id=s3_user_id,
            s3_keyring_password_section=s3_keyring_password_section,
            s3_bucket_name=s3_bucket_name,
            s3_folder=s3_folder,
            s3_files_to_generate=s3_files_to_generate,
        )
        self.s3_file_delimiter = '|'
        self.null_value = ''
        self.s3_clear_before = True
        self.s3_clear_when_done = True
        self.analyze_compression = None

    @property
    def needs_all_columns(self):
        return False

    def get_copy_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
            file_compression: str = '',
            analyze_compression: str = None,
            options: str = '',
    ):
        analyze_compression = analyze_compression or self.analyze_compression
        if analyze_compression:
            options += f' COMPUPDATE {self.analyze_compression} '

        # TODO: This SQL gets syntax error at or near "credentials"
        return f"""\
                COPY {table_to_load} FROM 's3://{self.s3_bucket_name}/{s3_source_path}'                      
                     credentials 'aws_access_key_id={self.s3_user_id};aws_secret_access_key={self.s3_password}'
                     AVRO 'auto'
                     {file_compression}  
                     {options}
               """

    @staticmethod
    def distribute(iterable, n):
        """Distribute the items from *iterable* among *n* smaller iterables.

        From https://more-itertools.readthedocs.io/en/stable/_modules/more_itertools/more.html

        This function uses :func:`itertools.tee` and may require significant
        storage. If you need the order items in the smaller iterables to match the
        original iterable, see :func:`divide`.

        """
        if n < 1:
            raise ValueError('n must be at least 1')

        children = itertools.tee(iterable, n)
        return [itertools.islice(it, index, None, n) for index, it in enumerate(children)]

    def load_from_iterator(
            self,
            iterator: typing.Iterator,
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str = None,
            parent_task: typing.Optional[ETLTask] = None,
    ):
        with TemporaryDirectory() as temp_dir:
            # TODO: Genereate schema from table
            schema = {
                "name": table_to_load,
                "type": "record",
                'fields': [
                    {'name': 'station', 'type': 'string'},
                    {'name': 'time', 'type': 'long'},
                    {'name': 'temp', 'type': 'int'},
                ],
            }
            """
            boolean: a binary value
            int: 32-bit signed integer
            long: 64-bit signed integer
            float: single precision (32-bit) IEEE 754 floating-point number
            double: double precision (64-bit) IEEE 754 floating-point number
            bytes: sequence of 8-bit unsigned bytes
            string: unicode character sequence
            """
            parsed_schema = fastavro.parse_schema(schema)

            file_number = 1
            filepath = os.path.join(temp_dir, f'data_{file_number}.json.gz')
            with open(filepath, 'wb') as avro_file:
                # avro_iterators = self.distribute(iterator, writer_pool_size)
                fastavro.writer(avro_file, parsed_schema, iterator)

            self.load_from_files(
                [filepath],
                table_object=table_object,
                table_to_load=table_to_load,
                perform_rename=perform_rename,
                analyze_compression=analyze_compression,
            )
