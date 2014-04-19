import json
import requests


class C2DMNotification(object):
    def __init__(self, registration_id, payload):
        self.registration_id = registration_id
        self.payload = payload

    def marshall(self):
        return {'type': 'c2dm',
                'registration_id': self.registration_id,
                'payload': self.payload}


class BBPNotification(object):
    def __init__(self, device_pins, message):
        self.device_pins = device_pins
        self.message = message

    def marshall(self):
        return {'type': 'bbp',
                'device_pins': self.device_pins,
                'message': self.message}


class APNSNotification(object):
    """
    Inititalizes a push notification message.

    token - device token
    alert - message string or message dictionary
    badge - badge number
    sound - name of sound to play
    identifier - message identifier
    expiry - expiry date of message
    extra - dictionary of extra parameters
    """
    def __init__(self, token, alert=None, badge=None, sound=None,
                 extra=None):
        if len(token) != 64:
            raise ValueError(u"Token must be a 64-char hex string.")
        if (alert is not None) and (not isinstance(alert, (str, unicode))):
            raise ValueError
        self.token = token
        self.alert = alert
        self.badge = badge
        self.sound = sound
        self.extra = extra

    def marshall(self):
        ret = dict(type='apns',
                   token=self.token)
        for attr in ['alert', 'badge', 'extra', 'sound']:
            val = getattr(self, attr)
            if val is not None:
                ret[attr] = val
        return ret


class Client(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.push_url = 'http://{0}:{1}/api/push/'.format(address, port)

    def push(self, notifications):
        data = json.dumps([n.marshall() for n in notifications])
        resp = requests.post(self.push_url,
                             data=data)
        return resp
