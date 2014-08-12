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
        resp.raise_for_status()
        data = resp.json()
        # Example:
        # {"multicast_id":592394215791271011422,
        #  "success":1,"failure":0,"canonical_ids":0,
        #  "results":[{"message_id":"0:12094e2028990994746%975ba952f9fd7ecd"}]}

        # If the value of failure and canonical_ids is 0, it's not
        # necessary to parse the remainder of the response.
        if not data['failure'] and not data['canonical_ids']:
            return
        for result in data['results']:
            logger.info('Result: %r' % result)
            # message_id = result['message_id']
            registration_id = result.get('registration_id')
            error = result.get('error')
            if registration_id:
                # If registration_id is set, replace the original ID
                # with the new value (canonical ID) in your server
                # database. Note that the original ID is not part of
                # the result, so you need to obtain it from the list
                # of code>registration_ids passed in the request
                # (using the same index).

                # FIXME
                pass
            if error:
                if error == 'Unavailable':
                    # If it is Unavailable, you could retry to send it in
                    # another request.

                    # FIXME
                    pass
                elif error == 'NotRegistered':
                    # {u'error': u'NotRegistered'}

                    # you should remove the registration ID from your
                    # server database because the application was
                    # uninstalled from the device or it does not have a
                    # broadcast receiver configured to receive
                    # com.google.android.c2dm.intent.RECEIVE intents.

                    # FIXME
                    pass
                else:
                    # Otherwise, there is something wrong in the
                    # registration ID passed in the request; it is
                    # probably a non-recoverable error that will also
                    # require removing the registration from the server
                    # database. See Interpreting an error response for all
                    # possible error values.

                    # FIXME
                    pass
