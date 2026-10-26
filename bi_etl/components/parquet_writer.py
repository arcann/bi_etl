import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import *

import pyarrow as pa
import pyarrow.parquet as pq

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.components.row.row import Row
from bi_etl.scheduler.etl_task import ETLTask
from bi_etl.statistics import Statistics

if TYPE_CHECKING:
    from bi_etl.components.table import Table

__all__ = ['ParquetWriter', 'build_parquet_schema']


_TYPE_MAP: Dict[type, pa.DataType] = {
    str: pa.string(),
    bytes: pa.large_binary(),
    date: pa.date32(),
    datetime: pa.timestamp('us'),
    time: pa.time64('us'),
    timedelta: pa.month_day_nano_interval(),
    bool: pa.bool_(),
    int: pa.int64(),
    float: pa.float64(),
}


def build_parquet_schema(table_object: 'Table') -> pa.Schema:
    """
    Build a :class:`pyarrow.Schema` from the columns of a table.

    Parameters
    ----------
    table_object:
        Table whose columns define the schema. Every field is nullable.

    Returns
    -------
    pyarrow.Schema
        Schema with one field per table column.
    """
    fields = []
    for column in table_object.columns:
        python_type = column.type.python_type
        if python_type == datetime and getattr(column.type, 'timezone', False):
            col_type = pa.timestamp('us', tz='UTC')
        elif python_type in _TYPE_MAP:
            col_type = _TYPE_MAP[python_type]
        elif python_type == Decimal:
            col_type = pa.decimal128(
                column.type.precision,
                column.type.scale,
            )
        else:
            col_type = pa.string()

        fields.append(pa.field(column.name, col_type, True))  # Nullable

    return pa.schema(fields)


class ParquetWriter(ETLComponent):
    """
    ParquetWriter writes rows to a Parquet file using :mod:`pyarrow`.
    It accepts :class:`~bi_etl.components.row.row.Row` objects like the other bi_etl writer components.

    Rows are buffered and written to the file as one row group each time ``row_group_size`` rows have
    been collected (and again at :meth:`commit` and :meth:`close`).

    Parameters
    ----------
    task:
        The instance to register in (if not None)

    file_data:
        The file to write. If str or :class:`pathlib.Path` then it's assumed to be a filename
        that will be created (or overwritten). Otherwise, it's assumed to be a binary file object.

    schema:
        The :class:`pyarrow.Schema` of the file.

    compression:
        The compression codec name, as accepted by :class:`pyarrow.parquet.ParquetWriter`.
        Default is ``'SNAPPY'``.

    row_group_size:
        The number of rows to buffer before writing a row group.

    logical_name:
        The logical name of this target. Used for log messages.

    Attributes
    ----------
    column_names: list
        The field names from the schema.

    rows_written: int
        The number of rows inserted so far (including rows still in the buffer).

    file_path: str, optional
        The path of the file being written, if known.
    """

    DEFAULT_COMPRESSION = 'SNAPPY'
    DEFAULT_ROW_GROUP_SIZE = 100_000

    def __init__(
        self,
        task: Optional[ETLTask],
        file_data: Union[str, Path, BinaryIO],
        schema: pa.Schema,
        compression: str = DEFAULT_COMPRESSION,
        row_group_size: int = DEFAULT_ROW_GROUP_SIZE,
        logical_name: Optional[str] = None,
        **kwargs
    ):
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        self.file_path: Optional[str] = None
        if isinstance(file_data, (str, Path)):
            self.file_path = str(file_data)
            file_data = self.file_path
            self.log.debug(f"Opening file {self.file_path} for writing")
        else:
            self.log.info(f"Treating input as file object {file_data}")
            try:
                self.file_path = str(file_data.name)
            except (AttributeError, TypeError):
                pass

        if logical_name is None:
            logical_name = Path(self.file_path).name if self.file_path else str(file_data)

        # Don't pass kwargs up. They should be set here at the end
        super().__init__(
            task=task,
            logical_name=logical_name,
        )
        self.schema = schema
        self.compression = compression
        self.row_group_size = row_group_size
        self.column_names = list(schema.names)
        self.rows_written = 0
        self.trace_data = False
        self._buffer: List[Any] = []
        self._writer = pq.ParquetWriter(file_data, schema, compression=compression)

        # Should be the last call of every init
        self.set_kwattrs(**kwargs)

    @classmethod
    def from_table(
        cls,
        task: Optional[ETLTask],
        file_data: Union[str, Path, BinaryIO],
        table_object: 'Table',
        **kwargs
    ) -> 'ParquetWriter':
        """
        Build a ParquetWriter with a schema generated from the columns of a table.

        Parameters
        ----------
        task:
            The instance to register in (if not None)
        file_data:
            The file to write. See :class:`ParquetWriter`.
        table_object:
            The table to build the schema from. See :func:`build_parquet_schema`.
        kwargs:
            Additional arguments passed to :class:`ParquetWriter`.

        Returns
        -------
        ParquetWriter
        """
        return cls(task, file_data, build_parquet_schema(table_object), **kwargs)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(task={self.task},"
            f"logical_name={self.logical_name},"
            f"file_path={self.file_path},"
            f"column_names={self.column_names})"
        )

    def _write_buffer(self):
        if self._buffer:
            table = pa.Table.from_pylist(self._buffer, schema=self.schema)
            self._buffer = []
            self._writer.write_table(table)

    def insert_row(
        self,
        source_row: Row,
        additional_insert_values: Optional[dict] = None,
        stat_name: str = 'insert',
        parent_stats: Optional[Statistics] = None,
    ) -> Row:
        """
        Inserts a row into the target file.

        Parameters
        ----------
        source_row:
            The row with values to insert. Columns not in the schema are ignored and
            columns missing from the row are written as null.
        additional_insert_values:
            Values to add / override in the row before inserting.
        stat_name:
            Name of this step for the ETLTask statistics.
        parent_stats:
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.

        Returns
        -------
        source_row
        """
        stats = self.get_stats_entry(stat_name, parent_stats=parent_stats)

        if additional_insert_values:
            record = dict(source_row.items())
            record.update(additional_insert_values)
        else:
            record = source_row

        if self.trace_data:
            self.log.debug(f"{self} Raw row being inserted:\n{source_row}")

        self._buffer.append(record)
        self.rows_written += 1
        stats.add_to_stat('inserts', 1)
        if len(self._buffer) >= self.row_group_size:
            self._write_buffer()
        return source_row

    def insert(
        self,
        source: Union[Row, list],
        additional_insert_values: Optional[dict] = None,
        parent_stats: Optional[Statistics] = None,
        **kwargs
    ):
        """
        Insert a row or list of rows in the file.

        Parameters
        ----------
        source:
            :class:`~bi_etl.components.row.row.Row` or list thereof to insert
        additional_insert_values:
            Additional values to set on each row.
        parent_stats:
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.
        """
        if isinstance(source, list):
            for row in source:
                self.insert_row(
                    row,
                    additional_insert_values=additional_insert_values,
                    parent_stats=parent_stats,
                    **kwargs
                )
            return None
        else:
            return self.insert_row(
                source,
                additional_insert_values=additional_insert_values,
                parent_stats=parent_stats,
                **kwargs
            )

    def commit(self):
        """
        Write any buffered rows to the file as a row group.
        """
        self._write_buffer()

    def close(self, error: bool = False):
        """
        Write any buffered rows and close the file.

        Parameters
        ----------
        error:
            True if closing due to an error. Buffered rows are discarded.
        """
        if not self.is_closed:
            try:
                if not error:
                    self._write_buffer()
            finally:
                self._writer.close()
                super().close(error=error)
