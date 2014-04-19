import os
import logging
import sys

from werkzeug.serving import run_simple

from . import server

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    assert len(sys.argv) == 2, "Usage: pulsus <config_dir>"

    config_dir = sys.argv[1]
    config = server.read_config(config_dir)
    logging.config.fileConfig(os.path.join(config_dir, 'logging.conf'))
    server = server.setup(config)
    server_address = config.get('server', 'address')
    server_port = config.getint('server', 'port')
    logger.info("Pulsus started")
    run_simple(server_address, server_port, server)
