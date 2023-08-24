from functools import cached_property
from pathlib import Path
from typing import *

import pyarrow
from pyarrow.dataset import Dataset

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.scheduler.task import ETLTask

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
        
    primary_key: list
        The name of the primary key column(s). Only impacts trace messages.  Default=None.
        (inherited from ETLComponent)
    
    progress_frequency: int
        How often (in seconds) to output progress messages. None for no progress messages.
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
        schema: pyarrow.Schema = None,
        pyarrow_format: str = None,
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
        self._pyarrow_dataset = None

        # Should be the last call of every init
        self.set_kwattrs(**kwargs)

    @cached_property
    def _dataset(self) -> Dataset:
        return pyarrow.dataset.dataset(
            source=self.source,
            schema=self.schema,
            format=self.pyarrow_format,
        )

    def _obtain_column_names(self):
        self._column_names = [field.name for field in self._dataset.schema]

    def _raw_rows(self):
        this_iteration_header = self.full_iteration_header
        for batch in self._dataset.to_batches():
            for raw_row in batch.to_pylist():
                new_row = self.row_object(iteration_header=this_iteration_header)
                new_row.update_from_dict(raw_row)
                yield new_row


if __name__ == '__main__':
    with PyArrowDatasetReader(
        None,
        r'C:\temp_data\data_access_api\n5yK2zeTV6CoYui7fP9bI',
        logical_name='test_arrow',
    ) as test:
        print(f"Columns={test.column_names}")
        for n, row in enumerate(test):
            if n <= 10:
                print(row.as_dict)
        print(f"Read {n} rows")
