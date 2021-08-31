import asyncio
import curses
import random
import time

from curses_tools import draw_frame


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


async def animate_spaceship(canvas, row, column, rocket_1, rocket_2):
    while True:
        draw_frame(canvas, row, column, rocket_2, negative=True)
        draw_frame(canvas, row, column, rocket_1)
        await asyncio.sleep(0)

        draw_frame(canvas, row, column, rocket_1, negative=True)
        draw_frame(canvas, row, column, rocket_2)
        await asyncio.sleep(0)


def draw(canvas):
    canvas.border()
    curses.curs_set(False)
    # TypeError: unbound method window.getmaxyx() needs an argument
    # height, width = curses.window.getmaxyx()
    height, width = 10, 79

    with open("animations/rocket_frame_1.txt", "r") as f:
        rocket_1 = f.read()
    with open("animations/rocket_frame_2.txt", "r") as f:
        rocket_2 = f.read()

    coroutines = [animate_spaceship(canvas, 10, 40, rocket_1, rocket_2)]

    stars_amount = 20
    for _ in range(stars_amount):
        row = random.randint(1, height)
        column = random.randint(1, width)
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
        canvas.refresh()
        TIC_TIMEOUT = 0.1
        time.sleep(TIC_TIMEOUT)

  
if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
