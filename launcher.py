#!/usr/bin/env python

import logging

from tornado import ioloop, options
from viper import application

options.define('port', default=3000, help='run on the given port', type=int)
options.define('mongodb_host', default="127.0.0.1", type=str)
options.define('mongodb_port', default=27017, type=int)

logger = logging.getLogger(__file__)

if __name__ == '__main__':
    try:
        options.parse_command_line()
        application(mongodb={
            'host': options.options.mongodb_host,
            'port': options.options.mongodb_port
        }).listen(options.options.port)
        logger.info('Listening on port: %s', options.options.port)
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logger.info('Shutting down the server')
