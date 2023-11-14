import multiprocessing
import time


class NotifierRetry(NotifierBase):
    def __init__(self, config_section: notifiers_config.JiraNotifier):
        super().__init__()

        self._retry_process = None
        self._to_retry_queue = None
        self._from_retry_queue = None
        self._retry_time_limit_mins = 30

    def _retry_processor(
            self,
            to_retry_queue: multiprocessing.Queue,
            from_retry_queue: multiprocessing.Queue,
    ):
        pending_notfications = list()
        last_msg = datetime.now()
        while True:
            try:
                msg: dict = to_retry_queue.get_nowait()
                last_msg = datetime.now()
                if 'send_pending_notfications' in dict:
                    # Send the pending_notfications list back to the caller
                    from_retry_queue.put(pending_notfications)
                else:
                    pending_notfications.append(msg)
            except Empty:
                pass

            next_pending_notfications = list()
            for msg in pending_notfications:
                try:
                    self._raw_send(**msg)
                except:
                    next_pending_notfications.append(msg)
            pending_notfications = next_pending_notfications

            time.sleep(30)
            if (datetime.now() - last_msg).total_seconds > (self._retry_time_limit_mins * 60):
                break

    def _start_retry_processor(self):
        if self._retry_process is not None:
            raise RuntimeError("_retry_process already set. _start_retry_processor called twice?")
        self._to_retry_queue = multiprocessing.Queue()
        self._from_retry_queue = multiprocessing.Queue()
        self._retry_process = multiprocessing.Process(
            target=self._retry_processor,
            kwargs={
                'to_retry_queue': self._to_retry_queue,
                'from_retry_queue': self._from_retry_queue,
            }
        )
        self._retry_process.start()

    def send(self, subject, message, sensitive_message=None, attachment=None, throw_exception=False):
        try:
            self._raw_send(
                subject=subject,
                message=message,
                sensitive_message=sensitive_message,
                attachment=attachment,
            )
        except Exception as e:
            if throw_exception:
                raise
            else:
                if self._retry_process is None:
                    self._start_retry_processor()
                self._to_retry_queue.put(dict(
                    subject=subject,
                    message=f"RETRY! Original from: {datetime.now()}\n{message}",
                    sensitive_message=sensitive_message,
                    attachment=attachment,
                ))
