import os
import logging
import struct
import time

import gevent
from gevent.event import Event
from gevent.queue import Queue
from gevent import socket
from gevent import ssl

try:
    import ujson as json
except ImportError:
    import json

INITIAL_TIMEOUT = 5
MAX_TIMEOUT = 600


logger = logging.getLogger(__name__)


class NotificationMessage(object):
    """
    Initializes a push notification message.

    token - device token
    alert - message string or message dictionary
    badge - badge number
    sound - name of sound to play
    identifier - message identifier
    expiry - expiry date of message
    extra - dictionary of extra parameters
    """
    def __init__(self, token, alert=None, badge=None, sound=None, identifier=0,
                 expiry=None, extra=None, **kwargs):
        if len(token) != 32:
            raise ValueError(u"Token must be a 32-byte binary string")
        if alert is not None and not isinstance(alert, (str, unicode, dict)):
            raise ValueError(u"Alert message must be a string or a dictionary")
        if expiry is None:
            expiry = long(time.time() + 365 * 86400)

        self.token = token
        self.alert = alert
        self.badge = badge
        self.sound = sound
        self.identifier = identifier
        self.expiry = expiry
        self.extra = extra

    def __str__(self):
        aps = {}
        if self.alert is not None:
            aps["alert"] = self.alert
        if self.badge is not None:
            aps["badge"] = self.badge
        if self.sound is not None:
            aps["sound"] = self.sound

        data = {"aps": aps}
        if self.extra is not None:
            data.update(self.extra)

        encoded = json.dumps(data)
        length = len(encoded)

        return struct.pack(
            "!bIIH32sH%(length)ds" % {"length": length},
            1, self.identifier, self.expiry,
            32, self.token, length, encoded)


