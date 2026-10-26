"""
Background upload of bulk load files while the loader is still writing the next ones.

Writing a file (CSV/Avro/JSON serialization and compression) and uploading it are independent,
so a :class:`FileUploader` lets the upload of one finished file overlap with the writing of the next.
"""
import threading
from pathlib import Path
from typing import Callable, List, Union

from bi_etl.bulk_loaders.bulk_worker import BulkWorker


class FileUploader:
    """
    Uploads files on a background thread, in the order they are passed to :meth:`submit`.

    :meth:`submit`, :meth:`finish` and :meth:`abort` are intended to be called from a single producer thread.
    The upload function is only ever called from the background thread, one file at a time.

    Parameters
    ----------
    upload_function:
        Blocking callable that uploads one local file. It is passed the path as a ``str``.
    name:
        Name for the background thread.
    """

    def __init__(
            self,
            upload_function: Callable[[str], None],
            name: str = 'file_uploader',
    ):
        """Create the uploader and start its background thread."""
        self._upload_function = upload_function
        self._cancelled = threading.Event()
        self._uploaded: List[str] = []
        # chunk_size=1 so that every file is handed to the upload thread as soon as it is submitted
        self._worker = BulkWorker(self._upload_all, name=name, chunk_size=1)
        self._worker.start()

    def _upload_all(self, local_files) -> None:
        """
        Upload each file from *local_files* on the background thread, recording the ones that completed.

        Stops early if :meth:`abort` was called.
        """
        for local_file in local_files:
            if self._cancelled.is_set():
                break
            self._upload_function(local_file)
            self._uploaded.append(local_file)

    def _raise_if_failed(self) -> None:
        """Raise the exception that ended the upload thread, if it has failed."""
        if self._worker.done and self._worker.exception is not None:
            raise self._worker.exception

    def submit(self, local_file: Union[str, Path]) -> None:
        """
        Queue a completed file for upload. Never blocks on the upload itself.

        Parameters
        ----------
        local_file:
            Path of a file that is completely written and closed.

        Raises
        ------
        Exception
            The exception from an earlier failed upload, so that the producer
            stops writing files that can no longer be loaded.
        """
        self._raise_if_failed()
        self._worker.put(str(local_file))

    def finish(self) -> List[str]:
        """
        Wait for all queued uploads to complete.

        Returns
        -------
        list of str
            The paths that were uploaded, in upload order.

        Raises
        ------
        Exception
            The exception from the first failed upload.
        """
        self._worker.close_input()
        self._worker.join()
        if self._worker.exception is not None:
            raise self._worker.exception
        return list(self._uploaded)

    def abort(self) -> None:
        """
        Stop uploading and wait for the upload thread to exit.

        Files still in the queue are not uploaded. An upload that is already in progress is allowed to finish.
        Does not raise upload errors, so it is safe to call while another exception is propagating.
        """
        self._cancelled.set()
        self._worker.abort()
        self._worker.join()