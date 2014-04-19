from . import server

config = server.read_config('.')
application = server.setup(config)
