#!/usr/bin/env python3

import yaml
import logging
import logging.config
import os
import time
import copy
import random
import colorsys
from enum import Enum
# from termcolor import colored

import helper
from hardware import IKEAShelf

def stringify(container, vertical_border = '', horizontal_border = ''):
    s = ''
    if len(horizontal_border) > 0:
        s += vertical_border + horizontal_border * len(container) + vertical_border + '\n'
    if len(vertical_border) > 0:
        s += vertical_border
    prev_y = None
    for (x, y, color) in helper.row_wise(container):
        if prev_y is not None and y != prev_y:
            s += vertical_border + '\n' + vertical_border
        if color is None:
            s += ' '
        else:
            brightness = int(color.brightness * 9)
            if brightness == 0:
                s += ' '
            else:
                text = "%d" % brightness
                attrs = []
                if brightness > 6:
                    attrs = ['reverse']
                elif brightness <=3:
                    attrs = ['dark']
                color = 'red' if color.hue > 0.6 else 'green'
                #s += colored(text, color, attrs = attrs)
                s += str(brightness)
            
        prev_y = y
    if len(vertical_border) > 0:
        s += vertical_border
    if len(horizontal_border) > 0:
        s += '\n' + vertical_border + horizontal_border * len(container) + vertical_border
    return s


class Color:
    def __init__(self, hue = 0.0, saturation = 0.0, brightness = 0.0):
        self.hue = float(hue)
        self.saturation = float(saturation)
        self.brightness = float(brightness)

    def __eq__(self, other):
        if other is None: return False
        return self.hue == other.hue and self.saturation == other.saturation and self.brightness == other.brightness

    def __str__(self):
        return "h: %.1f s: %.1f b: %.1f" % (self.hue, self.saturation, self.brightness)

    def blend_towards(self, target_color, current_progress, new_progress):
        self.hue = self.__blend_value(self.hue, target_color.hue, current_progress, new_progress)
        self.saturation = self.__blend_value(self.saturation, target_color.saturation, current_progress, new_progress)
        self.brightness = self.__blend_value(self.brightness, target_color.brightness, current_progress, new_progress)

    def __blend_value(self, current_value, target_value, current_progress, new_progress):
        progress_step = new_progress - current_progress
        remaining_difference = target_value - current_value
        remaining_progress = 1.0 - current_progress
        if remaining_progress < 0.0001:
            return target_value

        start_value = target_value - 1.0 / remaining_progress * remaining_difference

        total_difference = target_value - start_value
        step_difference = total_difference * progress_step
        return current_value + step_difference

    def rgb(self):
        return colorsys.hsv_to_rgb(self.hue, self.saturation, self.brightness)

    def hsb(self):
        return (self.hue, self.saturation, self.brightness)


class Shape(Enum):
     T = [[True, None], [True, True], [True, None]]
     O = [[True, True], [True, True]]
     I = [[True, True, True, True]]
     J = [[None, None, True], [True, True, True]]
     L = [[True, True, True], [None, None, True]]
     Z = [[True, None], [True, True], [None, True]]
     S = [[None, True], [True, True], [True, None]]
     

class Brick:
    def __init__(self, shape, color, x, y):
        self.shape = shape
        self.position = (x, y)
        self.gravity_affected = True
        self.pattern = copy.deepcopy(shape.value)
        for (x, y, value) in helper.column_wise(self.pattern):
            if value is None: continue
            self.pattern[x][y] = color
        
    @property
    def x(self):
        return self.position[0]
    
    @property
    def y(self):
        return self.position[1]
    
    @property
    def width(self):
        return len(self.pattern)
    
    @property
    def height(self):
        return len(self.pattern[0])

    def set_saturation(self, saturation):
        for (x, y, color) in helper.column_wise(self.pattern):
            color.saturation = saturation

    def set_brightness(self, brightness):
        for (x, y, color) in helper.column_wise(self.pattern):
            color.brightness = brightness
    
    def __str__(self):
        return stringify(self.pattern)

    def rotate_cw(self):
        self.pattern = list(zip(*self.pattern))
        self.pattern.reverse()

    def rotate_ccw(self):
        self.pattern.reverse()
        self.pattern = list(zip(*self.pattern))


class Field:
    def __init__(self, width, height):
        self.field = helper.array_2d(width, height)
    
    @property
    def width(self):
        return len(self.field)
    
    @property
    def height(self):
        return len(self.field[0])

    def set_all_saturation(self, saturation):
        for (x, y, color) in helper.column_wise(self.field):
            color.saturation = saturation

    def set_all_brightness(self, brightness):
        for (x, y, color) in helper.column_wise(self.field):
            color.brightness = brightness

    def can_move(self, brick, new_position):
        # return True
        if (new_position[0] < 0 or
                new_position[0] + brick.width  > self.width or
                new_position[1] + brick.height > self.height):
            return False
        for (x, y, color) in helper.column_wise(brick.pattern):
            if color is None: continue
            if self.field[new_position[0] + x][new_position[1] + y] is not None: return False
        return True

    def is_outside(self, brick):
        if (brick.position[0] + brick.width < 0 or
                brick.position[0] > self.width or
                brick.position[1] > self.height):
            return True
        return False
    
    def __str__(self):
        return stringify(self.field)
    
    def merge(self, brick):
        # transfer brick.pattern to target
        for (x, y, color) in helper.column_wise(brick.pattern):
            if color is None: continue
            if brick.x + x < 0 or brick.x + x >= self.width: continue
            if brick.y + y < 0 or brick.y + y >= self.height: continue
            self.field[brick.x + x][brick.y + y] = color


