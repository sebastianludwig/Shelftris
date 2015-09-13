import helper
import yaml
import asyncio
import traceback
from shelftris import Color

if helper.is_raspberry():
    from adafruit import wirebus
    from adafruit import pca9685
else:
    from dummy import wirebus
    from dummy import pca9685


class Compartment:
    def __init__(self, driver, red_outlet, green_outlet, blue_outlet, logger=None):
        self.driver = driver
        self.red_outlet = red_outlet
        self.green_outlet = green_outlet
        self.blue_outlet = blue_outlet
        self.logger = logger

        self._color = None

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, new_color):
        if new_color is None:
            new_color = Color(0, 0, 0)

        if self._color == new_color: return

        self._color = new_color
        rgb = self._color.rgb()
        self.driver.setPWM(self.red_outlet, 0, rgb[0] ** 0.5)
        self.driver.setPWM(self.green_outlet, 0, rgb[1])
        self.driver.setPWM(self.blue_outlet, 0, rgb[2] ** 2)


class IKEAShelf:
    def __init__(self, loop, view, logger=None):
        self._loop = loop
        self.logger = logger
        self.view = view
        self.update_interval = 0.05
        self.drivers = {}    # driver_address -> driver
        self.compartments = helper.array_2d(self.view.width, self.view.height)

        with open(helper.relative_path('..', 'conf', 'IKEA.json')) as f:
            self._parse_config(yaml.load(f))

        asyncio.async(self.update(), loop=loop)


    def __del__(self):
        for _, driver in self.drivers.items():
            driver.setAllPWM(0, 0)

    def _parse_config(self, config):
        def driver_for_address(drivers, address):
            if address not in drivers:
                if not wirebus.I2C.isDeviceAnswering(address):
                    return None

                driver = pca9685.Driver(address, logger=self.logger)
                drivers[address] = driver
            return drivers[address]

        for square in config:
            driver_address = int(square["driver_address"], 16)
            driver = driver_for_address(self.drivers, driver_address)
            if driver is None:
                if logger is not None:
                    logger.critical("No driver found for at address 0x%02X", dirver_address)
                return
            compartment = Compartment(driver, square["red"], square["green"], square["blue"], logger=self.logger)
            self.compartments[square["position"][0]][square["position"][1]] = compartment

    @asyncio.coroutine
    def update(self):
        while True:
            try:
                for (x, y, color) in helper.row_wise(self.view.state()):
                    if self.compartments[x][y] is not None:
                        self.compartments[x][y].color = color
            except Exception as ex:
                output = traceback.format_exception(ex.__class__, ex, ex.__traceback__)
                if self.logger is not None:
                    self.logger.critical(''.join(output))
            yield from asyncio.sleep(self.update_interval)

