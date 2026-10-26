import logging
from pathlib import Path
from typing import *

import fastavro

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.scheduler.etl_task import ETLTask

__all__ = ['AvroReader']


class AvroReader(ETLComponent):
    """
    AvroReader reads Avro container files using :mod:`fastavro` and presents the records
    using the common bi_etl interface including :class:`~bi_etl.components.row.row.Row` objects.

    Requires the optional ``fastavro`` package (``pip install bi_etl[avro]``).

    Parameters
    ----------
    task:
        The instance to register in (if not None)

    filedata:
        The Avro file to read. If str or :class:`pathlib.Path` then it's assumed to be a filename.
        Otherwise it's assumed to be a binary file object (which is not closed by this component).

    reader_schema:
        Optional Avro schema (as a dict) to use to read the data.
        Used for schema evolution / projection. Default is None which uses the schema stored in the file.

    logical_name:
        The logical name of this source. Used for log messages.

    Attributes
    ----------
    column_names: list
        The names to use for columns. Defaults to the top level field names from the Avro schema.

    log_first_row : boolean
        Should we log progress on the first row read. *Only applies if used as a source.*
        (inherited from ETLComponent)

    max_rows : int, optional
        The maximum number of rows to read. *Only applies if Table is used as a source.*
        (inherited from ETLComponent)

    progress_message: str
        The progress message to print. Default is ``"{logical_name} row # {row_number}"``.
        Note ``logical_name`` and ``row_number`` subs.
        (inherited from ETLComponent)
    """

    def __init__(
        self,
        task: Optional[ETLTask],
        filedata: Union[str, Path, BinaryIO],
        reader_schema: Optional[dict] = None,
        logical_name: Optional[str] = None,
        **kwargs
    ):
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        self._close_file = False
        if isinstance(filedata, (str, Path)):
            self.log.debug(f"Opening file {filedata}")
            if logical_name is None:
                logical_name = Path(filedata).name
            self.file = open(filedata, mode='rb')
            self._close_file = True
        else:
            self.log.info(f"Treating input as file object {filedata}")
            self.file = filedata
            if logical_name is None:
                try:
                    logical_name = Path(self.file.name).name
                except (AttributeError, TypeError):
                    logical_name = str(self.file)

        # Don't pass kwargs up. They should be set here at the end
        super().__init__(
            task=task,
            logical_name=logical_name,
        )
        self.reader_schema = reader_schema
        self._avro_reader = None

        # Should be the last call of every init
        self.set_kwattrs(**kwargs)

    @property
    def avro_reader(self) -> fastavro.reader:
        """
        Build or get the :class:`fastavro.reader` object.
        """
        if self._avro_reader is None:
            self._avro_reader = fastavro.reader(self.file, reader_schema=self.reader_schema)
        return self._avro_reader

    def _obtain_column_names(self):
        """
        Set the column names from the top level fields of the Avro record schema.

        Raises
        ------
        ValueError
            If the schema being read is not an Avro record.
        """
        schema = self.avro_reader.reader_schema or self.avro_reader.writer_schema
        if not isinstance(schema, dict) or schema.get('type') != 'record':
            raise ValueError(f"{self.logical_name} Avro schema is not a record. Found {schema}")
        self._column_names = [field['name'] for field in schema['fields']]

    def _raw_rows(self):
        this_iteration_header = self.full_iteration_header
        for record in self.avro_reader:
            new_row = self.row_object(iteration_header=this_iteration_header)
            new_row.update_from_dict(record)
            yield new_row

    def close(self, error: bool = False):
        """
        Close the underlying file if it was opened by this component.

        Parameters
        ----------
        error:
            True if closing due to an error.
        """
        if self._close_file and not self.file.closed:
            self.file.close()
        super().close(error=error)