class Game:
    def __init__(self, width, height):
        self.field = Field(width, height)
        self.bricks = []
        self.views = []

    def loop(self):
        last_update = time.time()
        while True:
            try:
                now = time.time()
                elapsed_time = now - last_update
                # TODO call at different rates (view faster than the game)
                self.update(elapsed_time)
                for view in self.views:
                    view.update(elapsed_time)

                last_update = now

                time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                break

    def update(self, elapsed_time):
        to_remove = []
        for brick in self.bricks:
            new_position = (brick.x, brick.y +1)
            if self.field.can_move(brick, new_position):
                brick.position = new_position
            else:
                self.field.merge(brick)
                to_remove.append(brick)

            if self.field.is_outside(brick):
                to_remove.append(brick)
        for brick in to_remove:
            self.bricks.remove(brick)
        
    def place_brick(self, brick):
        if brick.gravity_affected:
            self.bricks.append(brick)
        else:
            self.field.merge(brick)

    def set_all_saturation(self, saturation):
        self.field.set_all_saturation(saturation)
        for brick in self.bricks:
            brick.set_saturation = saturation

    def set_all_brightness(self, brightness):
        self.field.set_all_saturation(saturation)
        for brick in self.bricks:
            brick.set_saturation = saturation

    def state(self):
        # TODO cache by tick (which is incremented every update) - or have boolean cache_valid which is set to false every update...mmmh..is caching really an option? This way still all requesting objects would work on the same copy..
        "2D array of Color objects"
        field = copy.deepcopy(self.field)
        for brick in self.bricks:
            field.merge(brick)
        return field.field


class ConsoleStateView:
    def __init__(self, stateful, in_place = False):
        self.stateful = stateful
        self._needs_jump = False
        self.in_place = in_place

    def update(self, elapsed_time):
        if self.in_place and self._needs_jump:
            print("\033[%dA" % (len(self.stateful.state()[0]) + 3))
        print(stringify(self.stateful.state(), vertical_border = '|', horizontal_border = '-'))
        self._needs_jump = True


class ColorBlendingView:
    def __init__(self, game):
        self.game = game
        self.blend_time = 1
        self.current_state = game.state()
        self.previous_target = game.state()
        self.blend_progress = game.state()
        for (x, y, _) in helper.column_wise(self.current_state):
            self.current_state[x][y] = None
            self.previous_target[x][y] = None
            self.blend_progress[x][y] = 0

    @property
    def width(self):
        return len(self.current_state)
    
    @property
    def height(self):
        return len(self.current_state[0])

    def update(self, elapsed_time):
        for (x, y, current_color) in helper.column_wise(self.current_state):
            target_color = self.game.state()[x][y]
            if self.previous_target[x][y] != target_color:
                self.blend_progress[x][y] = 0
                self.previous_target[x][y] = target_color

            if current_color == target_color:
                continue

            if target_color is None:
                target_color = Color(hue = current_color.hue, saturation = current_color.saturation, brightness = 0)

            if current_color is None:
                current_color = Color(hue = target_color.hue, saturation = target_color.saturation, brightness = 0)
                self.current_state[x][y] = current_color

            progress = min(self.blend_progress[x][y] + elapsed_time / self.blend_time, 1)
            current_color.blend_towards(target_color, self.blend_progress[x][y], progress)
            self.blend_progress[x][y] = progress

    def state(self):
        return copy.deepcopy(self.current_state)



def runGame():
    with open(helper.relative_path('..', 'conf', 'logging_conf.yaml')) as f:
        logging.config.dictConfig(yaml.load(f))

    logger = logging.getLogger('debug')

    game = Game(2, 4)
    colorView = ColorBlendingView(game)
    driver = IKEAShelf(colorView, logger=logger)
    consoleView = ConsoleStateView(game, in_place=True)
    
    color = Color(0.5, 1, 1)
    brick = Brick(Shape.T, color, 0, 0)
    brick.rotate_cw()
    game.place_brick(brick)
    #     shape = random.choice(list(Shape))
    #     x = random.randrange(self.field.width - len(shape.value))
    #     y = 0
    #     brick = Brick(shape, random.choice(colors), x, y)
    #     brick.gravity_affected = True
    #     self.place_brick(brick)


    game.views += [colorView, consoleView, driver]
    game.loop()

if __name__ == '__main__':
    runGame()
