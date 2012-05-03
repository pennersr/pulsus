import logging
import requests
import requests.async
import urllib

import gevent
from gevent.queue import Queue
from gevent.event import Event

class C2DMNotification(object):
    def __init__(self, registration_id, payload):
        self.registration_id = registration_id
        self.payload = payload

class C2DMService(object):
    def __init__(self, source, email, password):
        self.source = source
        self.email = email
        self.password = password
        self._send_queue = Queue()
        self._send_queue_cleared = Event()
        self.log = logging.getLogger('pulsus.service.c2dm')

    def _send_loop(self):
        self._send_greenlet = gevent.getcurrent()
        try:
            self.log.info("C2DM service started")
            while True:
                notification = self._send_queue.get()
                try:
                    self._do_push(notification)
                except Exception, e:
                    self.log.exception("Error while pushing")
                    self._send_queue.put(notification)
                    gevent.sleep(5.0)
                finally:
                    if self._send_queue.qsize() < 1 and \
                            not self._send_queue_cleared.is_set():
                        self._send_queue_cleared.set()
        except gevent.GreenletExit, e:
            pass
        finally:
            self._send_greenlet = None
        self.log.info("C2DM service stopped")
        

    def start(self):
        gevent.spawn(self._send_loop)

    def stop(self, timeout = 10.0):
        if (self._send_greenlet is not None) and \
                (self._send_queue.qsize() > 0):
            self.wait_send(timeout = timeout)

        if self._send_greenlet is not None:
            gevent.kill(self._send_greenlet)
            self._send_greenlet = None
        return self._send_queue.qsize() < 1


    def wait_send(self, timeout = None):
        self._send_queue_cleared.clear()
        self._send_queue_cleared.wait(timeout = timeout)


    def get_auth_token(self):
        req = requests.async.post('https://www.google.com/accounts/ClientLogin',
                             data={'Email': self.email,
                                   'Passwd': self.password,
                                   'accountType': 'GOOGLE',
                                   'source': self.source,
                                   'service': 'ac2dm'})
        resp = requests.async.map([req])[0]
        resp.raise_for_status()
        for line in resp.content.split():
            line = line.strip()
            parts = line.split('=')
            if len(parts) == 2 and parts[0] == 'Auth':
                return parts[1]

    def send_message(self, auth_token, reg_id, message):
        post_data = { 'registration_id': reg_id,
                      'collapse_key': '0',
                      'data.payload': message }
        url = "https://android.apis.google.com/c2dm/send"
        headers = { 'Authorization': 'GoogleLogin auth=' + auth_token }
        req = requests.async.post(url,
                                   data=post_data,
                                   headers=headers,
                                   verify=False)
        resp = requests.async.map([req])[0]
        print resp.status_code
        print resp.content
        print resp.headers
        # Update auth token
        # Inspect id/error retry-after
        # https://groups.google.com/group/android-c2dm/browse_thread/thread/00b03b6a0985059f/14b69680f3b6926b
        
        return resp

    def push(self, notification):
        self._send_queue.put(notification)

    def _do_push(self, notification):
        auth_token = self.get_auth_token()
        self.send_message(auth_token, notification.registration_id, notification.payload)


