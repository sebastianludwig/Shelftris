#!/usr/bin/env python

import time
import copy
import random
import colorsys
from enum import Enum

class Color:
  def __init__(self):
    self.hue = 0
    self.saturation = 0
    self.brightness = 0

  def __eq__(self, other):
    return self.hue == other.hue and self.saturation == other.saturation and self.brightness == other.brightness

  def __str__(self):
    return str(self.hue)

  def blend_towards(self, target_color, current_progress, new_progress):
    self.hue = self.__blend_value(self.hue, target_color.hue, current_progress, new_progress)
    self.saturation = self.__blend_value(self.saturation, target_color.saturation, current_progress, new_progress)
    self.brightness = self.__blend_value(self.brightness, target_color.brightness, current_progress, new_progress)

  def __blend_value(current_value, target_value, current_progress, new_progress):
    progress_step = new_progress - current_progress
    remaining_difference = target_value - current_value
    remaining_progress = 1 - current_progress
    start_value = target_value - 1 / remaining_progress * remaining_difference

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
   

def column_wise(container):
   for x_index, column in enumerate(container):
      for y_index, value in enumerate(column):
        yield (x_index, y_index, value)

def row_wise(container):
  row_wise = zip(*container)
  for y_index, row in enumerate(row_wise):
    for x_index, value in enumerate(row):
      yield (x_index, y_index, value)

def stringify(container):
  s = ''
  prev_y = None
  for (x, y, color) in row_wise(container):
    if prev_y is not None and y != prev_y:
      s += '\n'
    s += str(color) if color is not None else ' '
    prev_y = y
  return s


class Brick:
  def __init__(self, shape, color, x, y):
    self.shape = shape
    self.position = (x, y)
    self.gravity_affected = True
    self.pattern = copy.deepcopy(shape.value)
    for (x, y, value) in column_wise(self.pattern):
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
    for (x, y, color) in column_wise(self.pattern):
      color.saturation = saturation

  def set_brightness(self, brightness):
    for (x, y, color) in column_wise(self.pattern):
      color.brightness = brightness
  
  def __str__(self):
    return stringify(self.pattern)

  def rotate_cw(self):
    self.pattern = zip(*self.pattern)
    self.pattern.reverse()

  def rotate_ccw(self):
    self.pattern.reverse()
    self.pattern = zip(*self.pattern)


class Field:
  def __init__(self, width, height):
    self.field = [[None for _ in range(height)] for _ in range(width)]
  
  @property
  def width(self):
    return len(self.field)
  
  @property
  def height(self):
    return len(self.field[0])

  def set_all_saturation(self, saturation):
    for (x, y, color) in column_wise(self.field):
      color.saturation = saturation

  def set_all_brightness(self, brightness):
    for (x, y, color) in column_wise(self.field):
      color.brightness = brightness

  def can_move(self, brick, new_position):
    if (new_position[0] < 0 or
        new_position[0] + brick.width  > self.width or
        new_position[1] + brick.height > self.height):
      return False
    for (x, y, color) in column_wise(brick.pattern):
      if color is None: continue
      if self.field[new_position[0] + x][new_position[1] + y] is not None: return False
    return True
  
  def __str__(self):
    return stringify(self.field)
  
  def merge(self, brick):
    # transfer brick.pattern to target
    for (x, y, color) in column_wise(brick.pattern):
      if color is None: continue
      if brick.x + x < 0 or brick.x + x > self.width: continue
      if brick.y + y < 0 or brick.y + y > self.height: continue
      self.field[brick.x + x][brick.y + y] = color

class Game:
  def __init__(self):
    self.field = Field(9, 14)
    self.bricks = []
  
  def update(self, elapsed_time):
    to_remove = []
    for brick in self.bricks:
      new_position = (brick.x, brick.y +1)
      if self.field.can_move(brick, new_position):
        brick.position = new_position
      else:
        self.field.merge(brick)
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


class ConsoleView:
  def __init__(self, game):
    self.game = game

  def update(self, elapsed_time):
    print(stringify(game.state()))

class ColorBlendingView:
  def __init__(self, game):
    self.game = game
    self.blend_time = 2
    self.current_state = game.state()
    self.previous_target = game.state()
    self.blend_progress = game.state()
    for (x, y, ignore) in column_wise(self.current_state):
      self.current_state[x][y] = None
      self.previous_target[x][y] = None
      self.blend_progress = 0

  def update(self, elapsed_time):
    # have internal 2d array of colors
    # interate over self.game.state and blend h,s and b
    for (x, y, current_color) in self.current_state:
      target_color = self.game.state[x][y]
      if self.previous_target[x][y] != target:
        self.blend_progress[x][y] = 0
        self.previous_target[x][y] = target_color

      if current_color == target_color: continue

      progress = min(self.blend_progress[x][y] + self.blend_time / elapsed_time, 1)
      current_color.blend_towards(target_color, self.blend_progress[x][y], progress)
      self.blend_progress[x][y] = progress

  def state(self):
    return copy.deepcopy(self.current_state)

class RGBStripDriver:
  def __init__(self, view):
    self.view = view
    self.previous_state = self.view.state()
    for (x, y, ignored) in column_wise(self.previous_state):
      self.previous_state[x][y] = None

  def update(self, elapsed_time):
    for (x, y, color) in row_wise(self.view.state()):
      if color == self.previous_state[x][y]: continue

      # TODO issue command to extension board

      self.previous_state[x][y] = color

game = Game()
consoleView = ConsoleView(game)
colorView = ColorBlendingView(game)
driver = RGBStripDriver(colorView)


# TODO remove
random.seed(15)

colors = [Color()]

i = 0
last_update = time.time()
while True:
  try:
    if i % 3 == 0:
      x = random.randrange(6)
      y = 0 #random.randrange(10)
      b = Brick(random.choice(list(Shape)), random.choice(colors), x, y)
      b.gravity_affected = True
      game.place_brick(b)

    now = time.time()
    elapsed_time = now - last_update
    # TODO call at different rates (view faster than the game)
    game.update(elapsed_time)
    consoleView.update(elapsed_time)
    driver.update(elapsed_time)
    last_update = now

    time.sleep(0.5)
    i += 1
  except (KeyboardInterrupt, SystemExit):
    break