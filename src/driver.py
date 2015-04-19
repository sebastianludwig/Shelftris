#!/usr/bin/env python3

import logging
import logging.config
import yaml

from adafruit import pca9685
from adafruit import wirebus

from shelftris import Color

import time

def loop():
    logger = logging.getLogger('debug')

    driver = pca9685.Driver(64, 1, logger=logger)

    while True:
        try:
            black = Color()
            driver.setPWM(0, 0, 0.5)
            time.sleep(1)
            driver.setPWM(0, 0, 0)
            # # for led in range(0, 8):
            # #     color = Color(hue = (led + 1) / 3, saturation = 1, brightness = 1)
            # #     driver.set_led(led, color)
            # color = Color(hue = 0.2, saturation = 1, brightness = 0.1)
            # driver.set_led(0, color)
            # driver.write()
            time.sleep(0.3)
        except (KeyboardInterrupt, SystemExit):
            break
    

if __name__ == '__main__':
    loop()
