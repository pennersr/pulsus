==================
Welcome to pulsus!
==================

A Push Notification Service, written in Python, handling Apple APNS,
Google C2DM, and Blackberry Push.

Installation
============

Upstart configuration file::

    start on runlevel [2345]
    stop on runlevel [!2345]
    
    exec su -s /bin/sh -c 'exec "$0" "$@"' example -- /home/example/virtualenv/bin/python -m pulsus.server /home/example/etc/pulsus/
    respawn

Pulsus configuration file over at `/home/example/etc/pulsus/pulsus.conf`::

    [server]
    address = 127.0.0.1
    port = 8321
    
    
    [apns]
    cert_file_pem = /home/example/etc/pulsus/apns.pem
    
    [bbp]
    app_id = 1234-567890thisisreallyasecret1234567890
    password = secret
    push_url = https://pushapi.eval.blackberry.com/mss/PD_pushRequest
    
    [c2dm]
    source = PulsusExample
    email = example@gmail.com
    password = secret

