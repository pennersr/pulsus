==================
Welcome to pulsus!
==================

A Push Notification Service, written in Python, handling Apple APNS,
and Google GCM.

Installation
============

Pulsus configuration file over at `/home/example/etc/pulsus/pulsus.conf`::

    [server]
    address = 127.0.0.1
    port = 8321

    [apns:sandbox]
    cert_file_pem = /home/example/etc/pulsus/apns-dev.pem

    [apns]
    cert_file_pem = /home/example/etc/pulsus/apns.pem

    [gcm]
    api_key=AIzaSyATHISISSECRET

A `logging.conf` file is required to be present in the same directory.
Then, start as follows::

    /home/example/virtualenv/bin/python -m pulsus.server.serve /home/example/etc/pulsus/


Usage
=====

Client::

    from pulsus.client import Client
    from pulsus.services.apns import APNSNotification
    from pulsus.services.gcm import GCMJSONMessage

    android_message = GCMJSONMessage(
        registration_ids=['APA91bF....zLnytKBQ'],
        data={'message': 'Hello World!'})

    ios_message = APNSNotification(
        token='676be1c77...',
        sandbox=True,
        alert='Helo World!')])

    client = Client('127.0.0.1', 8321)
    client.push([android_message, ios_message])
