from gevent import monkey
monkey.patch_all()

import os
import logging.config
import sys

from werkzeug.serving import run_simple


if __name__ == "__main__":
    assert len(sys.argv) == 2, "Usage: pulsus <config_dir>"

    config_dir = sys.argv[1]
    # Must go 1st
    logging.config.fileConfig(os.path.join(config_dir, 'logging.conf'))
    logger = logging.getLogger(__name__)

    from . import server
    config = server.read_config(config_dir)

    server = server.setup(config)
    server_address = config.get('server', 'address')
    server_port = config.getint('server', 'port')
    logger.info("Pulsus started")
    run_simple(server_address, server_port, server)
