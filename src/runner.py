#!/usr/bin/env python3

import asyncio
import logging
import logging.config
import yaml

from shelftris import *
from webserver import WebServer


def main():
    with open(helper.relative_path('..', 'conf', 'logging_conf.yaml')) as f:
        logging.config.dictConfig(yaml.load(f))

    logger = logging.getLogger('debug')

    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, loop.stop)

    game = Game(loop, 2, 4, logger=logger)
    colorView = ColorBlendingView(loop, game)
    driver = IKEAShelf(loop, colorView, logger=logger)
    consoleView = ConsoleStateView(loop, game, in_place=True)
    
    #     shape = random.choice(list(Shape))
    #     x = random.randrange(self.field.width - len(shape.value))
    #     y = 0
    #     brick = Brick(shape, random.choice(colors), x, y)
    #     brick.gravity_affected = True
    #     self.place_brick(brick)

    server = WebServer(loop=loop, logger=logger)
    server.game = game

    try:
        with server:
            loop.run_forever()
    finally:
        loop.close()

if __name__ == '__main__':
    main()
