import math
import tkinter as tk
import uuid
from typing import List

import numpy as np

from Geom import Point, Vector
from scipy.interpolate import interp1d
from datetime import datetime
from PIL import Image, ImageTk

def empty_func(event):
    pass


class Contour:
    def __init__(self, w, h, pic_name=None, root=None, canvas=None, data=None, solid=True, step=1, number=0):
        self.root = root
        self.canvas = canvas
        self.number = number

        self.d = 5
        self.uid = uuid.uuid1()

        self.w = w
        self.h = h
        self.x0 = w / 2
        self.y0 = h / 2
        if data is None:
            data = []
            self._init_contour_on_canvas(data, pic_name)
            # TODO bring reshaping here
            if solid:
                self.edges = np.array(data).reshape(-1, 2).T
                data = self._complete_with_points_between(data, step)
            data = np.array(data).reshape(-1, 2).T
            data[0] = data[0] - self.x0
            data[1] = data[1] - self.y0
        self.data = data
        self.x = self.data[0, :]
        self.y = self.data[1, :]
        self.dump()

    def size(self):
        return self.data.shape[1]

    def dump(self):
        now = datetime.now().microsecond
        # datetime.time()
        with open(f"{str(now)}-dump-contour{self.number}", 'w') as out:
            for i in range(self.data.shape[1]):
                out.write(f"{self.data[0, i]}, {self.data[1, i]}\n")

    def smooth_edges(self, interp_radius, *args, **kwargs):
        pass

    def _complete_with_points_between(self, data, step):
        assert len(data) % 2 == 0
        if len(data) <= 2:
            return data
        res_data = []
        x_prev, y_prev = data[0], data[1]
        for x, y in zip(data[2:-1:2], data[3::2]):
            res_data.extend(self._points_between_generator(x_prev, y_prev, x, y, step))
            x_prev, y_prev = x, y
        res_data.extend(self._points_between_generator(x_prev, y_prev, data[0], data[1], step))
        return res_data

    def _points_between_generator(self, x1, y1, x2, y2, step):
        x_delta, y_delta = abs(x2 - x1), abs(y2 - y1)
        length = math.sqrt(x_delta * x_delta + y_delta * y_delta)
        num_points = int(length / step)
        for inner_x, inner_y in zip(np.linspace(start=x1, stop=x2, num=num_points, endpoint=True),
                                    np.linspace(start=y1, stop=y2, num=num_points, endpoint=True)):
            yield inner_x
            yield inner_y

    def _init_contour_on_canvas(self, init_data, pic_name=None):
        # init_root = tk.Tk()
        # init_canvas = tk.Canvas(init_root, width=self.w, height=self.h)
        # init_canvas.pack()

        init_root = tk.Tk()
        init_root.geometry('1000x1000')
        init_canvas = tk.Canvas(init_root, width=999, height=999)
        init_canvas.pack()
        pilImage = Image.open(pic_name)
        image = ImageTk.PhotoImage(pilImage)
        imagesprite = init_canvas.create_image(500, 500, image=image)
        init_canvas.pack()

        c = init_canvas

        d = self.d
        uid = self.uid
        last = None
        polygon = None

        def refresh_polygon():
            nonlocal polygon
            if polygon:
                c.delete(polygon)
            polygon = c.create_polygon(*init_data, fill='', outline='black', tag='mark_' + str(uid))

        def create_contour_point(event):
            nonlocal last
            nonlocal self
            nonlocal polygon
            x = event.x
            y = event.y
            last = c.create_oval(x - d, y - d, x + d, y + d, fill='green', tag='mark_' + str(uid))
            init_data.append(x)
            init_data.append(y)
            refresh_polygon()
            c.bind("<Button-1>", empty_func)

        def replace_last_contour_point(event):
            nonlocal last
            nonlocal self
            nonlocal polygon
            x = event.x
            y = event.y
            init_data[-2] = x
            init_data[-1] = y
            c.coords(last, x - d, y - d, x + d, y + d)
            refresh_polygon()
            c.bind("<Button-3>", empty_func)

        def add_contour_point(event):
            c.bind('<Button-1>', create_contour_point)

        def replace_last(event):
            c.bind('<Button-3>', replace_last_contour_point)

        def finish_contour(event):
            init_root.destroy()

        b_add = tk.Button(init_root, text='add point')
        b_add.bind("<Button-1>", add_contour_point)
        b_add.pack(side='top')

        b_replace = tk.Button(init_root, text='replace last point')
        b_replace.bind("<Button-1>", replace_last)
        b_replace.pack(side='bottom')

        b_finish = tk.Button(init_root, text='finish')
        b_finish.bind("<Button-1>", finish_contour)
        b_finish.pack(side='top')

        init_root.bind("<Button-1>", create_contour_point)
        init_root.bind("<Button-3>", replace_last_contour_point)
        init_root.bind("a", add_contour_point)
        init_root.bind("e", finish_contour)

        init_root.mainloop()


