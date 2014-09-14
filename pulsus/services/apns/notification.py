import struct
import json
import time

from ..base.notification import BaseNotification


class APNSNotification(BaseNotification):
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

    service_type = 'apns'

    def __init__(self, token, alert=None, badge=None, sound=None,
                 identifier=0, expiry=None, extra=None, sandbox=True):
        if len(token) != 64:
            raise ValueError(u"Token must be a 64-char hex string.")
        if (alert is not None) and (not isinstance(alert, (str, unicode))):
            raise ValueError
        self.token = token
        self.alert = alert
        self.badge = badge
        self.sound = sound
        self.identifier = identifier
        if expiry is None:
            expiry = long(time.time() + 365 * 86400)
        self.expiry = expiry
        self.extra = extra
        self.sandbox = sandbox

    @classmethod
    def deserialize_data(cls, data):
        return APNSNotification(**data)

    def serialize_data(self):
        ret = dict(token=self.token,
                   sandbox=self.sandbox)
        for attr in ['alert', 'badge', 'extra', 'sound',
                     'identifier', 'expiry']:
            val = getattr(self, attr)
            if val is not None:
                ret[attr] = val
        return ret

    def pack(self):
        aps = {}
        token = self.token.decode('hex')
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
            32, token, length, encoded)
