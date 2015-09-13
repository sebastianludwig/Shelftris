import asyncio
import traceback
from aiohttp import web
from shelftris import *

class WebServer:
    def __init__(self, loop, logger=None):
        self._loop = loop
        self.ip = '0.0.0.0'
        self.port = 80
        self.game = None
        self.logger = logger

        self._app = web.Application(loop=self._loop)
        self._app.router.add_route('POST', '/command', self._handle)


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
        try:
            command = yield from request.json()

            if self.game is None:
                return web.HTTPInternalServerError()

            self.logger.info(command)

            if command["action"] == "add_brick":
                return self._handle_add_brick(command)
            if command["action"] == "clear":
                return self._handle_clear(command)

            return web.HTTPNotFound()
        except Exception as ex:
            output = traceback.format_exception(ex.__class__, ex, ex.__traceback__)
            if self.logger is not None:
                self.logger.critical(''.join(output))

    def _handle_clear(self, command):
        self.game.field.clear()

    def _handle_add_brick(self, command):
        def mapShape(description):
            return {
                'T': Shape.T,
                'O': Shape.O,
                'I': Shape.I,
                'J': Shape.J,
                'L': Shape.L,
                'Z': Shape.Z,
                'S': Shape.S,
            }.get(description, None)

        self._handle_clear(command)        # TODO: remove

        shape = mapShape(command["shape"])
        if shape is None:
            return
        
        color = Color(command["color"]["hue"], command["color"]["saturation"], command["color"]["brightness"])
        brick = Brick(shape, color, command["origin"]["x"], command["origin"]["y"])
        brick.gravity_affected = False
        for _ in range(command["rotation"]):
            brick.rotate_cw()
        
        self.game.place_brick(brick)
        return web.HTTPOk()
