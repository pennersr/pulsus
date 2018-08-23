import logging
import requests
import time
from datetime import datetime

import gevent
from gevent.event import Event
from gevent.queue import Queue

from ..base.service import BaseService


INITIAL_TIMEOUT = 5
MAX_TIMEOUT = 600
WORKER_COUNT = 20

logger = logging.getLogger(__name__)


class GCMServiceWorker:

    def __init__(self, worker_id, api_key, feedback_queue):
        self._send_queue = Queue()
        self._send_queue_cleared = Event()
        self._send_greenlet = None
        self.timeout = INITIAL_TIMEOUT
        self._feedback_queue = feedback_queue
        self.worker_id = worker_id
        self.api_key = api_key
        self.session = requests.Session()

    def start(self):
        """Start the message sending loop."""
        self._send_greenlet = gevent.spawn(self.save_err, self._send_loop)

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

    def _send_loop(self):
        try:
            logger.info("GCM service started: worker %d" % (
                self.worker_id))
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
        logger.info("GCM service stopped: worker %d" % (
            self.worker_id))

    def send_notification(self, message):
        t = time.time()
        logger.info('Pushing GCM message...')
        url = "https://fcm.googleapis.com/fcm/send"
        headers = {'Authorization': 'key=' + self.api_key,
                   'Content-Type': 'application/json'}
        resp = self.session.post(
            url,
            data=message.pack(),
            headers=headers)
        logger.info('...pushed GCM message, took %fs' % (time.time() - t))
        resp.raise_for_status()
        data = resp.json()
        # Example:
        # {"multicast_id":592394215791271011422,
        #  "success":1,"failure":0,"canonical_ids":0,
        #  "results":[{"message_id":"0:12094e2028990994746%975ba952f9fd7ecd"}]}

        # If the value of failure and canonical_ids is 0, it's not
        # necessary to parse the remainder of the response.
        if not data['failure'] and not data['canonical_ids']:
            return
        registration_ids = message.registration_ids
        for result_i, result in enumerate(data['results']):
            logger.info('Result: %r' % result)
            # message_id = result['message_id']

            sent_registration_id = None
            if result_i < len(registration_ids):
                sent_registration_id = registration_ids[result_i]
            else:
                logger.error('Unable to lookup sent registration_id')

            registration_id = result.get('registration_id')
            error = result.get('error')
            if registration_id:
                # If registration_id is set, replace the original ID
                # with the new value (canonical ID) in your server
                # database. Note that the original ID is not part of
                # the result, so you need to obtain it from the list
                # of code>registration_ids passed in the request
                # (using the same index).

                # FIXME
                pass
            if error:
                if error == 'Unavailable':
                    # If it is Unavailable, you could retry to send it in
                    # another request.

                    # FIXME
                    pass
                elif error == 'NotRegistered':
                    # {u'error': u'NotRegistered'}

                    # you should remove the registration ID from your
                    # server database because the application was
                    # uninstalled from the device or it does not have a
                    # broadcast receiver configured to receive
                    # com.google.android.c2dm.intent.RECEIVE intents.

                    if sent_registration_id:
                        epoch = time.mktime(datetime.now().utctimetuple())
                        logger.info(
                            'Marking registration ID as to be'
                            ' removed: {}'.format(
                                sent_registration_id))
                        self._feedback_queue.put((
                            epoch,
                            sent_registration_id))
                else:
                    # Otherwise, there is something wrong in the
                    # registration ID passed in the request; it is
                    # probably a non-recoverable error that will also
                    # require removing the registration from the server
                    # database. See Interpreting an error response for all
                    # possible error values.

                    # FIXME
                    pass

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


class GCMService(BaseService):

    def __init__(self, api_key):
        self.feedback_queue = Queue()
        self.workers = [
            GCMServiceWorker(i, api_key, self.feedback_queue)
            for i in range(WORKER_COUNT)]
        self.next_worker = 0

    def get_feedback(self, block=True, timeout=None):
        return self.feedback_queue.get(
            block=block,
            timeout=timeout)

    def queue_notification(self, notification):
        self.workers[self.next_worker].queue_notification(notification)
        self.next_worker = (self.next_worker + 1) % WORKER_COUNT

    def start(self):
        for w in self.workers:
            w.start()

    def stop(self, timeout=10.0):
        for w in self.workers:
            w.stop()
