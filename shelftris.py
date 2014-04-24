import time
import copy
import random
from enum import Enum

class Square:
  def __init__(self, color):
    self.color = color
  
  def __str__(self):
    return self.color[0]

class Shape(Enum):
   T = [[True, None], [True, True], [True, None]]
   O = [[True, True], [True, True]]
   I = [[True, True, True, True]]
   J = [[True, None, None], [True, True, True]]
   L = [[True, True, True], [None, None, True]]
   Z = [[True, None], [True, True], [None, True]]
   S = [[None, True], [True, True], [True, None]]
   

class Brick:
  def __init__(self, shape, color, x, y):
    self.position = (x, y)
    self.gravity_affected = True
    self.pattern = copy.deepcopy(shape.value)
    for x_index, column in enumerate(self.pattern):
      for y_index, value in enumerate(column):
        if value is None: continue
        self.pattern[x_index][y_index] = Square(color)
    
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
  
  def __str__(self):
    row_wise = zip(*self.pattern)
    s = ''
    for y, row in enumerate(row_wise):
      for x, value in enumerate(row):
        s += str(value) if value is not None else ' '
      s += '\n'
    return s
  
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
  
  def can_move(self, brick, new_position):
    if (new_position[0] < 0 or
        new_position[0] + brick.width  > self.width or
        new_position[1] + brick.height > self.height):
      return False
    for x, column in enumerate(brick.pattern):
      for y, value in enumerate(column):
        if value is None: continue
        if self.field[new_position[0] + x][new_position[1] + y] is not None: return False
    return True
  
  def __str__(self):
    row_wise = zip(*self.field)
    s = ''
    for y, row in enumerate(row_wise):
      for x, value in enumerate(row):
        s += str(value) if value is not None else ' '
      s += '\n'
    return s
  
  def merge(self, brick):
    # transfer brick.pattern to field
    for x, column in enumerate(brick.pattern):
      for y, value in enumerate(column):
        if value is None: continue
        if brick.x + x < 0 or brick.x + x > self.width: continue
        if brick.y + y < 0 or brick.y + y > self.height: continue
        self.field[brick.x + x][brick.y + y] = value
    pass

class Shelftris:
  def __init__(self):
    self.field = Field(9, 14)
    self.bricks = []
  
  def update(self):
    for brick in self.bricks:
      new_position = (brick.x, brick.y +1)
      if self.field.can_move(brick, new_position):
        brick.position = new_position
      else:
        self.field.merge(brick)
        self.bricks.remove(brick)
    
  def place_brick(self, brick):
    if brick.gravity_affected:
      self.bricks.append(brick)
    else:
      self.field.merge(brick)



game = Shelftris()

colors = ['r', 'g', 'b', 'y']

# b = Brick(Shape.T, 'r', 5, 7)
# b.gravity_affected = False
# game.place_brick(b)
# 
# exit()

i = 0
while True:
  try:
    if i % 3 == 0:
      x = random.randrange(6)
      y = random.randrange(10)
      b = Brick(random.choice(list(Shape)), random.choice(colors), x, y)
      b.gravity_affected = True
      game.place_brick(b)
    game.update()
    print game.field
    time.sleep(0.5)
    i += 1
  except (KeyboardInterrupt, SystemExit):
    break