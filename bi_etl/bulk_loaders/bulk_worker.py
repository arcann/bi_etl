"""
Background worker that runs a blocking bulk loader while the caller keeps feeding it rows.

:class:`bi_etl.components.table.Table.insert_row` is synchronous. It hands rows to a :class:`BulkWorker`,
which runs :meth:`bi_etl.bulk_loaders.bulk_loader.BulkLoader.load_from_iterable` on a background thread.
Because the work is on its own thread, it behaves the same
whether the caller is plain synchronous code or code running inside an asyncio event loop.

Rows are handed to the background thread in chunks rather than one at a time.
The cost of a thread-safe queue operation is far larger than the cost of a list append,
so buffering ``chunk_size`` rows per queue operation removes most of the per-row hand-off overhead.
"""
import queue
import threading
import time
from typing import Any, Callable, Iterable, Iterator, List, Optional


class BulkWorkerAborted(Exception):
    """Raised inside the worker's row iterator when the worker is aborted before the input is complete."""


_END_OF_INPUT = object()
_ABORT = object()


class BulkWorker:
    """
    Runs ``target(rows)`` on a background thread, where ``rows`` is an iterator over the items passed to :meth:`put`.

    :meth:`put`, :meth:`close_input`, :meth:`abort` and :meth:`join` are intended to be called from a single
    producer thread.

    Parameters
    ----------
    target_function:
        Blocking callable that consumes the iterator and returns a result (e.g. the row count).
    name:
        Name for the background thread.
    chunk_size:
        Number of items buffered by :meth:`put` before they are handed to the background thread.
        Items are also handed over by :meth:`close_input`. A larger value lowers the per-item overhead
        but delays when the target first sees the items (and so when a failure in the target is noticed).
        Use 1 to hand over every item immediately.
    """
    DEFAULT_CHUNK_SIZE = 128
    GIL_SLEEP_TIME = 0

    def __init__(
            self,
            target_function: Callable[[Iterable], Any],
            name: str = 'bulk_worker',
            chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        """
        Create the worker. The background thread is not started until :meth:`start` is called.

        Raises
        ------
        ValueError
            If *chunk_size* is less than 1.
        """
        if chunk_size < 1:
            raise ValueError(f"chunk_size must be at least 1, not {chunk_size}")
        self._target_function = target_function
        self._chunk_size = chunk_size
        self._buffer: List[Any] = []
        self._queue = queue.SimpleQueue()
        self._put_count = 0
        self._consumed_count = 0
        self._done = threading.Event()
        self._input_closed = False
        self._exception: Optional[BaseException] = None
        self._value: Any = None
        self._thread = threading.Thread(target=self._thread_main, name=name, daemon=True)

    def start(self) -> None:
        """Start the background thread."""
        self._thread.start()

    def put(self, item: Any) -> None:
        """
        Add an item for the target. Never blocks.

        Parameters
        ----------
        item:
            The item to deliver to the target's iterator.
        """
        self._buffer.append(item)
        self._put_count += 1
        if len(self._buffer) >= self._chunk_size:
            self._flush()

    def _flush(self) -> None:
        """Hand the buffered items, if any, to the background thread as one chunk."""
        if self._buffer:
            chunk = self._buffer
            self._buffer = []
            self._queue.put(chunk)
            # Release GIL for long enough for queue get to proceed and start the IO
            time.sleep(self.GIL_SLEEP_TIME)

    def close_input(self) -> None:
        """Signal that no more items will be added. The target's iterator ends after the queued items."""
        self._flush()
        self._input_closed = True
        self._queue.put(_END_OF_INPUT)

    def abort(self) -> None:
        """
        Make the target's iterator raise :class:`BulkWorkerAborted` once it reaches this point in the queue.

        Used when the load is abandoned so that the target does not mistake the truncated input for a complete one.
        Items that have not yet been handed to the background thread are discarded.
        """
        self._buffer = []
        self._queue.put(_ABORT)

    def __len__(self) -> int:
        """Approximate number of items added but not yet taken by the target."""
        return self._put_count - self._consumed_count

    @property
    def input_closed(self) -> bool:
        """True once :meth:`close_input` has been called."""
        return self._input_closed

    @property
    def done(self) -> bool:
        """True once the target has returned or raised."""
        return self._done.is_set()

    @property
    def exception(self) -> Optional[BaseException]:
        """The exception raised by the target, if any. Only meaningful once :attr:`done` is True."""
        return self._exception

    @property
    def value(self) -> Any:
        """The value returned by the target. Only meaningful once :attr:`done` is True."""
        return self._value

    def join(self) -> None:
        """Block until the target has finished."""
        self._done.wait()
        self._thread.join()

    def _iterate(self) -> Iterator[Any]:
        """
        Iterate over the items passed to :meth:`put`, on the background thread. This is what the target consumes.

        Raises
        ------
        BulkWorkerAborted
            If :meth:`abort` was called before :meth:`close_input`.
        """
        while True:
            chunk = self._queue.get()
            if chunk is _END_OF_INPUT:
                return
            if chunk is _ABORT:
                raise BulkWorkerAborted("Bulk load aborted before all rows were provided")
            self._consumed_count += len(chunk)
            yield from chunk

    def _thread_main(self) -> None:
        """Run the target on the background thread, saving its value or exception and then setting :attr:`done`."""
        try:
            self._value = self._target_function(self._iterate())
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Re-raised to the caller by Table, from the thread that is calling insert_row
            self._exception = e
        finally:
            self._done.set()
