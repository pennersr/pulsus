import logging

import gevent
from gevent.queue import Queue
from gevent.event import Event

INITIAL_TIMEOUT = 5
MAX_TIMEOUT = 600


logger = logging.getLogger(__name__)


class BaseService(object):
    service_type = None

    def __init__(self):
        self._send_queue = Queue()
        self._send_queue_cleared = Event()
        self._send_greenlet = None
        self.timeout = INITIAL_TIMEOUT
        self._feedback_queue = Queue()

    def start(self):
        """Start the message sending loop."""
        if self._send_greenlet is None:
            self._send_greenlet = gevent.spawn(self.save_err, self._send_loop)

    def _send_loop(self):
        self._send_greenlet = gevent.getcurrent()
        try:
            logger.info("%s service started" % self.service_type)
            while True:
                message = self._send_queue.get()
                try:
                    self.send_notification(message)
                except Exception:
                    self.error_sending_notification(message)
                else:
                    self.timeout = INITIAL_TIMEOUT
                finally:
                    if self._send_queue.qsize() < 1 and \
                            not self._send_queue_cleared.is_set():
                        self._send_queue_cleared.set()
        except gevent.GreenletExit:
            pass
        finally:
            self._send_greenlet = None
        logger.info("%s service stopped" % self.service_type)

    def stop(self, timeout=10.0):
        if (self._send_greenlet is not None) and \
                (self._send_queue.qsize() > 0):
            self.wait_send(timeout=timeout)

        if self._send_greenlet is not None:
            gevent.kill(self._send_greenlet)
            self._send_greenlet = None
        return self._send_queue.qsize() < 1

    def wait_send(self, timeout=None):
        self._send_queue_cleared.clear()
        return self._send_queue_cleared.wait(timeout=timeout)

    def queue_notification(self, notification):
        self._send_queue.put(notification)

    def send_notification(self, notification):
        raise NotImplementedError

    def save_err(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            self.last_err = e
            raise

    def get_last_error(self):
        return self.last_err

    def error_sending_notification(self, notification):
        logger.exception("Error while pushing")
        self._send_queue.put(notification)
        gevent.sleep(self.timeout)
        # approaching Fibonacci series
        timeout = int(round(float(self.timeout) * 1.6))
        self.timeout = min(timeout, MAX_TIMEOUT)

    def check_blocking(self):
        if self.timeout == INITIAL_TIMEOUT:
            return False
        return True
