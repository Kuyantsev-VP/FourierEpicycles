from typing import Iterable
from PIL import ImageGrab
import tkinter as tk
from tkinter import colorchooser, simpledialog

INF = float('inf')


def to_float(arr):
    return [float(x) for x in arr]


def to_int(arr):
    return [int(x) for x in arr]


def dist(coords_a, coords_b):
    assert len(coords_b) == len(coords_a), "Vectors of different length"
    return sum(((coords_a[i] - coords_b[i]) ** 2 for i in range(len(coords_a)))) ** (1 / 2)


def flat_it(sequence: Iterable):
    for smth in sequence:
        try:
            it = iter(smth)
            if type(smth) == str:
                for char in smth:
                    yield char
                continue
        except TypeError:
            yield smth
            continue
        for el in flat_it(it):
            yield el


def choose_color_dialog():
    return colorchooser.askcolor()[1]


def ask_string(title, prompt, initialvalue='', parent=None):
    return simpledialog.askstring(title=title, prompt=prompt, initialvalue=initialvalue, parent=parent)
    pass


def getter(root, widget, file_path):
    x = root.winfo_rootx()+widget.winfo_x()
    y = root.winfo_rooty()+widget.winfo_y()
    x1 = x+widget.winfo_width()
    y1 = y+widget.winfo_height()
    ImageGrab.grab().crop((x, y, x1, y1)).save(file_path)


def draw_point(canvas, x, y, r=0.5, color='black', tag_name=''):
    return canvas.create_oval(x - r, y - r, x + r, y + r, tag=tag_name, fill=color, outline=color)


def draw_outlined_point(canvas, x, y, r=0.5, color='black', outline_color='black', tag_name='', **kwargs):
    return canvas.create_oval(x - r, y - r, x + r, y + r, tag=tag_name, fill=color, outline=outline_color, **kwargs)