class FourierApproxVector:
    def __init__(self, re, im, freq, amp, phase):
        self.re = re
        self.im = im
        self.freq = freq
        self.amp = amp
        self.phase = phase


class EpicycleChain1D:
    def __init__(self, canvas, rotation, signal=None, drawing=True, tag_name='', color='black'):
        self.canvas = canvas
        self.tag_name = tag_name
        # self.drawing = drawing
        self.rotation = rotation

        self.fourier_vectors = None
        if signal is not None:
            self.fourier_vectors = self.dft(signal)
            self.num_vectors = len(self.fourier_vectors)
            self._init_epicycles(color)
        self.width = canvas['width']
        self.height = canvas['height']
        self.x0 = int(self.width) / 2
        self.y0 = int(self.height) / 2

    def _init_epicycles(self, color):
        c = self.canvas
        self.epicycles = [(c.create_line(0, 0, 0, 0, tag=self.tag_name, fill=color),  #, activefill=color, arrow=tk.LAST, arrowshape="10 20 10"
                          c.create_oval(0, 0, 0, 0, tag=self.tag_name, outline=color, width=2)) for i in range(self.num_vectors)]
        self.vectors = [Vector(Point(0,0), Point(0,0)) for i in range(self.num_vectors)]

    def update_vectors_by_time(self, time):
        x_prev, y_prev = self.x0, self.y0
        j = 0
        for f_vec in sorted(self.fourier_vectors, key=lambda i: i.amp, reverse=True):
        # for f_vec in self.fourier_vectors:
            rad = f_vec.amp
            x_cur = x_prev + rad * math.cos(time * f_vec.freq + f_vec.phase + self.rotation)
            y_cur = y_prev + rad * math.sin(time * f_vec.freq + f_vec.phase + self.rotation)
            self.vectors[j] = Vector(Point(x_prev, y_prev), Point(x_cur, y_cur))
            x_prev, y_prev = x_cur, y_cur
            j += 1
        # return last point of chain
        return Point(x_cur, y_cur)

    def update_vectors(self, vectors):
        assert self.num_vectors == len(vectors)
        for i in range(self.num_vectors):
            self.vectors[i] = vectors[i]
        return self.vectors[-1].p_to

    def draw(self):
        for i in range(self.num_vectors):
            vector = self.vectors[i]
            epi = self.epicycles[i]

            from_x, from_y, to_x, to_y = list(vector.get_iter())
            rad = vector.norm()
            self.canvas.coords(epi[0], from_x, from_y, to_x, to_y)  # line
            self.canvas.coords(epi[1], from_x - rad, from_y - rad, from_x + rad, from_y + rad) # circle
        # return last point of chain
        return Point(to_x, to_y)

    def dft(self, signal):
        assert len(signal.shape) == 1 or signal.shape[0] == 1
        N = len(signal)
        X = []

        for k in range(0, N):
            re = 0
            im = 0
            for n in range(N):
                phi = 2 * math.pi * k * n / N
                re += signal[n] * math.cos(phi)
                im -= signal[n] * math.sin(phi)
            re = re / N
            im = im / N
            freq = k
            amp = math.sqrt(re * re + im * im)
            phase = math.atan2(im, re)
            X.append(FourierApproxVector(re, im, freq, amp, phase))
        return X


