import threading

import pytest

from bi_etl.bulk_loaders.bulk_worker import BulkWorker, BulkWorkerAborted


def _collect(rows):
    return list(rows)


def test_items_delivered_in_order_and_value_returned():
    worker = BulkWorker(_collect)
    worker.start()
    for i in range(50):
        worker.put(i)
    worker.close_input()
    worker.join()
    assert worker.done
    assert worker.exception is None
    assert worker.value == list(range(50))
    assert worker.input_closed
    assert len(worker) == 0


def test_target_runs_off_the_calling_thread():
    seen = []

    def target(rows):
        seen.append(threading.current_thread())
        return list(rows)

    worker = BulkWorker(target)
    worker.start()
    worker.close_input()
    worker.join()
    assert seen
    assert seen[0] is not threading.current_thread()


def test_target_exception_captured():
    def target(rows):
        raise KeyError('boom')

    worker = BulkWorker(target)
    worker.start()
    worker.join()
    assert worker.done
    assert isinstance(worker.exception, KeyError)
    assert worker.value is None


def test_target_returning_early_is_done_without_input_closed():
    worker = BulkWorker(lambda rows: 'early')
    worker.start()
    worker.join()
    assert worker.done
    assert worker.value == 'early'
    assert not worker.input_closed


def test_abort_raises_in_target_iterator():
    worker = BulkWorker(_collect)
    worker.start()
    worker.put(1)
    worker.abort()
    worker.join()
    assert isinstance(worker.exception, BulkWorkerAborted)


def test_not_done_until_input_closed():
    worker = BulkWorker(_collect)
    worker.start()
    worker.put(1)
    assert not worker.done
    worker.close_input()
    worker.join()
    assert worker.done


@pytest.mark.parametrize('chunk_size', [1, 2, 3, 10, 11, 1000])
def test_all_items_delivered_in_order_for_any_chunk_size(chunk_size):
    worker = BulkWorker(_collect, chunk_size=chunk_size)
    worker.start()
    for i in range(10):
        worker.put(i)
    worker.close_input()
    worker.join()
    assert worker.value == list(range(10))
    assert len(worker) == 0


@pytest.mark.parametrize('chunk_size', [0, -1])
def test_invalid_chunk_size_raises(chunk_size):
    with pytest.raises(ValueError, match='chunk_size'):
        BulkWorker(_collect, chunk_size=chunk_size)


def test_items_are_held_until_chunk_is_full():
    seen = []
    first_item = threading.Event()

    def target(rows):
        for row in rows:
            seen.append(row)
            first_item.set()
        return len(seen)

    worker = BulkWorker(target, chunk_size=3)
    worker.start()
    worker.put('a')
    worker.put('b')
    assert not first_item.wait(0.2)
    assert len(worker) == 2
    worker.put('c')
    assert first_item.wait(5)
    worker.close_input()
    worker.join()
    assert seen == ['a', 'b', 'c']


def test_abort_discards_unflushed_items():
    worker = BulkWorker(_collect, chunk_size=10)
    worker.start()
    worker.put(1)
    worker.abort()
    worker.join()
    assert isinstance(worker.exception, BulkWorkerAborted)
    assert worker.value is None
