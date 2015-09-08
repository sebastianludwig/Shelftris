import asyncio
from aiohttp import web
from shelftris import *

class WebServer:
    def __init__(self, loop, logger=None):
        self.ip = '0.0.0.0'
        self.port = 80
        self.game = None
        self.logger = logger
        self._loop = loop

        self._app = web.Application(loop=self._loop)
        self._app.router.add_route('GET', '/command', self._handle)


    def __enter__(self):
        """Ought to be called with no asyncio event loop running"""

        self._handler = self._app.make_handler()

        future_server = self._loop.create_server(self._handler, self.ip, self.port)
        self._server = self._loop.run_until_complete(future_server)

        if self.logger is not None:
            self.logger.info('server started, listening on %s:%s', self.ip, self.port)

        return self

    def __exit__(self, type, value, traceback):
        """Ought to be called with no asyncio event loop running"""

        if self._server is None:
            return False

        self._loop.run_until_complete(self._handler.finish_connections(1.0))
        self._server.close()
        self._loop.run_until_complete(self._server.wait_closed())
        self._loop.run_until_complete(self._app.finish())

        self._server = None
        if self.logger is not None:
            self.logger.info('server stopped')

        return False        

    @asyncio.coroutine
    def _handle(self, request):
        color = Color(0.5, 1, 1)
        brick = Brick(Shape.T, color, 0, 0)
        brick.gravity_affected = False
        brick.rotate_cw()
        if self.game is not None:
            self.game.place_brick(brick)
            return web.HTTPOk()

        return web.HTTPNotFound()

        