class EpicycleChain2D:
    def __init__(self, canvas, signal, tag_name='', color='orange'):
        signal_x = signal[0, :]
        signal_y = signal[1, :]
        self.color = color
        self.chain_x = EpicycleChain1D(canvas, rotation=0, signal=signal_x, tag_name=tag_name+'|ch_x', color='green')
        self.chain_y = EpicycleChain1D(canvas, rotation=math.pi / 2, signal=signal_y, tag_name=tag_name+'|ch_y', color='blue')
        self.chain_xy = combine_chains(self.chain_x, self.chain_y, tag_name='ch_xy', color=self.color)
        self.t = 0
        self.dt = 2*math.pi / signal.shape[1]

    def increase_time(self):
        self.t += self.dt
        v = self.update_vectors_by_time(self.t)
        if self.t >= 2 * math.pi:
            self.t=0
        return v

    def update_vectors_by_time(self, t):
        vx = self.chain_x.update_vectors_by_time(t)
        vy = self.chain_y.update_vectors_by_time(t)
        v = self.chain_xy.update_vectors(merge_vectors(self.chain_x.vectors, self.chain_y.vectors))
        return v

    def draw(self):
        for i in range(self.chain_xy.num_vectors):
            vector = self.chain_xy.vectors[i]
            epi = self.chain_xy.epicycles[i]

            x_from, y_from, x_to, y_to = list(vector.get_iter())
            rad = vector.norm()
            self.chain_xy.canvas.coords(epi[0], x_from, y_from, x_to, y_to)  # line
            arrow_length = rad / 10
            self.chain_xy.canvas.itemconfig(epi[0], activefill=self.color, arrow=tk.LAST, arrowshape=f"{arrow_length/2} {arrow_length} {arrow_length/4}")
            self.chain_xy.canvas.coords(epi[1], x_from - rad, y_from - rad, x_from + rad, y_from + rad) # circle
        # return last point of chain
        return Point(x_to, y_to)


def draw_point(canvas, x, y, r=0.5, color='black', tag_name=''):
    return canvas.create_oval(x - r, y - r, x + r, y + r, tag=tag_name, fill=color, outline=color)


def combine_chains(chain1: EpicycleChain1D, chain2: EpicycleChain1D, tag_name, color='black'):
    assert chain1.canvas == chain2.canvas
    assert chain1.num_vectors == chain2.num_vectors
    rotation = (chain1.rotation + chain2.rotation) / 2
    result = EpicycleChain1D(chain1.canvas, rotation, tag_name=tag_name)

    N = chain1.num_vectors
    c = result.canvas

    result.vectors = [Vector(Point(0,0), Point(0,0)) for i in range(N)]
    result.epicycles = [(c.create_line(0, 0, 0, 0, tag=tag_name, fill=color),  # , arrow=tk.LAST),
                       c.create_oval(0, 0, 0, 0, tag=tag_name, outline=color)) for i in range(N)]

    for i in range(N):
        result.vectors[i] = chain1.vectors[i] + chain2.vectors[i]
    result.num_vectors = N
    return result

def merge_vectors(vectors1, vectors2):
    assert vectors1[0].p_from == vectors2[0].p_from
    assert len(vectors1) == len(vectors2)
    vectors = []
    x_prev, y_prev = list(vectors1[0].p_from.get_iter())
    for i in range(len(vectors1)):
        rel_vec1 = (vectors1[i].p_to[0] - vectors1[i].p_from[0], vectors1[i].p_to[1] - vectors1[i].p_from[1])
        rel_vec2 = (vectors2[i].p_to[0] - vectors2[i].p_from[0], vectors2[i].p_to[1] - vectors2[i].p_from[1])
        rel_vec = rel_vec1[0] + rel_vec2[0], rel_vec1[1] + rel_vec2[1]
        x_cur, y_cur = x_prev + rel_vec[0], y_prev + rel_vec[1]
        vectors.append(Vector(Point(x_prev, y_prev), Point(x_cur, y_cur)))
        x_prev, y_prev = x_cur, y_cur
    return vectors

