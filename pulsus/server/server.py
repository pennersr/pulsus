from gevent import monkey
monkey.patch_all()

from datetime import datetime
from gevent.queue import Empty

import os
import json
import gevent
import logging
import logging.config
import ConfigParser

from werkzeug.wrappers import Request, Response

from .services.apns import NotificationService, NotificationMessage
from .services.bbp import BlackBerryPushService, BlackBerryPushNotification
from .services.c2dm import C2DMService, C2DMNotification


logger = logging.getLogger(__name__)


class APIServer(object):

    def __init__(self, *args, **kwargs):
        self.apns = kwargs.pop('apns')
        self.bbp = kwargs.pop('bbp')
        self.c2dm = kwargs.pop('c2dm')

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def dispatch_request(self, request):
        if request.path == '/api/push/' and request.method == 'POST':
            notifications = json.loads(request.data)
            self.push_notifications(notifications)
            resp = Response('bla')
            resp.status_code = 201
        elif request.path == '/api/feedback/' and request.method == 'GET':
            resp = self.handle_feedback(request)
        return resp

    def handle_feedback(self, request):
        feedback = []
        try:
            while True:
                epoch, token = self.apns.get_feedback(block=False)
                dt = datetime.utcfromtimestamp(epoch)
                feedback.append(dict(type='apns',
                                     marked_inactive_on=dt.isoformat(),
                                     token=token.encode('hex')))
        except Empty:
            pass
        resp = Response(json.dumps(feedback))
        return resp

    def push_notifications(self, notifications):
        for notification in notifications:
            if notification['type'] == 'apns':
                self.push_apns(notification)
            elif notification['type'] == 'c2dm':
                self.push_c2dm(notification)
            elif notification['type'] == 'bbp':
                self.push_bbp(notification)
            else:
                logger.error("Unknown push type")

    def push_c2dm(self, notification):
        logger.debug("Sending C2DM notification")
        n = C2DMNotification(notification['registration_id'],
                             notification['payload'])
        self.c2dm.push(n)

    def push_bbp(self, notification):
        logger.debug("Sending BBP notification")
        n = BlackBerryPushNotification(notification['device_pins'],
                                       notification['message'])
        self.bbp.push(n)

    def push_apns(self, notification):
        logger.debug("Sending APNS notification")
        token = notification['token'].decode('hex')
        kwargs = dict()
        for attr in ['alert', 'badge', 'extra', 'sound']:
            if attr in notification:
                kwargs[attr] = notification[attr]
        message = NotificationMessage(token,
                                      **kwargs)
        self.apns.send(message)


def apns_feedback_handler(apns):
    for fb in apns.get_feedback():
        print fb


def read_config(config_dir):
    config = ConfigParser.ConfigParser()
    config.read([os.path.join(config_dir, 'pulsus.conf')])
    return config


def setup(config):
    # Apple
    apns_server = NotificationService(
        sandbox=config.getboolean('apns', 'sandbox'),
        certfile=config.get('apns', 'cert_file_pem'))
    apns_server.start()

    gevent.spawn(apns_feedback_handler, apns_server)

    # BlackBerry
    try:
        bbp_server = BlackBerryPushService(config.get('bbp', 'app_id'),
                                           config.get('bbp', 'password'),
                                           config.get('bbp', 'push_url'))
        bbp_server.start()
    except ConfigParser.NoSectionError:
        bbp_server = None

    # C2DM
    c2dm_server = C2DMService(config.get('c2dm', 'source'),
                              config.get('c2dm', 'email'),
                              config.get('c2dm', 'password'))
    c2dm_server.start()

    # API
    api_server = APIServer(apns=apns_server,
                           bbp=bbp_server,
                           c2dm=c2dm_server)
    return api_server
