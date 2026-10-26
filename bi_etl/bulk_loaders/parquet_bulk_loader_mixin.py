# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import os.path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Iterable, Optional

import pyarrow as pa

from bi_etl.components.parquet_writer import ParquetWriter, build_parquet_schema
from bi_etl.components.row.row import Row

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.etl_task import ETLTask


class ParquetBulkLoaderMixin:
    """Mixin providing Parquet schema generation, chunk writing, and loading.

    Subclasses must call :meth:`_init_parquet` from their ``__init__`` to set
    the number of rows per file.

    Each file is queued for upload (see
    :meth:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader._queue_file_for_upload`) as soon as it has been
    written, so :meth:`load_from_files` only has to wait for the uploads still in progress.

    .. note::

       :class:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader` also defines
       :meth:`load_from_iterable` (raising ``NotImplementedError``).  For
       this mixin's implementation to win the MRO, concrete Parquet loaders
       must list ``ParquetBulkLoaderMixin`` *before* :class:`BulkLoader` (or
       any base deriving from it) in their own bases.

       This mixin intentionally does **not** override
       :attr:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader.needs_all_columns`,
       since the correct value is loader-specific, not generic to Parquet.
    """

    PARQUET_COMPRESSION = 'SNAPPY'

    def _init_parquet(self, chunk_size: int = 25_000):
        """
        Initialise Parquet settings.  Call from subclass ``__init__``.

        Parameters
        ----------
        chunk_size
            Maximum number of rows in each Parquet file.
        """
        self.chunk_size = chunk_size

    # --- Schema helpers ------------------------------------------------------

    @staticmethod
    def _get_parquet_schema(table_object: Table) -> pa.Schema:
        """Build a :class:`pyarrow.Schema` from the columns of *table_object*.

        Parameters
        ----------
        table_object
            Table whose columns define the schema. Every field is nullable.

        Returns
        -------
        pyarrow.Schema
            Schema with one field per table column.
        """
        return build_parquet_schema(table_object)

    # --- Chunk writing -------------------------------------------------------

    def _start_parquet_chunk(
            self,
            temp_dir: str,
            file_number: int,
            schema: pa.Schema,
            local_files_list: list,
    ) -> ParquetWriter:
        """Open a writer for a numbered Parquet file and add the file to *local_files_list*.

        Parameters
        ----------
        temp_dir
            Directory the file is created in.
        file_number
            Number used in the file name.
        schema
            Schema of the file.
        local_files_list
            List that the path of the new file is appended to.
        """
        self.log.debug(f"Starting bulk load chunk {file_number}")
        # TODO: Redshift will recognize and uncompress these file types
        #   .gz
        #   .snappy
        #   .bz2
        filepath = os.path.join(temp_dir, f'data_{file_number}.parquet.snappy')
        local_files_list.append(filepath)
        return ParquetWriter(
            task=None,
            file_data=filepath,
            schema=schema,
            compression=self.PARQUET_COMPRESSION,
        )

    def _finish_parquet_chunk(self, writer: ParquetWriter, file_number: int) -> int:
        """Close *writer*, then queue its file for upload.

        Returns
        -------
        int
            Number of rows in the file.
        """
        writer.close()
        self.log.debug(f"Closed bulk load chunk {file_number}: {writer.file_path}")
        self._queue_file_for_upload(writer.file_path)
        return writer.rows_written

    # --- Load from iterable --------------------------------------------------

    def load_from_iterable(
            self,
            iterable: Iterable[Row],
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str | None = None,
            parent_task: Optional[ETLTask] = None,
    ) -> int:
        """Write rows from *iterable* to local Parquet files and load them via :meth:`load_from_files`.

        Parameters
        ----------
        iterable
            Source of :class:`~bi_etl.components.row.row.Row` objects to load.
        table_object
            Table the rows are being loaded into.
        table_to_load
            Name of the table (or temp table) to load into.  Defaults to
            ``table_object.qualified_table_name``.
        perform_rename
            Passed through to :meth:`load_from_files`.
        progress_frequency
            Not used by the Parquet loaders. Accepted for compatibility with the other loaders.
        analyze_compression
            Passed through to :meth:`load_from_files`.
        parent_task
            Not used by the Parquet loaders. Accepted for compatibility with the other loaders.

        Returns
        -------
        int
            Number of rows written.
        """
        table_to_load = table_to_load or table_object.qualified_table_name

        with TemporaryDirectory(
                dir=self.config.temp_file_path,
                ignore_cleanup_errors=True,
        ) as temp_dir, self._file_upload_session(table_object):
            schema = self._get_parquet_schema(table_object)
            self.log.debug(f"schema = {schema}")

            file_number = 0
            data_length = 0
            local_files_list = list()
            writer: ParquetWriter | None = None

            try:
                for row in iterable:
                    if writer is None:
                        file_number += 1
                        writer = self._start_parquet_chunk(temp_dir, file_number, schema, local_files_list)
                    writer.insert_row(row)

                    if writer.rows_written >= self.chunk_size:
                        data_length += self._finish_parquet_chunk(writer, file_number)
                        writer = None

                # Write final chunk
                if writer is not None:
                    data_length += self._finish_parquet_chunk(writer, file_number)
                    writer = None
            finally:
                if writer is not None:
                    writer.close(error=True)

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
                        f"COPY from files should have loaded {data_length:,} but it reports {rows_loaded:,} rows loaded"
                    )
            else:
                self.log.info(f"{self} had nothing to do with 0 rows found")
            return data_length