#!/usr/bin/env python3
# TERMINAL_MODE
import curses
import random
import time
import math

# Переменные для настройки
SYMBOL_SET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*+-=[]{}|;:,.<>?/~│_─▔╴╵╶╷╌╎⌜⌝⌞⌟┌┐┘└╭╮╯╰┴┬⊺├┤┼⌈⌉⌊⌋"
HEAD_COLOR = "white"   # Цвет головы
TAIL_GRADIENT_COLORS = ["cyan", "magenta", "magenta"]
# Список цветов для градиента хвоста: "green" — зелёный, "red" — красный, "blue" — синий, "yellow" — жёлтый, "white" — белый, "cyan" — голубой, "magenta" — пурпурный
SYMBOL_FALL_SPEED = 0.125  # Базовая скорость падения символов (строки за кадр)
FADE_SPEED = 0.125  # Скорость затухания символов
FRAME_RATE = 20  # Частота обновления экрана (кадров в секунду)
TAIL_LENGTH_MIN = 5   # Минимальная длина хвоста колонки
TAIL_LENGTH_MAX = 34  # Максимальная длина хвоста колонки
FADE_STEPS = 256  # Максимальное количество шагов затухания символов
BOTTOM_FADE_BOOST = 1.0  # Коэффициент ускорения затухания внизу экрана
CHAR_CHANGE_RATE = 0.05  # Вероятность смены символа в хвосте
COLUMN_DENSITY = 0.6  # Доля ширины экрана, заполненная колонками
SYMBOL_BRIGHTNESS = 0.5  # Яркость символов (влияет на A_BOLD, A_NORMAL, A_DIM)
TAIL_FADE_CURVE = 0.7  # Кривая затухания хвоста
RANDOM_RESET_CHANCE = 0.002  # Вероятность случайного сброса колонки
PAUSE_DURATION = 0.0  # Время паузы колонок после сброса
BACKGROUND_CHAR = ' '  # Символ фона
SYMBOL_DIVERSITY = 1.0  # Доля символов из SYMBOL_SET
MOVEMENT_VARIATION = 0.05  # Диапазон отклонения скорости
PULSE_RATE = 0.3  # Частота пульсации яркости
SCREEN_FILL_RATE = 0.0  # Доля экрана, заполненная при старте
PROGRESS_FILLED_CHAR = '│'  # Символ для головы колонок
TEXT_PULSE_AMPLITUDE = 0.0  # Амплитуда пульсации яркости
EMOTION_INTENSITY = 0.6  # Интенсивность анимации

CHARS = list(SYMBOL_SET)[:int(len(SYMBOL_SET) * SYMBOL_DIVERSITY)]

class MatrixColumn:
    def __init__(self, max_y):
        self.max_y = max_y
        self.pos = random.randint(0, max_y - 1)
        self.speed = SYMBOL_FALL_SPEED + random.uniform(-MOVEMENT_VARIATION, MOVEMENT_VARIATION)
        self.tail_length = random.randint(TAIL_LENGTH_MIN, TAIL_LENGTH_MAX)
        self.pos_float = float(self.pos)
        self.tail_chars = [random.choice(CHARS) for _ in range(self.tail_length)]
        self.paused = PAUSE_DURATION > 0
        self.pause_time = time.time() if self.paused else 0

    def update(self, x, buffer, dirty_positions, color_pairs):
        if self.paused:
            if time.time() - self.pause_time >= PAUSE_DURATION:
                self.paused = False
            return

        self.pos_float += self.speed * EMOTION_INTENSITY
        new_pos = int(self.pos_float)

        if new_pos > self.max_y + self.tail_length or random.random() < RANDOM_RESET_CHANCE:
            for offset in range(self.tail_length):
                y = int(self.pos - offset)
                if 0 <= y < self.max_y and buffer[y][x][0] != BACKGROUND_CHAR:
                    buffer[y][x] = (BACKGROUND_CHAR, curses.color_pair(0), 0.0)
                    dirty_positions.add((y, x))
            self.pos = 0
            self.pos_float = 0.0
            self.tail_length = random.randint(TAIL_LENGTH_MIN, TAIL_LENGTH_MAX)
            self.tail_chars = [random.choice(CHARS) for _ in range(self.tail_length)]
            self.paused = PAUSE_DURATION > 0
            self.pause_time = time.time() if self.paused else 0
        else:
            old_tail_y = int(self.pos - self.tail_length)
            new_tail_y = new_pos - self.tail_length
            if 0 <= old_tail_y < self.max_y and old_tail_y < new_tail_y and buffer[old_tail_y][x][0] != BACKGROUND_CHAR:
                buffer[old_tail_y][x] = (BACKGROUND_CHAR, curses.color_pair(0), 0.0)
                dirty_positions.add((old_tail_y, x))

        self.pos = new_pos
        for i in range(self.tail_length):
            if random.random() < CHAR_CHANGE_RATE:
                self.tail_chars[i] = random.choice(CHARS)

        for offset in range(self.tail_length):
            y = self.pos - offset
            if 0 <= y < self.max_y:
                char = self.tail_chars[offset] if offset > 0 else PROGRESS_FILLED_CHAR
                fade_level = FADE_STEPS * (1 - (offset / self.tail_length) ** TAIL_FADE_CURVE)
                # Градиент цвета для хвоста
                if offset == 0:
                    attr = curses.A_BOLD | curses.color_pair(1)  # Голова
                else:
                    gradient_step = min(offset / (self.tail_length - 1), 1.0) if self.tail_length > 1 else 0
                    color_index = int(gradient_step * (len(color_pairs) - 2)) + 2  # Пропускаем пару 0 и 1
                    attr = curses.A_NORMAL | curses.color_pair(color_index)
                    if SYMBOL_BRIGHTNESS < 0.5 and offset > self.tail_length // 2:
                        attr = curses.A_DIM | curses.color_pair(color_index)
                if buffer[y][x] != (char, attr, fade_level):
                    buffer[y][x] = (char, attr, fade_level)
                    dirty_positions.add((y, x))

