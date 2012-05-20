import time
import random
import logging
from datetime import datetime, timedelta
import requests
import requests.async

import gevent
from gevent.queue import Queue
from gevent.event import Event

class  BlackBerryPushNotification(object):
    def __init__(self, device_pins, message, deliver_before=None, push_id=None):
        if not deliver_before:
            deliver_before = (datetime.now() + timedelta(minutes=10))
        if push_id is None:
            push_id = int((time.time() - 1335539652) * 1000)*100 + random.randint(0,100)
        self.device_pins = device_pins
        self.deliver_before = deliver_before
        self.push_id = push_id
        self.message = message

class BlackBerryPushService(object):
    def __init__(self, app_id, password, push_url):
        self.app_id = app_id
        self.password = password
        self.push_url = push_url
        self._send_queue = Queue()
        self._send_queue_cleared = Event()
        self.log = logging.getLogger('pulsus.service.bbp')

    def _send_loop(self):
        self._send_greenlet = gevent.getcurrent()
        try:
            self.log.info("BlackBerry Push service started")
            while True:
                notification = self._send_queue.get()
                try:
                    self._do_push(notification)
                except Exception, e:
                    print e
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
        self.log.info("BlackBerry Push service stopped")
        

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

    def push(self, notification):
        self._send_queue.put(notification)

    def _do_push(self, notification):
        addresses = "\n".join(['<address address-value="{pin}"/>'.format(pin=pin)
                               for pin in notification.device_pins])
        boundary = "8d5588928a90afd3009d"
        xml = """<?xml version="1.0"?>
<!DOCTYPE pap PUBLIC "-//WAPFORUM//DTD PAP 2.1//EN" "http://www.openmobilealliance.org/tech/DTD/pap_2.1.dtd">
<pap>
<push-message push-id="{push_id}" deliver-before-timestamp="{deliver_before}" source-reference="{app_id}">
{addresses}
<quality-of-service delivery-method="unconfirmed"/>
</push-message>
</pap>""".format(deliver_before=notification.deliver_before.strftime('%Y-%m-%dT%H:%M:%SZ'),
                 push_id=notification.push_id,
                 app_id=self.app_id,
                 addresses=addresses)
        # Poor man's multipart (failed using `requests` multipart support)
        post_data = """Content-Type: application/xml; charset=UTF-8

{xml}
--{boundary}
Content-Type: text/plain

{message}
--{boundary}
""".format(xml=xml,
           message=notification.message,
           boundary=boundary)

        headers = { 'Content-Type': 'multipart/related; boundary={0}; type=application/xml'.format(boundary) }
        req =  requests.async.post(self.push_url, 
                                   data=post_data,
                                   auth=(self.app_id, 
                                         self.password),
                                   headers=headers)
        resp = requests.async.map([req])[0]
        resp.raise_for_status()
        self.log.debug(resp.content)



