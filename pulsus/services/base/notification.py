class BaseNotification(object):

    service_type = None
    notification_type = None

    def serialize_data(self):
        raise NotImplementedError()

    def serialize(self):
        ret = {'data': self.serialize_data()}
        ret['type'] = self.service_type
        if self.notification_type:
            ret['kind'] = self.notification_type
        return ret

    @classmethod
    def deserialize(cls, data):
        # FIXME: Something hardcoded for now, to be
        # be replaced
        from ..apns import APNSNotification
        from ..gcm import GCMJSONMessage

        if data['type'] == APNSNotification.service_type:
            return APNSNotification.deserialize_data(data['data'])
        elif data['type'] == GCMJSONMessage.service_type:
            return GCMJSONMessage.deserialize_data(data['data'])
