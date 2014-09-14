import json
import requests


class Client(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.api_url = 'http://{0}:{1}/api'.format(address, port)

    def push(self, notifications):
        data = json.dumps([n.serialize() for n in notifications])
        resp = requests.post(self.api_url + '/push/',
                             data=data)
        return resp

    def feedback(self):
        resp = requests.post(self.api_url + '/feedback/')
        resp.raise_for_status()
        return resp.json()