def main(stdscr):
    curses.curs_set(0)
    stdscr.timeout(0)
    
    # Инициализация цветов
    curses.start_color()
    curses.use_default_colors()
    color_map = {
        "green": curses.COLOR_GREEN, "red": curses.COLOR_RED, "blue": curses.COLOR_BLUE,
        "yellow": curses.COLOR_YELLOW, "white": curses.COLOR_WHITE, "cyan": curses.COLOR_CYAN,
        "magenta": curses.COLOR_MAGENTA
    }
    head_color = color_map.get(HEAD_COLOR.lower(), curses.COLOR_WHITE)
    curses.init_pair(1, head_color, -1)  # Цвет головы
    # Инициализация градиента цветов для хвоста
    tail_colors = [color_map.get(c.lower(), curses.COLOR_YELLOW) for c in TAIL_GRADIENT_COLORS]
    color_pairs = [1]  # Начальная пара для головы
    for i, color in enumerate(tail_colors, start=2):
        curses.init_pair(i, color, -1)
        color_pairs.append(i)
    stdscr.bkgd(BACKGROUND_CHAR, curses.color_pair(0))

    max_y, max_x = stdscr.getmaxyx()
    num_columns = int(max_x * COLUMN_DENSITY)
    columns = [MatrixColumn(max_y) for _ in range(num_columns)]
    buffer = [[(BACKGROUND_CHAR, curses.color_pair(0), 0.0) for _ in range(max_x)] for _ in range(max_y)]
    dirty_positions = set()

    if SCREEN_FILL_RATE > 0:
        for y in range(max_y):
            for x in range(max_x):
                if random.random() < SCREEN_FILL_RATE:
                    stdscr.addch(y, x, random.choice(CHARS), curses.A_DIM | curses.color_pair(2))
        stdscr.refresh()
        time.sleep(0.01)

    pulse_time = time.time()
    while True:
        current_max_y, current_max_x = stdscr.getmaxyx()
        if current_max_y != max_y or current_max_x != max_x:
            max_y, max_x = current_max_y, current_max_x
            num_columns = int(max_x * COLUMN_DENSITY)
            columns = [MatrixColumn(max_y) for _ in range(num_columns)]
            buffer = [[(BACKGROUND_CHAR, curses.color_pair(0), 0.0) for _ in range(max_x)] for _ in range(max_y)]
            stdscr.clear()
            dirty_positions.clear()

        pulse_factor = 1.0
        if PULSE_RATE > 0:
            pulse_factor = 1.0 + TEXT_PULSE_AMPLITUDE * math.sin(2 * math.pi * PULSE_RATE * (time.time() - pulse_time))

        for y in range(max_y):
            for x in range(max_x):
                char, attr, fade_level = buffer[y][x]
                if fade_level > 0:
                    fade_factor = FADE_SPEED * (1 + BOTTOM_FADE_BOOST * (y / max_y)) * pulse_factor
                    new_fade_level = max(fade_level - fade_factor * EMOTION_INTENSITY, 0)
                    if new_fade_level != fade_level:
                        if new_fade_level == 0:
                            buffer[y][x] = (BACKGROUND_CHAR, curses.color_pair(0), 0.0)
                        else:
                            buffer[y][x] = (char, attr, new_fade_level)
                        dirty_positions.add((y, x))

        for i, col in enumerate(columns):
            col.max_y = max_y
            x = i * (max_x - 1) // (num_columns - 1) if num_columns > 1 else 0
            col.update(x, buffer, dirty_positions, color_pairs)

        for y, x in dirty_positions:
            char, attr, fade_level = buffer[y][x]
            try:
                if fade_level > FADE_STEPS * 0.8:
                    stdscr.addch(y, x, char, curses.A_BOLD | attr)
                elif fade_level > FADE_STEPS * 0.6:
                    stdscr.addch(y, x, char, curses.A_NORMAL | attr)
                else:
                    stdscr.addch(y, x, char, curses.A_DIM | attr)
            except curses.error:
                pass
        dirty_positions.clear()

        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break

        time.sleep(1 / FRAME_RATE)

if __name__ == "__main__":
    curses.wrapper(main)