class NotificationService(object):
    def __init__(self, sandbox=True, **kwargs):
        if "certfile" not in kwargs:
            raise ValueError(u"Must specify a PEM bundle.")
        if not os.path.exists(kwargs['certfile']):
            raise ValueError('PEM bundle file not found')
        self._sslargs = kwargs
        self._push_connection = None
        self._feedback_connection = None
        self._sandbox = sandbox
        self._send_queue = Queue()
        self._error_queue = Queue()
        self._feedback_queue = Queue()
        self._send_greenlet = None
        self._error_greenlet = None
        self._feedback_greenlet = None
        self._send_queue_cleared = Event()
        self.timeout = 5
        self.last_err = None

    def set_sandbox(self, sandbox):
        self._sandbox = sandbox

    def _check_send_connection(self):
        if self._push_connection is None:
            tcp_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM, 0)
            s = ssl.wrap_socket(tcp_socket, ssl_version=ssl.PROTOCOL_SSLv3,
                                **self._sslargs)
            addr = ["gateway.push.apple.com", 2195]
            if self._sandbox:
                addr[0] = "gateway.sandbox.push.apple.com"
            s.connect_ex(tuple(addr))
            self._push_connection = s
            self._error_greenlet = gevent.spawn(self.save_err,
                                                self._error_loop)

    def _check_feedback_connection(self):
        if self._feedback_connection is None:
            tcp_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM, 0)
            s = ssl.wrap_socket(tcp_socket, ssl_version=ssl.PROTOCOL_SSLv3,
                                **self._sslargs)
            addr = ["feedback.push.apple.com", 2196]
            if self._sandbox:
                addr[0] = "feedback.sandbox.push.apple.com"
            s.connect_ex(tuple(addr))

            self._feedback_connection = s

    def check_blocking(self):
        if self.timeout == INITIAL_TIMEOUT:
            return False
        return True

    def _send_loop(self):
        self._send_greenlet = gevent.getcurrent()
        try:
            logger.info("APNS service started")
            while True:
                msg = self._send_queue.get()
                self._check_send_connection()
                try:
                    self._push_connection.send(str(msg))
                except Exception:
                    self._send_queue.put(msg)
                    if self._push_connection is not None:
                        self._push_connection.close()
                        self._push_connection = None
                    gevent.sleep(self.timeout)
                    # approaching Fibonacci series
                    timeout = int(round(float(self.timeout) * 1.6))
                    if timeout > MAX_TIMEOUT:
                        timeout = MAX_TIMEOUT
                    self.timeout = timeout
                else:
                    # reset the timeout if any success
                    self.timeout = INITIAL_TIMEOUT
                finally:
                    if self._send_queue.qsize() < 1 and \
                            not self._send_queue_cleared.is_set():
                        self._send_queue_cleared.set()
        except gevent.GreenletExit:
            logger.exception('Error')
        finally:
            logger.info("APNS service stopped")
            self._send_greenlet = None

    def _error_loop(self):
        self._error_greenlet = gevent.getcurrent()
        try:
            while True:
                if self._push_connection is None:
                    break
                msg = self._push_connection.recv(1 + 1 + 4)
                if len(msg) < 6:
                    return
                data = struct.unpack("!bbI", msg)
                self._error_queue.put((data[1], data[2]))
        except gevent.GreenletExit:
            logger.exception('Error')
        finally:
            if self._push_connection is not None:
                self._push_connection.close()
                self._push_connection = None
            self._error_greenlet = None

    def _feedback_loop(self):
        self._feedback_greenlet = gevent.getcurrent()
        try:
            self._check_feedback_connection()
            while True:
                msg = self._feedback_connection.recv(4 + 2 + 32)
                if len(msg) < 38:
                    return
                data = struct.unpack("!IH32s", msg)
                self._feedback_queue.put((data[0], data[2]))
        except gevent.GreenletExit:
            logger.exception('Error')
        finally:
            if self._feedback_connection:
                self._feedback_connection.close()
                self._feedback_connection = None
            self._feedback_greenlet = None

    def send(self, obj):
        """Send a push notification"""
        if not isinstance(obj, NotificationMessage):
            raise ValueError(u"You can only send NotificationMessage objects.")
        self._send_queue.put(obj)

    def get_error(self, block=True, timeout=None):
        """
        Get the next error message.

        Each error message is a 2-tuple of (status, identifier)."""
        return self._error_queue.get(block=block, timeout=timeout)

    def get_feedback(self, block=True, timeout=None):
        """
        Get the next feedback message.

        Each feedback message is a 2-tuple of (timestamp, device_token)."""
        if self._feedback_greenlet is None:
            self._feedback_greenlet = gevent.spawn(self.save_err,
                                                   self._feedback_loop)
        return self._feedback_queue.get(block=block, timeout=timeout)

    def get_last_error(self):
        return self.last_err

    def save_err(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            self.last_err = e
            raise

    def wait_send(self, timeout=None):
        """Wait until all queued messages are sent."""
        self._send_queue_cleared.clear()
        return(self._send_queue_cleared.wait(timeout=timeout))

    def start(self):
        """Start the message sending loop."""
        if self._send_greenlet is None:
            self._send_greenlet = gevent.spawn(self.save_err, self._send_loop)

    def stop(self, timeout=10.0):
        """
        Send all pending messages, close connection.
        Returns True if no message left to sent. False if dirty.

        - timeout: seconds to wait for sending remaining messages. disconnect
          immediately if None.
        """
        if (self._send_greenlet is not None) and \
                (self._send_queue.qsize() > 0):
            self.wait_send(timeout=timeout)

        if self._send_greenlet is not None:
            gevent.kill(self._send_greenlet)
            self._send_greenlet = None
        if self._error_greenlet is not None:
            gevent.kill(self._error_greenlet)
            self._error_greenlet = None
        if self._feedback_greenlet is not None:
            gevent.kill(self._feedback_greenlet)
            self._feedback_greenlet = None

        return self._send_queue.qsize() < 1
