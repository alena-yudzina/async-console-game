import asyncio
import curses
import random
import time
from itertools import cycle

import curses_tools


def move_rocket(row, column, canvas, rows_direction, columns_direction, rocket_1):
    row_size, column_size = curses_tools.get_frame_size(rocket_1)
    height, width = canvas.getmaxyx()

    if row >= 0 and row + row_size <= height:
        row += rows_direction
    if row == -1:
        row = 1
    if row == height - row_size + 1:
        row = height - row_size - 1
    if column >= 0 and column + column_size <= width:
        column += columns_direction
    if column == -1:
        column = 1
    if column == width - column_size + 1:
        column = width - column_size - 1

    return(row, column)


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        for _ in range(random.randint(0, 20)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, row, column, rocket_1, rocket_2, width, height):
    iterator = cycle([rocket_2, rocket_1, rocket_1, rocket_2])

    for rocket in iterator:
        curses_tools.draw_frame(canvas, row, column, rocket, negative=True)
        rows_direction, columns_direction, space_pressed = curses_tools.read_controls(canvas)
        row, column = move_rocket(row, column, canvas, rows_direction, columns_direction, rocket_1)
        curses_tools.draw_frame(canvas, row, column, next(iterator))
        await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    height, width = canvas.getmaxyx()
    TIC_TIMEOUT = 0.1

    with open("animations/rocket_frame_1.txt", "r") as f:
        rocket_1 = f.read()
    with open("animations/rocket_frame_2.txt", "r") as f:
        rocket_2 = f.read()

    coroutines = [animate_spaceship(canvas, 0, 0, rocket_1, rocket_2, width, height)]

    stars_amount = 50
    for _ in range(stars_amount):
        row = random.randint(1, height - 1)
        column = random.randint(1, width - 1)
        symbol = random.choice(['*', '+', '.', ':'])
        coroutines.append(blink(canvas, row, column, symbol=symbol))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break
        canvas.border()
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
