import os
import logging
import struct

import gevent
from gevent.queue import Queue
from gevent import socket
from gevent import ssl

from ..base.service import BaseService

from .notification import APNSNotification

INITIAL_TIMEOUT = 5
MAX_TIMEOUT = 600


logger = logging.getLogger(__name__)


class APNSService(BaseService):

    service_type = 'apns'

    def __init__(self, sandbox=True, **kwargs):
        super(APNSService, self).__init__()
        if "certfile" not in kwargs:
            raise ValueError(u"Must specify a PEM bundle.")
        if not os.path.exists(kwargs['certfile']):
            raise ValueError('PEM bundle file not found')
        self._sslargs = kwargs
        self._push_connection = None
        self._sandbox = sandbox
        self._error_queue = Queue()
        self._send_greenlet = None
        self._error_greenlet = None
        self._feedback_connection = None
        self._feedback_greenlet = None
        self.last_err = None

    def _check_send_connection(self):
        if self._push_connection is None:
            tcp_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM, 0)
            s = ssl.wrap_socket(tcp_socket, ssl_version=ssl.PROTOCOL_TLSv1,
                                **self._sslargs)
            addr = ["gateway.push.apple.com", 2195]
            if self._sandbox:
                addr[0] = "gateway.sandbox.push.apple.com"
            logger.debug('Connecting to %s' % addr[0])
            s.connect_ex(tuple(addr))
            self._push_connection = s
            self._error_greenlet = gevent.spawn(self.save_err,
                                                self._error_loop)

    def _check_feedback_connection(self):
        if self._feedback_connection is None:
            tcp_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM, 0)
            s = ssl.wrap_socket(tcp_socket, ssl_version=ssl.PROTOCOL_TLSv1,
                                **self._sslargs)
            addr = ["feedback.push.apple.com", 2196]
            if self._sandbox:
                addr[0] = "feedback.sandbox.push.apple.com"
            logger.debug('Connecting to %s' % addr[0])
            s.connect_ex(tuple(addr))

            self._feedback_connection = s

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

    def queue_notification(self, obj):
        """Send a push notification"""
        if not isinstance(obj, APNSNotification):
            raise ValueError(u"You can only send APNSNotification objects.")
        return super(APNSService, self).queue_notification(obj)

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

    def stop(self, timeout=10.0):
        """
        Send all pending messages, close connection.
        Returns True if no message left to sent. False if dirty.

        - timeout: seconds to wait for sending remaining messages. disconnect
          immediately if None.
        """
        super(APNSService, self).stop(timeout=timeout)

        if self._error_greenlet is not None:
            gevent.kill(self._error_greenlet)
            self._error_greenlet = None
        if self._feedback_greenlet is not None:
            gevent.kill(self._feedback_greenlet)
            self._feedback_greenlet = None

        return self._send_queue.qsize() < 1

    def error_sending_notification(self, notification):
        if self._push_connection is not None:
            self._push_connection.close()
            self._push_connection = None
        return super(APNSService, self).error_sending_notification(
            notification)

    def send_notification(self, notification):
        self._check_send_connection()
        logger.debug('Sending APNS notification')
        self._push_connection.send(notification.pack())