# def dft(signal):
#     assert len(signal.shape) == 1 or signal.shape[0] == 1
#     N = len(signal)
#     X = []
#
#     for k in range(0, N):
#         re = 0
#         im = 0
#         for n in range(N):
#             phi = 2 * math.pi * k * n / N
#             re += signal[n] * math.cos(phi)
#             im -= signal[n] * math.sin(phi)
#         re = re / N
#         im = im / N
#         freq = k
#         amp = math.sqrt(re * re + im * im)
#         phase = math.atan2(im, re)
#         X.append(FourierApproxVector(re, im, freq, amp, phase))
#     return X
#
#
# def draw_epicycles(x0, y0, time, fourier: List[FourierApproxVector], canvas, tag_name, draw=True, rot=0., mod=1.,
#                    color='black'):
#     assert len(fourier) > 0
#     x_prev, y_prev = x0, y0
#
#     for epi in sorted(fourier, key=lambda i: i.amp, reverse=True):
#         rad = epi.amp * mod  # !!!
#         x_cur = x_prev + rad * math.cos(time * epi.freq + epi.phase + rot)
#         y_cur = y_prev + rad * math.sin(time * epi.freq + epi.phase + rot)
#         if draw:
#             line = canvas.create_line(x_prev, y_prev, x_cur, y_cur, tag=tag_name, fill=color)
#             circ_rad = rad
#             circle = canvas.create_oval(x_prev - circ_rad, y_prev - circ_rad, x_prev + circ_rad, y_prev + circ_rad,
#                                         tag=tag_name)
#         x_prev, y_prev = x_cur, y_cur
#     return Point(x_cur, y_cur)




# canvas_width = 600
# canvas_height = 600
#
# # TODO сделать для 1-мерного случая, как в примере, чтобы проверить, что все адекватно
# # signal = np.array([-1, 1, -1, 1, -1, 1])
# # signal = np.array([x*x for x in np.arange(0, 1, 0.1)])
# # signal = np.array([-1, 2, -3, 4, -5, 6])
# # signal_x = np.array([1, 1, -1, -1]) * 100
# signal_x = np.array([0, 0, 0, 0]) * 100
# signal_y = np.array([-1, -1, 1, 1]) * 100
# assert len(signal_x) == len(signal_y)
#
# cont = Contour(canvas_width, canvas_height, solid=True, step=1)
# print(cont.data)
# # cont.data = cont.data[:, ::7]
# signal_x = cont.data[0, :]
# signal_y = cont.data[1, :]
# fourier_x = dft(signal_x)
# fourier_y = dft(signal_y)
#
# root = tk.Tk()
# canvas = tk.Canvas(root, width=canvas_width, height=canvas_height)
# canvas.pack()
#
# # Центр координат, оси
# x0, y0 = canvas_width / 2, canvas_height / 2
# draw_point(canvas, x0, y0, r=5)
# canvas.create_line(x0, 0, x0, canvas_height)
# canvas.create_line(0, y0, canvas_width, y0)
# # for t in np.arange(0, 2 * math.pi, 0.01):
# # for t in np.arange(2 * math.pi, 0, -0.01):
#
# # Главный цикл
# t = 0
# dt = 2 * math.pi / len(fourier_x)
# line_x, line_y = None, None
# while t < 2 * math.pi:
#     vx = draw_epicycles(x0, y0, t, fourier_x, canvas, 'tag', rot=0, draw=True, color='green')
#     vy = draw_epicycles(x0, y0, t, fourier_y, canvas, 'tag', rot=math.pi / 2, color='blue')
#     draw_point(canvas, vx.x, vy.y, r=1, tag_name='point_tag', color='red')
#     line_x = canvas.create_line(vx.x, vx.y, vx.x, vy.y, fill='red')
#     line_y = canvas.create_line(vy.x, vy.y, vx.x, vy.y, fill='red')
#     canvas.update()
#     canvas.after(50)
#     canvas.delete('tag')
#     canvas.delete(line_x)
#     canvas.delete(line_y)
#     # draw_point(canvas, x0+t, y, 'red')
#     # draw_point(canvas, x, y0+t, 'red')
#     canvas.update()
#     t += dt
#     # t += 0.01
#     if t >= 2 * math.pi:
#         canvas.after(1000)
#         canvas.delete('point_tag')
#         t = 0
# canvas.after(1000)
#
# root.mainloop()
