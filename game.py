import asyncio
import curses
import random
import time
from itertools import cycle

import curses_tools
from explosion import explode
from game_scenario import PHRASES, get_garbage_delay_tics
from obstacles import Obstacle
from physics import update_speed


TIC_TIMEOUT = 0.1
YEAR_START = 1957
YEARS_COUNT_SPEED = int(2 / TIC_TIMEOUT)
YEAR_PLASMA_GUN_INVENTED = 2022
STARS_AMOUNT = 50


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        await sleep((random.randint(0, 20)))

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


async def fire(
    canvas, start_row, start_column, rows_speed=-0.5, columns_speed=0
):

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep(1)

    canvas.addstr(round(row), round(column), 'O')
    await sleep(1)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await sleep(1)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed
        for obstacle in obstacles:
            if obstacle.has_collision(row, column, 1, 1):
                obstacles_in_last_collisions.append(obstacle)
                return


async def show_gameover(canvas):

    rows_number, columns_number = canvas.getmaxyx()
    height_gameover, width_gameover = curses_tools.get_frame_size(
        game_over_farme
    )
    row_gameover = rows_number // 2 - height_gameover // 2
    column_gameover = columns_number // 2 - width_gameover // 2

    while True:
        curses_tools.draw_frame(
            canvas, row_gameover, column_gameover, game_over_farme
        )
        await asyncio.sleep(0)


async def animate_spaceship(canvas, row, column, rocket_1, rocket_2):

    iterator = cycle([rocket_2, rocket_1, rocket_1, rocket_2])
    row_speed = column_speed = 0

    row_max, column_max = canvas.getmaxyx()
    frame_rows,  frame_columns = curses_tools.get_frame_size(rocket_1)
    row_limits = (1, row_max - frame_rows - 1)
    column_limits = (1, column_max - frame_columns - 1)

    for rocket in iterator:
        curses_tools.draw_frame(canvas, row, column, rocket, negative=True)
        rows_direction, columns_direction, space_pressed = curses_tools.read_controls(canvas)
        row_speed, column_speed = update_speed(
            row_speed, column_speed, rows_direction, columns_direction
        )

        if row >= max(row_limits) and row_speed >= 0 or row <= min(row_limits) and row_speed <= 0:
            row_speed = 0
        row = row + row_speed
    
        if column >= max(column_limits) and column_speed >= 0 or column <= min(column_limits) and column_speed <= 0:
            column_speed = 0
        column = column + column_speed

        if space_pressed and year > YEAR_PLASMA_GUN_INVENTED:
            coroutines.append(fire(canvas, row, column + 2))

        current_rocket = next(iterator)
        curses_tools.draw_frame(canvas, row, column, current_rocket)
        await sleep(1)

        for obstacle in obstacles:
            if obstacle.has_collision(row, column, frame_rows, frame_columns):
                obstacles_in_last_collisions.append(obstacle)
                curses_tools.draw_frame(canvas, row, column, current_rocket, negative=True)
                await explode(canvas, row, column)
                await show_gameover(canvas)
                return


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):

    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0
    rows_size, columns_size = curses_tools.get_frame_size(garbage_frame)

    obstacle = Obstacle(
        row=row,
        column=column,
        rows_size=rows_size,
        columns_size=columns_size
    )
    obstacles.append(obstacle)

    try:
        while obstacle.row < rows_number:
            if obstacle in obstacles_in_last_collisions:
                curses_tools.draw_frame(
                    canvas, obstacle.row, obstacle.column,
                    garbage_frame, negative=True
                )
                obstacles.remove(obstacle)
                obstacles_in_last_collisions.remove(obstacle)

                await explode(
                    canvas,
                    obstacle.row + rows_size//2,
                    obstacle.column + columns_size//2
                )
                return
            curses_tools.draw_frame(
                canvas, obstacle.row, obstacle.column, garbage_frame
            )
            await sleep(1)
            curses_tools.draw_frame(
                canvas, obstacle.row, obstacle.column,
                garbage_frame, negative=True
            )
            obstacle.row += speed
    finally:
        if obstacle in obstacles:
            obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas, garbage_frame):

    while True:
        if get_garbage_delay_tics(year):
            _, columns_number = canvas.getmaxyx()
            column = random.randint(1, columns_number)
            coroutines.append(
                fly_garbage(canvas, column, garbage_frame, speed=0.5)
            )
            await sleep(get_garbage_delay_tics(year))
        await asyncio.sleep(0)


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def count_years():
    global year
    year = YEAR_START
    while True:
        await sleep(YEARS_COUNT_SPEED)
        year += 1


async def show_win_info(canvas, info_frame):

    while True:
        if year in PHRASES:
            phrase = PHRASES[year]
        info_frame.clrtoeol()
        info_frame.addstr(0, 0, '{}: {}'.format(year, phrase))
        info_frame.noutrefresh()
        await asyncio.sleep(0)


def draw(canvas):

    curses.curs_set(False)
    canvas.nodelay(True)
    height, width = canvas.getmaxyx()

    global coroutines, obstacles, obstacles_in_last_collisions

    with open("animations/rocket_frame_1.txt", "r") as f:
        rocket_1 = f.read()
    with open("animations/rocket_frame_2.txt", "r") as f:
        rocket_2 = f.read()
    with open("animations/trash_xl.txt", "r") as garbage_file:
        garbage = garbage_file.read()

    info_frame = canvas.derwin(2, height-1, 1, 1)
    coroutines = [
        animate_spaceship(canvas, 0, 0, rocket_1, rocket_2),
        count_years(),
        show_win_info(canvas, info_frame),
        fill_orbit_with_garbage(canvas, garbage),
    ]

    obstacles = []
    obstacles_in_last_collisions = []

    for _ in range(STARS_AMOUNT):
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
        canvas.border()
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':

    with open("animations/game_over.txt", "r") as f:
        game_over_farme = f.read()

    curses.update_lines_cols()
    curses.wrapper(draw)
    
