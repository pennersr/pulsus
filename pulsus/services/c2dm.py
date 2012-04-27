import requests
import requests.async
import urllib

class C2DMService(object):
    def __init__(self, source, email, password):
        self.source = source
        self.email = email
        self.password = password


    def get_auth_token(self):
        req = requests.async.post('https://www.google.com/accounts/ClientLogin',
                             data={'Email': self.email,
                                   'Passwd': self.password,
                                   'accountType': 'GOOGLE',
                                   'source': self.source,
                                   'service': 'ac2dm'})
        resp = requests.async.map([req])[0]
        resp.raise_for_status()
        print resp.content
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
        print headers
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

