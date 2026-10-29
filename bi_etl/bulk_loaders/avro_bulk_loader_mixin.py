# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import os.path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Callable, Iterable, Optional

import fastavro

from bi_etl.components.avro_writer import AvroWriter, build_avro_schema, default_avro_codec
from bi_etl.components.row.row import Row
from bi_etl.timer import Timer

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.etl_task import ETLTask


class AvroBulkLoaderMixin:
    """
    Mixin providing Avro schema generation, chunk writing, codec setup, and loading.

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

    # Benchmark shows that 250,000 is slightly faster but only for 1M+ row tables.
    # Smaller tables would then not benefit from any cross file parallel processing
    DEFAULT_ROWS_PER_FILE = 25_000

    def _init_avro(
            self,
            rows_per_file: int | None = None
    ):
        """
        Initialise Avro. Call from subclass ``__init__``.
        """
        self.rows_seen = 0
        if rows_per_file is not None:
            self.rows_per_file = rows_per_file
        else:
            self.rows_per_file = self.DEFAULT_ROWS_PER_FILE
        self.codec = default_avro_codec()
        self._translate_columns: dict[str, Callable] = {}

    # --- Schema helpers ------------------------------------------------------

    def _get_avro_schema(self, table_object: Table, table_name: str) -> dict:
        """Build an Avro record schema from *table_object*'s columns."""
        # Entries are specific to the table being loaded, so don't keep any from a previous load
        schema, self._translate_columns = build_avro_schema(table_object, table_name)
        return schema

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

    def _start_avro_chunk(
            self,
            temp_dir: str,
            file_number: int,
            parsed_schema,
            local_files_list: list,
    ) -> AvroWriter:
        """Open a writer for the numbered Avro file in *temp_dir* and add the file to *local_files_list*."""
        self.log.debug(f"Starting bulk load chunk {file_number}")
        filepath = os.path.join(temp_dir, f'data_{file_number}.avro')
        local_files_list.append(filepath)
        return AvroWriter(
            task=None,
            file_data=filepath,
            schema=parsed_schema,
            codec=self.codec,
            translate_columns=self._translate_columns,
        )

    def _finish_avro_chunk(self, writer: AvroWriter, file_number: int) -> int:
        """Close *writer*, then queue its file for upload. Returns the number of rows in the file."""
        writer.close()
        self.log.debug(f"Closed bulk load chunk {file_number}: {writer.file_path}")
        self._queue_file_for_upload(writer.file_path)
        return writer.rows_written

    # --- Load from iterable ---------------------------------------------------

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
        """Write rows from *iterable* to local Avro files and load them via :meth:`load_from_files`.

        Each file is queued for upload (see :meth:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader._queue_file_for_upload`)
        as soon as it is written, so :meth:`load_from_files` only has to wait for the uploads still in progress.

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
        ) as temp_dir, self._file_upload_session(table_object):
            parsed_schema = self._parse_avro_schema(table_object, table_to_load)

            file_number = 0
            data_length = 0
            local_files_list = []
            writer: AvroWriter | None = None

            progress_timer = Timer()
            row_number = -1
            try:
                for row_number, row in enumerate(iterable):
                    if writer is None:
                        file_number += 1
                        writer = self._start_avro_chunk(temp_dir, file_number, parsed_schema, local_files_list)
                    writer.insert_row(row)

                    if writer.rows_written >= self.rows_per_file:
                        data_length += self._finish_avro_chunk(writer, file_number)
                        writer = None

                    if progress_frequency is not None:
                        if 0 < progress_frequency < progress_timer.seconds_elapsed:
                            self.log.info(f"Wrote row {row_number:,}")
                            progress_timer.reset()

                # Write final chunk
                if writer is not None:
                    data_length += self._finish_avro_chunk(writer, file_number)
                    writer = None
            finally:
                if writer is not None:
                    writer.close(error=True)
            self.rows_seen = row_number + 1  # enumerate has 1st row as 0

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
