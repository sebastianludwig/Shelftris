import os

def relative_path(*segments):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), *segments)

def is_raspberry():
    return os.popen('uname').read() == 'Linux\n'

def array_2d(width, height):
    return [[None for _ in range(height)] for _ in range(width)]

def column_wise(container):
     for x_index, column in enumerate(container):
            for y_index, value in enumerate(column):
                yield (x_index, y_index, value)

def row_wise(container):
    row_wise = zip(*container)
    for y_index, row in enumerate(row_wise):
        for x_index, value in enumerate(row):
            yield (x_index, y_index, value)
