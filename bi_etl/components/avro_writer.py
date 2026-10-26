import logging
from dataclasses import dataclass
from datetime import date, datetime, time as time_type, timedelta
from decimal import Decimal
from pathlib import Path
from typing import *

import fastavro
import fastavro.write

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.components.row.row import Row
from bi_etl.scheduler.etl_task import ETLTask
from bi_etl.statistics import Statistics
from bi_etl.utility.json import json_dumps

if TYPE_CHECKING:
    from bi_etl.components.table import Table

__all__ = ['AvroWriter', 'build_avro_schema', 'default_avro_codec']


def default_avro_codec() -> str:
    """
    Get the best compression codec available.

    Returns
    -------
    str
        ``'snappy'`` if :mod:`snappy` is installed, otherwise ``'deflate'``.
    """
    try:
        import snappy  # noqa: F401
        return 'snappy'
    except ImportError:
        return 'deflate'


@dataclass
class _TypeDefn:
    """Avro type definition for a Python type, with an optional function to convert values to that type."""
    type_list: List[Union[str, dict]]
    conversion_function: Optional[Callable] = None


_TYPE_MAP: Dict[type, _TypeDefn] = {
    str: _TypeDefn(type_list=['string']),
    bytes: _TypeDefn(type_list=['bytes']),
    date: _TypeDefn(type_list=[{"type": "int", "logicalType": "date"}]),
    datetime: _TypeDefn(type_list=[{"type": "long", "logicalType": "timestamp-millis"}]),
    time_type: _TypeDefn(type_list=[{"type": "long", "logicalType": "time-millis"}]),
    # total_seconds() returns a float, which an Avro long would reject
    timedelta: _TypeDefn(type_list=['double'], conversion_function=timedelta.total_seconds),
    bool: _TypeDefn(type_list=['boolean']),
    int: _TypeDefn(type_list=['long']),
    float: _TypeDefn(type_list=['double']),
    # Note: Decimal has special handling in build_avro_schema. This is placed here as a potential default
    Decimal: _TypeDefn(
        type_list=[{"type": "bytes", "logicalType": "decimal", "precision": 38, "scale": 10}],
        conversion_function=float,
    ),
    object: _TypeDefn(type_list=['string'], conversion_function=json_dumps),
    dict: _TypeDefn(type_list=['string'], conversion_function=json_dumps),
    list: _TypeDefn(type_list=['string'], conversion_function=json_dumps),
    set: _TypeDefn(type_list=['string'], conversion_function=json_dumps),
}


def build_avro_schema(table_object: 'Table', schema_name: str) -> Tuple[dict, Dict[str, Callable]]:
    """
    Build an Avro record schema from the columns of a table.

    Every field is nullable.

    Parameters
    ----------
    table_object:
        The table to build the schema from.
    schema_name:
        The name of the Avro record.

    Returns
    -------
    schema:
        The Avro record schema.
    translate_columns:
        Functions, by column name, that convert Python values to values that the schema accepts.
    """
    translate_columns: Dict[str, Callable] = {}
    fields = []
    for column in table_object.columns:
        python_type = table_object._get_python_type(column.type)
        if python_type == Decimal:
            col_type_defn = _TypeDefn(
                type_list=[
                    {
                        "type": "bytes",
                        "logicalType": "decimal",
                        "precision": column.type.precision,
                        "scale": column.type.scale
                    }
                ],
            )
        else:
            col_type_defn = _TYPE_MAP.get(python_type, _TypeDefn(['string'], conversion_function=str))
            if col_type_defn.conversion_function is not None:
                translate_columns[column.name] = col_type_defn.conversion_function
        fields.append(
            {
                'name': column.name,
                'type': ['null', *col_type_defn.type_list],
                'default': None,
            }
        )
    schema = {
        'name': schema_name,
        'type': 'record',
        'fields': fields,
    }
    return schema, translate_columns


