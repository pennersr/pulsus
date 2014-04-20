import logging
import grequests

from ..base.service import BaseService

logger = logging.getLogger(__name__)


class GCMService(BaseService):

    service_type = 'gcm'

    def __init__(self, api_key):
        super(GCMService, self).__init__()
        self.api_key = api_key

    def send_notification(self, message):
        logger.info(u'GCM push: %r' % message)
        url = "https://android.googleapis.com/gcm/send"
        headers = {'Authorization': 'key=' + self.api_key,
                   'Content-Type': 'application/json'}
        req = grequests.post(url,
                             data=message.pack(),
                             headers=headers)
        resp = grequests.map([req])[0]
        print resp.status_code
        print resp.content
        print resp.headers
        # Update auth token
        # Inspect id/error retry-after
        # https://groups.google.com/group/android-c2dm/browse_thread/thread/00b03b6a0985059f/14b69680f3b6926b  # noqa

        return resp
