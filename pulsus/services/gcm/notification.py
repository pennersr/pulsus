import json
from ..base.notification import BaseNotification


class GCMMessage(BaseNotification):

    service_type = 'gcm'


class GCMJSONMessage(GCMMessage):

    service_type = 'gcm'
    notification_type = 'json'

    def __init__(self, registration_ids, **kwargs):
        optional = [
            'collapse_key',
            'time_to_live',
            'delay_while_idle',
            'restricted_package_name',
            'data',
            'dry_run']
        self.data = {}
        for k, v in kwargs.iteritems():
            assert k in optional
            self.data[k] = v
        self.data['registration_ids'] = registration_ids

    def serialize_data(self):
        return self.data

    @classmethod
    def deserialize_data(cls, data):
        return GCMJSONMessage(**data)

    def pack(self):
        return json.dumps(self.data)