class AvroWriter(ETLComponent):
    """
    AvroWriter writes rows to an Avro container file using :mod:`fastavro`.
    It accepts :class:`~bi_etl.components.row.row.Row` objects like the other bi_etl writer components.

    Requires the optional ``fastavro`` package (``pip install bi_etl[avro]``).

    Parameters
    ----------
    task:
        The instance to register in (if not None)

    file_data:
        The file to write. If str or :class:`pathlib.Path` then it's assumed to be a filename
        that will be created (or overwritten). Otherwise, it's assumed to be a binary file object
        (which is not closed by this component).

    schema:
        The Avro record schema, as a dict. Parsed or unparsed schemas are accepted.

    codec:
        The compression codec. Default is :func:`default_avro_codec`.

    translate_columns:
        Functions, by column name, used to convert values before they are written.
        ``None`` values are never translated. See :func:`build_avro_schema`.

    logical_name:
        The logical name of this target. Used for log messages.

    Attributes
    ----------
    column_names: list
        The top level field names from the Avro schema.

    rows_written: int
        The number of rows written so far.

    file_path: str, optional
        The path of the file being written, if known.
    """

    def __init__(
        self,
        task: Optional[ETLTask],
        file_data: Union[str, Path, BinaryIO],
        schema: dict,
        codec: Optional[str] = None,
        translate_columns: Optional[Dict[str, Callable]] = None,
        logical_name: Optional[str] = None,
        **kwargs
    ):
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        self._close_file = False
        self.file_path: Optional[str] = None
        if isinstance(file_data, (str, Path)):
            self.log.debug(f"Opening file {file_data} for writing")
            self.file_path = str(file_data)
            self.file = open(file_data, mode='wb')
            self._close_file = True
        else:
            self.log.info(f"Treating input as file object {file_data}")
            self.file = file_data
            try:
                self.file_path = str(file_data.name)
            except (AttributeError, TypeError):
                pass

        if logical_name is None:
            logical_name = Path(self.file_path).name if self.file_path else str(self.file)

        # Don't pass kwargs up. They should be set here at the end
        super().__init__(
            task=task,
            logical_name=logical_name,
        )
        self.codec = codec or default_avro_codec()
        self.translate_columns: Dict[str, Callable] = translate_columns or {}
        self.rows_written = 0
        self.trace_data = False

        try:
            self.parsed_schema = fastavro.parse_schema(schema)
            self.column_names = [field['name'] for field in self.parsed_schema['fields']]
            self._writer = fastavro.write.Writer(self.file, self.parsed_schema, codec=self.codec)
        except Exception:
            self.log.error(f"Avro schema that errored = {schema}")
            self._close_owned_file()
            raise

        # Should be the last call of every init
        self.set_kwattrs(**kwargs)

    @classmethod
    def from_table(
        cls,
        task: Optional[ETLTask],
        file_data: Union[str, Path, BinaryIO],
        table_object: 'Table',
        schema_name: Optional[str] = None,
        **kwargs
    ) -> 'AvroWriter':
        """
        Build an AvroWriter with a schema generated from the columns of a table.

        Parameters
        ----------
        task:
            The instance to register in (if not None)
        file_data:
            The file to write. See :class:`AvroWriter`.
        table_object:
            The table to build the schema from. See :func:`build_avro_schema`.
        schema_name:
            The name of the Avro record. Default is ``table_object.qualified_table_name``.
        kwargs:
            Additional arguments passed to :class:`AvroWriter`.

        Returns
        -------
        AvroWriter
        """
        schema, translate_columns = build_avro_schema(
            table_object,
            schema_name or table_object.qualified_table_name,
        )
        return cls(task, file_data, schema, translate_columns=translate_columns, **kwargs)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(task={self.task},"
            f"logical_name={self.logical_name},"
            f"file={self.file},"
            f"column_names={self.column_names})"
        )

    def write_record(self, record: dict):
        """
        Write a dict directly to the file with no value translation.

        Parameters
        ----------
        record:
            Values by column name. Missing nullable columns are written as null.
        """
        self._writer.write(record)
        self.rows_written += 1

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
            The row with values to insert
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

        record = source_row.as_dict
        if additional_insert_values:
            record.update(additional_insert_values)

        for column_name, translate_function in self.translate_columns.items():
            # None is a NULL, which the schema allows for every column. It must not be translated.
            if record.get(column_name) is not None:
                record[column_name] = translate_function(record[column_name])

        if self.trace_data:
            self.log.debug(f"{self} Raw row being inserted:\n{source_row.str_formatted()}")

        self.write_record(record)
        stats.add_to_stat('inserts', 1)
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
        Write any buffered rows to the file.
        """
        self._writer.flush()

    def _close_owned_file(self):
        if self._close_file and not self.file.closed:
            self.file.close()

    def close(self, error: bool = False):
        """
        Write any buffered rows and close the file if it was opened by this component.

        Parameters
        ----------
        error:
            True if closing due to an error.
        """
        if not self.is_closed:
            if not self.file.closed:
                self._writer.flush()
            self._close_owned_file()
            super().close(error=error)
