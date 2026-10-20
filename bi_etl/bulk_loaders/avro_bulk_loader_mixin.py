# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import os.path
from dataclasses import dataclass
from datetime import date, datetime, time as time_type, timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Callable, Iterable, Optional

import fastavro

from bi_etl.timer import Timer
from bi_etl.utility.json import json_dumps

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.etl_task import ETLTask


class AvroBulkLoaderMixin:
    """Mixin providing Avro schema generation, chunk writing, codec setup, and loading.

    Subclasses must call :meth:`_init_avro` from their ``__init__`` to
    configure the compression codec and set the chunk size.

    .. note::

       :class:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader` also defines
       :meth:`load_from_iterable` (raising ``NotImplementedError``).  For
       this mixin's implementation to win the MRO, concrete Avro loaders
       must list ``AvroBulkLoaderMixin`` *before* :class:`BulkLoader` (or
       any base deriving from it) in their own bases.

       This mixin intentionally does **not** override
       :attr:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader.needs_all_columns`,
       since the correct value is loader-specific, not generic to Avro.
       Each concrete Avro loader should override the property directly::

           @property
           def needs_all_columns(self):
               return False
    """

    def _init_avro(self, chunk_size: int = 50000):
        """
        Initialise Avro. Call from subclass ``__init__``.
        """
        self.chunk_size = chunk_size
        try:
            import snappy
            self.codec = 'snappy'
        except ImportError:
            self.codec = 'deflate'
        self._translate_columns: dict[str, Callable] = {}

    # --- Schema helpers ------------------------------------------------------

    def _get_avro_schema(self, table_object: Table, table_name: str) -> dict:
        """Build an Avro record schema from *table_object*'s columns."""

        @dataclass
        class TypeDefn:
            type_list: list[str | dict]
            conversion_function: Callable | None = None

        map_type = {"type": "map", "values": "string"}
        array_type = {"type": "array", "items": "string"}

        type_map = {
            str: TypeDefn(type_list=['string']),
            bytes: TypeDefn(type_list=['bytes']),
            date: TypeDefn(type_list=['date']),
            datetime: TypeDefn(
                type_list=[
                    {
                        "type": "long",
                        "logicalType": "timestamp-millis"
                    }
                ]
            ),
            time_type: TypeDefn(
                type_list=[
                    {
                        "type": "long",
                        "logicalType": 'time-millis',
                    }
                ]
            ),
            timedelta: TypeDefn(type_list=['long'], conversion_function=timedelta.total_seconds),
            bool: TypeDefn(type_list=['boolean']),
            int: TypeDefn(type_list=['long']),
            float: TypeDefn(type_list=['double']),
            Decimal: TypeDefn(type_list=['int', 'double']),
            object: TypeDefn(type_list=['string'], conversion_function=json_dumps),
            dict: TypeDefn(type_list=['string'], conversion_function=json_dumps),
            list: TypeDefn(type_list=['string'], conversion_function=json_dumps),
            set: TypeDefn(type_list=['string'], conversion_function=json_dumps),
        }
        fields = []
        columns = table_object.columns
        for column in columns:
            python_type = table_object._get_python_type(column.type)
            col_type_defn = type_map.get(python_type, TypeDefn(['string'], conversion_function=str))
            if col_type_defn.conversion_function is not None:
                self._translate_columns[column.name] = col_type_defn.conversion_function
            fields.append(
                {
                    'name': column.name,
                    'type': ['null', *col_type_defn.type_list],
                    'default': None,
                }
            )
        return {
            'name': table_name,
            'type': 'record',
            'fields': fields,
        }

    def _parse_avro_schema(self, table_object: Table, table_name: str):
        """Build and parse an Avro schema, returning the parsed form."""
        schema = self._get_avro_schema(table_object, table_name)
        try:
            parsed_schema = fastavro.parse_schema(schema)
            self.log.debug(f"Avro schema = {schema}")
            self.log.debug(f"Avro parsed_schema = {parsed_schema}")
            return parsed_schema
        except Exception:
            self.log.error(f"Avro schema that errored = {schema}")
            raise

    # --- Chunk writing -------------------------------------------------------

    def _write_avro_chunk(
            self,
            temp_dir: str,
            file_number: int,
            parsed_schema,
            data_chunk: list,
            local_files_list: list,
    ):
        """Write *data_chunk* rows to a numbered Avro file in *temp_dir*."""
        self.log.debug(f"Starting bulk load chunk {file_number}")
        filepath = os.path.join(temp_dir, f'data_{file_number}.avro')
        local_files_list.append(filepath)
        with open(filepath, 'wb') as avro_file:
            fastavro.writer(avro_file, parsed_schema, data_chunk, codec=self.codec)
        self.log.debug(f"Closed bulk load chunk {file_number}: {filepath}")

    # --- Load from iterable ---------------------------------------------------

    def load_from_iterable(
            self,
            iterable: Iterable,
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str | None = None,
            parent_task: Optional[ETLTask] = None,
    ) -> int:
        """Write rows from *iterable* to local Avro files and load them via :meth:`load_from_files`.

        Parameters
        ----------
        iterable
            Source of :class:`~bi_etl.components.row.row.Row` objects to load.
        table_object
            Table the rows are being loaded into.
        table_to_load
            Name of the table (or temp table) to load into. Defaults to
            ``table_object.qualified_table_name``.
        perform_rename
            Passed through to :meth:`load_from_files`.
        progress_frequency
            Seconds between progress log messages. Pass ``None`` to disable.
        analyze_compression
            Passed through to :meth:`load_from_files`.
        parent_task
            Unused by this implementation, present for interface compatibility.

        Returns
        -------
        int
            Number of rows written.
        """
        table_to_load = table_to_load or table_object.qualified_table_name

        with TemporaryDirectory(
                dir=self.config.temp_file_path,
                ignore_cleanup_errors=True,
        ) as temp_dir:
            parsed_schema = self._parse_avro_schema(table_object, table_to_load)

            file_number = 0
            data_length = 0
            local_files_list = []
            data_chunk = []

            progress_timer = Timer()
            for row_number, row in enumerate(iterable):
                data_dict = row.as_dict
                # Translate column values
                for column_name, translate_function in self._translate_columns.items():
                    if column_name in data_dict:
                        data_dict[column_name] = translate_function(data_dict[column_name])
                data_chunk.append(data_dict)

                if len(data_chunk) >= self.chunk_size:
                    data_length += len(data_chunk)
                    file_number += 1
                    self._write_avro_chunk(
                        temp_dir=temp_dir,
                        file_number=file_number,
                        parsed_schema=parsed_schema,
                        data_chunk=data_chunk,
                        local_files_list=local_files_list,
                    )
                    data_chunk = []

                if progress_frequency is not None:
                    if 0 < progress_frequency < progress_timer.seconds_elapsed:
                        self.log.info(f"Wrote row {row_number:,}")
                        progress_timer.reset()

            # Write final chunk
            if data_chunk:
                data_length += len(data_chunk)
                file_number += 1
                self._write_avro_chunk(
                    temp_dir=temp_dir,
                    file_number=file_number,
                    parsed_schema=parsed_schema,
                    data_chunk=data_chunk,
                    local_files_list=local_files_list,
                )

            if data_length > 0:
                self.log.debug(f"Loading from files {local_files_list}")
                rows_loaded = self.load_from_files(
                    local_files_list,
                    table_object=table_object,
                    table_to_load=table_to_load,
                    perform_rename=perform_rename,
                    analyze_compression=analyze_compression,
                )
                if rows_loaded != data_length:
                    self.log.error(
                        f"COPY from files should have loaded {data_length:,} "
                        f"but it reports {rows_loaded:,} rows loaded"
                    )
                return data_length
            else:
                self.log.info(f"{self} had nothing to do with 0 rows found")
                return 0
