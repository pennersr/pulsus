import json
import requests


class Client(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.push_url = 'http://{0}:{1}/api/push/'.format(address, port)

    def push(self, notifications):
        data = json.dumps([n.serialize() for n in notifications])
        resp = requests.post(self.push_url,
                             data=data)
        return resp
