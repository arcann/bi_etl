from functools import cached_property
from pathlib import Path
from typing import *

import pyarrow
import pyarrow.dataset
from pyarrow.dataset import Dataset, Scanner

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.components.row.row import Row
from bi_etl.scheduler.etl_task import ETLTask
from bi_etl.statistics import Statistics

__all__ = ['PyArrowDatasetReader']


class PyArrowDatasetReader(ETLComponent):
    """
    PyArrowDatasetReader will read rows using pyarrow.dataset functionality but presented
    using the common bi_etl interface including Row objects.

    Currently, parquet, ipc/arrow/feather, csv, and orc are supported by pyarrow.dataset.

      * A unified interface that supports different sources and file formats and different file systems (local, cloud).
      * Discovery of sources (crawling directories, handle directory-based partitioned datasets, basic schema normalization, ..)
      * Optimized reading with predicate pushdown (filtering rows), projection (selecting and deriving columns), and optionally parallel reading.

    Parameters
    ----------
    task:
        The  instance to register in (if not None)

    source:
        Path pointing to a single file: Open a FileSystemDataset from a single file.

        Path pointing to a directory: The directory gets discovered recursively according to a partitioning scheme if given.

        List of file paths: Create a FileSystemDataset from explicitly given files. The files must be located on the same filesystem given by the filesystem parameter. Note that in contrary of construction from a single file, passing URIs as paths is not allowed.

    schema:
        Optionally provide the Schema for the Dataset, in which case it will not be inferred from the source.

    format:
        Currently "parquet", "ipc" / "arrow" / "feather", "csv", and "orc" are supported.
        For Feather, only version 2 files are supported.

    logical_name:
        The logical name of this source. Used for log messages.

    Attributes
    ----------
    column_names: list
        The names to use for columns

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
        schema: pyarrow.Schema | None = None,
        pyarrow_format: str | None = None,
        logical_name: Optional[str] = None,
        **kwargs
    ):
        # Don't pass kwargs up. They should be set here at the end
        super().__init__(
            task=task,
            logical_name=logical_name,
        )
        self.source = source
        self.schema = schema
        self.pyarrow_format = pyarrow_format

        # Should be the last call of every init
        self.set_kwattrs(**kwargs)

    def _dataset_kwargs(self) -> Dict[str, Any]:
        """
        Extra keyword arguments for :func:`pyarrow.dataset.dataset`.

        Subclasses override this to expose format specific options such as ``partitioning``
        or ``filesystem``.

        Returns
        -------
        dict
            Keyword arguments added to the dataset construction call.
        """
        return {}

    def _scanner_kwargs(self) -> Dict[str, Any]:
        """
        Extra keyword arguments for :meth:`pyarrow.dataset.Dataset.scanner`.

        Subclasses override this to expose projection (``columns``), predicate pushdown (``filter``),
        ``batch_size`` and similar options.

        Returns
        -------
        dict
            Keyword arguments added to the scanner construction call.
        """
        return {}

    @cached_property
    def _dataset(self) -> Dataset:
        return pyarrow.dataset.dataset(
            source=self.source,
            schema=self.schema,
            format=self.pyarrow_format,
            **self._dataset_kwargs(),
        )

    def _scanner(self, extra_filter: Optional[pyarrow.dataset.Expression] = None) -> Scanner:
        """
        Build the scanner used to read the dataset.

        Parameters
        ----------
        extra_filter:
            Optional filter expression combined (AND) with any filter from :meth:`_scanner_kwargs`.

        Returns
        -------
        pyarrow.dataset.Scanner
        """
        kwargs = self._scanner_kwargs()
        if extra_filter is not None:
            existing_filter = kwargs.get('filter')
            kwargs['filter'] = extra_filter if existing_filter is None else existing_filter & extra_filter
        return self._dataset.scanner(**kwargs)

    def _obtain_column_names(self):
        # The projected schema reflects any column selection from the scanner options
        self._column_names = [field.name for field in self._scanner().projected_schema]

    @staticmethod
    def _criteria_dict_to_expression(criteria_dict: dict) -> pyarrow.dataset.Expression:
        """
        Convert a ``criteria_dict`` (column to value) into a pyarrow filter expression.

        Parameters
        ----------
        criteria_dict:
            Keys are column names. A ``None`` value matches nulls, a list, tuple or set matches any member,
            and any other value matches by equality.

        Returns
        -------
        pyarrow.dataset.Expression
            All the conditions combined with AND.
        """
        expression = None
        for column, value in criteria_dict.items():
            field = pyarrow.dataset.field(column)
            if value is None:
                condition = field.is_null()
            elif isinstance(value, (list, tuple, set, frozenset)):
                condition = field.isin(list(value))
            else:
                condition = field == value
            expression = condition if expression is None else expression & condition
        return expression

    @staticmethod
    def _batch_to_value_lists(batch: pyarrow.RecordBatch) -> Iterator[list]:
        """
        Convert a record batch to one list of Python values per row, in the batch's column order.

        This is faster than :meth:`pyarrow.RecordBatch.to_pylist` since it does not build a ``dict`` per row.
        The columns are converted individually (instead of with ``to_pydict``) so that
        duplicate column names are not collapsed.

        Parameters
        ----------
        batch:
            The record batch to convert.

        Yields
        ------
        list
            The values of one row.
        """
        if batch.num_columns == 0:
            for _ in range(batch.num_rows):
                yield []
            return
        for values in zip(*[column.to_pylist() for column in batch.columns]):
            yield list(values)

    def _raw_rows(self, extra_filter: Optional[pyarrow.dataset.Expression] = None):
        this_iteration_header = self.full_iteration_header
        for batch in self._scanner(extra_filter).to_batches():
            for values in self._batch_to_value_lists(batch):
                new_row = self.row_object(iteration_header=this_iteration_header)
                new_row.update_from_values(values)
                yield new_row

    def where(
            self,
            criteria_list: Optional[list] = None,
            criteria_dict: Optional[dict] = None,
            order_by: Optional[list] = None,
            column_list: Optional[list] = None,
            exclude_cols: Optional[FrozenSet] = None,
            use_cache_as_source: Optional[bool] = None,
            progress_frequency: Optional[int] = None,
            stats_id: Optional[str] = None,
            parent_stats: Optional[Statistics] = None,
    ) -> Iterable[Row]:
        """
        Iterate over the rows matching ``criteria_dict``. The criteria are pushed down into the
        pyarrow scan so that non-matching data (and for parquet, row groups) can be skipped.

        Parameters
        ----------
        criteria_list:
            Not supported.
        criteria_dict:
            Dict keys should be columns, values are matched using ``=``, ``in`` (list, tuple, set) or
            ``is null`` (None).
        order_by:
            Not supported.
        column_list:
            Not supported.
        exclude_cols:
            Not supported.
        use_cache_as_source:
            Not supported.
        progress_frequency:
            See :meth:`~bi_etl.components.etlcomponent.ETLComponent.iter_result`.
        stats_id:
            See :meth:`~bi_etl.components.etlcomponent.ETLComponent.iter_result`.
        parent_stats:
            See :meth:`~bi_etl.components.etlcomponent.ETLComponent.iter_result`.

        Returns
        -------
        rows
        """
        assert order_by is None, f'{self} does not support order_by'
        assert criteria_list is None, f'{self} does not support criteria_list'
        extra_filter = None
        if criteria_dict:
            extra_filter = self._criteria_dict_to_expression(criteria_dict)
        return self.iter_result(
            self._raw_rows(extra_filter),
            progress_frequency=progress_frequency,
            stats_id=stats_id,
            parent_stats=parent_stats,
        )

