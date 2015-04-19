import time
import math
from .wirebus import I2C

# ===========================================================================
# Based on https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code
# Copyright (c) 2012-2013 Limor Fried, Kevin Townsend and Mikey Sklar for Adafruit Industries. All rights reserved.
# ===========================================================================

class Driver(object):
    # Registers/etc.
    __MODE1              = 0x00
    __MODE2              = 0x01
    __SUBADR1            = 0x02
    __SUBADR2            = 0x03
    __SUBADR3            = 0x04
    __PRESCALE           = 0xFE
    __LED0_ON_L          = 0x06
    __LED0_ON_H          = 0x07
    __LED0_OFF_L         = 0x08
    __LED0_OFF_H         = 0x09
    __ALL_LED_ON_L       = 0xFA
    __ALL_LED_ON_H       = 0xFB
    __ALL_LED_OFF_L      = 0xFC
    __ALL_LED_OFF_H      = 0xFD

    # Bits
    __RESTART            = 1 << 7
    __AI                 = 1 << 5
    __SLEEP              = 1 << 4
    __ALLCALL            = 1 << 0

    __INVRT              = 1 << 4
    __OUTDRV             = 1 << 2


    @classmethod
    def softwareReset(cls):
        "Sends a software reset (SWRST) command to all the servo drivers on the bus"
        bus_numbers = I2C.pinoutConfiguredBuses()
        for bus_number in bus_numbers:
            if I2C.isDeviceAnswering(0x00, bus_number):
                general_call = I2C(0x00, bus_number)
                general_call.writeRaw8(0x06)            # SWRST

    def __init__(self, address=0x40, busnum=-1, logger=None):
        self.logger = logger
        self.i2c = I2C(address, busnum=busnum, logger=self.logger)
        self.address = address
        if self.logger is not None:
            self.logger.debug("Reseting PCA9685 MODE1 (without SLEEP, but with AI) and MODE2")
        self.setAllPWM(0, 0)
        self.i2c.write8(self.__MODE2, self.__OUTDRV)
        self.i2c.write8(self.__MODE1, self.__ALLCALL | self.__AI)
        time.sleep(0.005)                                       # wait for oscillator

    def wakeUp(self):
        "Activates the sleep mode"
        mode1 = self.i2c.readU8(self.__MODE1)
        mode1 = mode1 & ~self.__SLEEP
        self.i2c.write8(self.__MODE1, mode1)
        time.sleep(0.005)

    def sleep(self):
        "Deactivates the sleep mode"
        mode1 = self.i2c.readU8(self.__MODE1)
        self.i2c.write8(self.__MODE1, mode1 | self.__SLEEP)

    def setPWMFreq(self, freq):
        "Sets the PWM frequency"

        # calculate pre scale (datasheet section 7.3.5)
        prescaleval = 25000000.0    # 25MHz
        prescaleval /= 4096.0       # 12-bit
        prescaleval /= float(freq)
        prescaleval -= 1.0
        if self.logger is not None:
            self.logger.debug("Setting PWM frequency to %d Hz", freq)
            self.logger.debug("Estimated pre-scale: %.2f", prescaleval)
        prescale = int(prescaleval + 0.5)
        if self.logger is not None:
            self.logger.debug("Final pre-scale: %d", prescale)

        oldmode = self.i2c.readU8(self.__MODE1)
        newmode = (oldmode & 0x7F) | self.__SLEEP                 # sleep (and preparation for restart)
        self.i2c.write8(self.__MODE1, newmode)                    # go to sleep
        self.i2c.write8(self.__PRESCALE, prescale)
        self.i2c.write8(self.__MODE1, oldmode)
        # restart (datasheet section 7.3.1.1)
        time.sleep(0.005)                                         # wait for oscillator
        self.i2c.write8(self.__MODE1, oldmode | self.__RESTART)

    def _scale_value(self, value):
        if value < 0 or value > 1: raise ValueError('PWM value not in interval [0, 1]: %s' % value)
        return int(value * 4095)

    def setPWM(self, channel, on, off):
        "Sets a single PWM channel"
        on = self._scale_value(on)
        off = self._scale_value(off)
        self.i2c.writeList(self.__LED0_ON_L+4*channel, [on & 0xFF, on >> 8, off & 0xFF, off >> 8])

    def setAllPWM(self, on, off):
        "Sets a all PWM channels"
        on = self._scale_value(on)
        off = self._scale_value(off)
        self.i2c.writeList(self.__ALL_LED_ON_L, [on & 0xFF, on >> 8, off & 0xFF, off >> 8])
