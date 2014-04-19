==================
Welcome to pulsus!
==================

A Push Notification Service, written in Python, handling Apple APNS,
Google C2DM, and Blackberry Push.

Installation
============

Pulsus configuration file over at `/home/example/etc/pulsus/pulsus.conf`::

    [server]
    address = 127.0.0.1
    port = 8321


    [apns]
    cert_file_pem = /home/example/etc/pulsus/apns.pem
    sandbox = True

    [bbp]
    app_id = 1234-567890thisisreallyasecret1234567890
    password = secret
    push_url = https://pushapi.eval.blackberry.com/mss/PD_pushRequest

    [c2dm]
    source = PulsusExample
    email = example@gmail.com
    password = secret


A `logging.conf` file is required to be present in the same directory.
Then, start as follows::

    /home/example/virtualenv/bin/python -m pulsus.server.serve /home/example/etc/pulsus/


Usage
=====

Client::

    from pulsus.client import Client, APNSNotification

    c = Client('127.0.0.1', 8321)
    c.push([APNSNotification(token='676be1c77...',
                             alert='Greetings from Pulsus!')])
