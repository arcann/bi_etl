# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import os.path
from datetime import date, datetime, time as time_type, timedelta
from decimal import Decimal
from typing import *

import fastavro

if TYPE_CHECKING:
    from bi_etl.components.table import Table


class AvroBulkLoaderMixin:
    """Mixin providing Avro schema generation, chunk writing, and codec setup.

    Subclasses must call :meth:`_init_avro` from their ``__init__`` to
    configure the compression codec.

    .. note::

       This mixin intentionally does **not** override
       :attr:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader.needs_all_columns`.
       Because :class:`BulkLoader` already defines that property (returning
       ``True``), Python's MRO would resolve to ``BulkLoader`` before a
       mixin listed later in the bases.  Each concrete Avro loader should
       override the property directly::

           @property
           def needs_all_columns(self):
               return False
    """

    def _init_avro(self):
        """Initialise Avro compression codec.  Call from subclass ``__init__``."""
        try:
            import snappy
            self.codec = 'snappy'
        except ImportError:
            self.codec = 'deflate'

    # --- Schema helpers ------------------------------------------------------

    @staticmethod
    def _get_avro_schema(table_object: Table, table_name: str) -> dict:
        """Build an Avro record schema from *table_object*'s columns."""
        type_map = {
            str: ['string'],
            bytes: ['bytes'],
            date: ['string'],
            datetime: ['string'],
            time_type: ['string'],
            timedelta: ['string'],
            bool: ['boolean'],
            int: ['long'],
            float: ['double'],
            Decimal: ['int', 'double'],
        }
        fields = []
        columns = table_object.columns
        for column in columns:
            col_type = type_map.get(column.type.python_type, ['string'])
            fields.append({
                'name': column.name,
                'type': ['null'] + col_type,
                'default': None,
            })
        return {
            'name': table_name,
            'type': 'record',
            'fields': fields,
        }

    def _parse_avro_schema(self, table_object: Table, table_name: str):
        """Build and parse an Avro schema, returning the parsed form."""
        schema = self._get_avro_schema(table_object, table_name)
        self.log.debug(f"Avro schema = {schema}")
        return fastavro.parse_schema(schema)

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
