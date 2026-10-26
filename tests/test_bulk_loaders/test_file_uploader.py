import threading
import time

import pytest

from bi_etl.bulk_loaders.file_uploader import FileUploader


class UploadError(Exception):
    pass


def test_files_uploaded_in_order_off_the_calling_thread():
    threads = []
    uploaded = []

    def upload(path):
        threads.append(threading.current_thread())
        uploaded.append(path)

    uploader = FileUploader(upload)
    for name in ['a', 'b', 'c']:
        uploader.submit(name)
    assert uploader.finish() == ['a', 'b', 'c']
    assert uploaded == ['a', 'b', 'c']
    assert all(t is not threading.current_thread() for t in threads)


def test_path_objects_are_passed_to_upload_as_str(tmp_path):
    seen = []
    uploader = FileUploader(seen.append)
    uploader.submit(tmp_path / 'data.avro')
    assert uploader.finish() == [str(tmp_path / 'data.avro')]
    assert seen == [str(tmp_path / 'data.avro')]


def test_finish_with_nothing_submitted():
    uploader = FileUploader(lambda path: None)
    assert uploader.finish() == []


def test_submit_does_not_wait_for_the_upload():
    started = threading.Event()
    release = threading.Event()

    def upload(path):
        started.set()
        assert release.wait(5)

    uploader = FileUploader(upload)
    uploader.submit('a')
    assert started.wait(5)
    # The upload of 'a' is still blocked, but more files can be queued
    uploader.submit('b')
    uploader.submit('c')
    release.set()
    assert uploader.finish() == ['a', 'b', 'c']


def test_failure_raised_by_finish():
    def upload(path):
        raise UploadError(path)

    uploader = FileUploader(upload)
    uploader.submit('a')
    with pytest.raises(UploadError, match='a'):
        uploader.finish()


def test_failure_raised_by_later_submit():
    failed = threading.Event()

    def upload(path):
        failed.set()
        raise UploadError(path)

    uploader = FileUploader(upload)
    uploader.submit('a')
    assert failed.wait(5)
    with pytest.raises(UploadError):
        # The failure is recorded just after upload returns, so allow for that
        for _ in range(500):
            uploader.submit('b')
            time.sleep(0.01)
    uploader.abort()


def test_no_uploads_after_a_failure():
    uploaded = []

    def upload(path):
        if path == 'b':
            raise UploadError(path)
        uploaded.append(path)

    uploader = FileUploader(upload)
    for name in ['a', 'b', 'c']:
        uploader.submit(name)
    with pytest.raises(UploadError):
        uploader.finish()
    assert uploaded == ['a']


def test_abort_skips_queued_files_and_waits_for_the_upload_in_progress():
    started = threading.Event()
    release = threading.Event()
    uploaded = []

    def upload(path):
        started.set()
        assert release.wait(5)
        uploaded.append(path)

    uploader = FileUploader(upload)
    for name in ['a', 'b', 'c']:
        uploader.submit(name)
    assert started.wait(5)
    timer = threading.Timer(0.1, release.set)
    timer.start()
    uploader.abort()
    timer.join()
    assert uploaded == ['a']


def test_abort_with_nothing_queued_stops_the_thread():
    uploader = FileUploader(lambda path: None, name='abort_idle_uploader')
    uploader.abort()
    assert not any(t.name == 'abort_idle_uploader' for t in threading.enumerate())


def test_abort_does_not_raise_upload_failure():
    def upload(path):
        raise UploadError(path)

    uploader = FileUploader(upload)
    uploader.submit('a')
    uploader.abort()