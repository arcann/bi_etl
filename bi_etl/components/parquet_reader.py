from pathlib import Path
from typing import *

import pyarrow
import pyarrow.dataset
import pyarrow.parquet

from bi_etl.components.pyarrow_dataset_reader import PyArrowDatasetReader
from bi_etl.scheduler.etl_task import ETLTask

__all__ = ['ParquetReader']


class ParquetReader(PyArrowDatasetReader):
    """
    ParquetReader reads Parquet files (a single file, a list of files, or a directory of files)
    using :class:`~bi_etl.components.pyarrow_dataset_reader.PyArrowDatasetReader` with the
    parquet specific options that are the most useful exposed directly.

    Parameters
    ----------
    task:
        The instance to register in (if not None)

    source:
        Path to a single file, path to a directory (discovered recursively), or a list of file paths.
        See :class:`~bi_etl.components.pyarrow_dataset_reader.PyArrowDatasetReader`.

    columns:
        Optional list of column names to read (projection). Only these columns are read from the files.
        Default is None which reads all columns.

    filters:
        Optional predicate used to skip row groups, files and rows that do not match.
        Either a :class:`pyarrow.dataset.Expression` (e.g. ``pyarrow.dataset.field('id') > 5``)
        or the list of tuples / list of lists of tuples (DNF) form accepted by
        :func:`pyarrow.parquet.read_table`, e.g. ``[('id', '>', 5), ('name', 'in', ['a', 'b'])]``.

    partitioning:
        How to interpret directory names as partition columns. Default is ``'hive'`` (``key=value`` directories).
        Use ``'directory'`` for plain value directories (requires a ``schema``), or None to disable.
        Can also be any value accepted by :func:`pyarrow.dataset.dataset`.

    schema:
        Optionally provide the :class:`pyarrow.Schema` for the dataset, in which case it will not be inferred.

    filesystem:
        Optional :class:`pyarrow.fs.FileSystem` (e.g. for S3) the source paths are on.

    batch_size:
        Maximum number of rows per record batch read from the files. Default is None, which uses the pyarrow default.

    use_threads:
        Should pyarrow read in parallel. Default is True.

    logical_name:
        The logical name of this source. Used for log messages.

    Attributes
    ----------
    column_names: list
        The names to use for columns. Reflects the ``columns`` projection when given.

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
        source: Union[str, Path, List[str], List[Path]],
        columns: Optional[Sequence[str]] = None,
        filters: Union[pyarrow.dataset.Expression, List[tuple], List[List[tuple]], None] = None,
        partitioning: Union[str, Any, None] = 'hive',
        schema: Optional[pyarrow.Schema] = None,
        filesystem: Optional[Any] = None,
        batch_size: Optional[int] = None,
        use_threads: bool = True,
        logical_name: Optional[str] = None,
        **kwargs
    ):
        if isinstance(columns, str):
            raise TypeError(f"columns must be a list of column names, not a single string: {columns!r}")
        if batch_size is not None and batch_size < 1:
            raise ValueError(f"batch_size must be a positive integer, not {batch_size}")

        # Don't pass kwargs up. They should be set here at the end
        super().__init__(
            task=task,
            source=source,
            schema=schema,
            pyarrow_format='parquet',
            logical_name=logical_name,
        )
        self.columns = None if columns is None else list(columns)
        self.filters = filters
        self.partitioning = partitioning
        self.filesystem = filesystem
        self.batch_size = batch_size
        self.use_threads = use_threads

        # Should be the last call of every init
        self.set_kwattrs(**kwargs)

    @property
    def filter_expression(self) -> Optional[pyarrow.dataset.Expression]:
        """
        The ``filters`` value as a :class:`pyarrow.dataset.Expression` (None if there are no filters).
        """
        if self.filters is None or isinstance(self.filters, pyarrow.dataset.Expression):
            return self.filters
        return pyarrow.parquet.filters_to_expression(self.filters)

    def _dataset_kwargs(self) -> Dict[str, Any]:
        """
        Add the ``partitioning`` and ``filesystem`` options (when set) to the dataset construction.

        Returns
        -------
        dict
        """
        kwargs = {}
        if self.partitioning is not None:
            kwargs['partitioning'] = self.partitioning
        if self.filesystem is not None:
            kwargs['filesystem'] = self.filesystem
        return kwargs

    def _scanner_kwargs(self) -> Dict[str, Any]:
        """
        Add the projection, filter, batch size and threading options to the scan.

        Returns
        -------
        dict
        """
        kwargs = {'use_threads': self.use_threads}
        if self.columns is not None:
            kwargs['columns'] = self.columns
        filter_expression = self.filter_expression
        if filter_expression is not None:
            kwargs['filter'] = filter_expression
        if self.batch_size is not None:
            kwargs['batch_size'] = self.batch_size
        return kwargs
