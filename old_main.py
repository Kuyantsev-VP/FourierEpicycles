from math import cos, sin
from geom import Point, Vector
import tkinter as tk
import numpy as np
from util import flat_it


# class FourierDrawer:
#     def __init__(self, root: tk.Tk, width, height):
#         self.root = root
#         self.width = width
#         self.height = height
#         self.canvas = tk.Canvas(root, width=width, height=height)
#         self.canvas.pack()
#
#     def _fourier(self, n, x0):
#         length = 6*n
#         res = [Point(0.,0.)] * length
#         # e^ix = cosx + i*sinx
#         x = 0
#         y = 0
#         for l in range(1, length):
#             if l % (2*n) == 0:
#                 l = 1
#             x += cos(2 + l * n) * x0
#             y += -sin(2 + l * n) * x0
#             coef = 1 / ((20 + n*l)**2)
#             res[l] = Point(x * coef, y * coef)
#         return res
#
#     def get_f_point(self, x0):
#         fur_vecs = self._fourier(3, x0)
#         p_cur = Point(0, 0)
#         points = []
#         for fur in fur_vecs:
#             points.append(p_cur)
#             p_new = Point(fur.x, fur.y)
#             # if with_vectors
#             #     self.canvas.create_line(p_cur.x, p_cur.y, p_new.x, p_new.y, arrow=tk.LAST)
#             p_cur = p_new
#         # self._put_point(p_cur)
#         return p_cur, points
#
#     def draw_fourier_curve(self, start, end, step=0.1, with_vectors=True):
#         num_points = int((end - start) / step) + 1
#         contour_ps = [Point(0, 0)] * num_points
#         fourier_ps_per_p = [[] for i in range(num_points)]
#         for i, x in enumerate(np.arange(start, end, step)):
#             p, ps = self.get_f_point(x)
#             contour_ps[i] = p
#             fourier_ps_per_p[i] = ps
#         if len(fourier_ps_per_p[1]) == 0:
#             a = 1
#         # if with_vectors:
#         #     x_range, y_range = self._bound_coordinates(fourier_ps_per_p)
#         # else:
#         #     x_range, y_range = self._bound_coordinates(contour_ps)
#         x_range, y_range = self._bound_coordinates(fourier_ps_per_p)
#
#         for i in range(len(fourier_ps_per_p)):
#             fourier_ps_per_p[i] = self._scale_coords(fourier_ps_per_p[i], x_range, y_range)
#         contour_ps = self._scale_coords(contour_ps, x_range, y_range)
#
#         vectors = None
#         for points_per_p in fourier_ps_per_p:
#             if len(points_per_p) == 0:
#                 continue
#             if with_vectors:
#                 self._delete_vectors(vectors)
#                 vectors = self._put_vector(points_per_p[2:])
#             self._put_point(points_per_p[-1], d=4)
#             self.canvas.after(100)
#             self.canvas.update()
#
#     def _delete_vectors(self, vs):
#         if vs is None:
#             return
#         for v in vs:
#             self.canvas.delete(v)
#
#     def _put_vector(self, v):
#         p_cur = v[0]
#         lines = []
#         for p_new in v[1:]:
#             line = self.canvas.create_line(p_cur.x, p_cur.y, p_new.x, p_new.y, arrow=tk.LAST)
#             self._put_point(p_new, d=1, color='black')
#             lines.append(line)
#             self.canvas.delete()
#             p_cur = p_new
#         return lines
#
#     def _put_point(self, p, color='red', d=2):
#         self.canvas.create_oval(p.x - d, p.y - d, p.x + d, p.y + d, fill=color)
#         # self.root.update()
#
#     def _scale_coords(self, coords, x_range, y_range):
#         # bounding points of picture
#         # TODO get rid of magic constant. Area of visualized graph depends on vertex size
#         min_abs_bp = Point(self.width * 0.1, self.height * 0.1)
#         max_abs_bp = Point(self.width * 0.9, self.height * 0.9)
#         # x_range, y_range = self._bound_coordinates(coords)
#         dx = (max_abs_bp.x - min_abs_bp.x) / x_range
#         dy = (max_abs_bp.y - min_abs_bp.y) / y_range
#         res = []
#         x0 = (max_abs_bp.x - min_abs_bp.x) / 2
#         y0 = (max_abs_bp.y - min_abs_bp.y) / 2
#         for vc in coords:
#             x = x0 + vc.x * dx
#             y = y0 + vc.y * dy
#             res.append(Point(x, y))
#         return res
#
#     def _bound_coordinates(self, coords):
#         min_x, min_y = min((c.x for c in flat_it(coords))), min((c.y for c in flat_it(coords)))
#         max_x, max_y = max((c.x for c in flat_it(coords))), max((c.y for c in flat_it(coords)))
#         # for c in coords
#         return max_x - min_x, max_y - min_y

from contour import Contour
from fourier import EpicycleChain1D, draw_point, combine_chains, EpicycleChain2D
import math


def get_data(file):
    res = []
    with open(file, 'r') as f:
        for line in f:
            x, y = line.split(', ')
            res.append(np.array([float(x), float(y)]))
    res = np.array(res)
    return res.T


def _points_between_generator(x1, y1, x2, y2, num_points):
    for inner_x, inner_y in zip(np.linspace(start=x1, stop=x2, num=num_points, endpoint=True),
                                np.linspace(start=y1, stop=y2, num=num_points, endpoint=True)):
        yield inner_x
        yield inner_y


def equilize_data(datas):
    max_data = None
    max_size = 0
    for data in datas:
        if data.shape[1] > max_size:
            max_data = data
            max_size = data.shape[1]
    datas.remove(max_data)
    new_datas = [max_data]
    for data in datas:

        new_data = []
        dif = max_size - data.shape[1]
        points_between_count = int(dif / data.shape[1]) + 1
        # data = data.T
        for i, point in enumerate(data.T[:-1]):
            next_point = data.T[i+1]
            points = np.array(list(_points_between_generator(point[0], point[1], next_point[0], next_point[1], points_between_count))).reshape(-1,2)
            for p in points:
                new_data.append([p[0], p[1]])
        points = np.array(list(_points_between_generator(data.T[-1][0], data.T[-1][1], data.T[0][0], data.T[0][1], points_between_count))).reshape(-1,2)
        for p in points:
            new_data.append([p[0], p[1]])
        while len(new_data) < max_data.shape[1]:
            new_data.append(new_data[-1])
        new_data = np.array(new_data).T
        new_datas.append(new_data)
    return new_datas



if __name__ == "__main__":
    canvas_width = 999
    canvas_height = 999

    # cont.smooth_edges(None)

    # contours = []
    # contours.append(Contour(canvas_width, canvas_height, pic_name="morosh.png", solid=True, step=3))
    # contours.append(Contour(canvas_width, canvas_height, pic_name="morosh.png", solid=True, step=3))
    # contours.append(Contour(canvas_width, canvas_height, pic_name="morosh.png", solid=True, step=3))


    root = tk.Tk()
    canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='black')
    canvas.pack()


    # signal_x = cont.x
    # signal_y = cont.y
    # chain_x = EpicycleChain1D(canvas, rotation=0, signal=signal_x, tag_name='ch_x', color='green')
    # chain_y = EpicycleChain1D(canvas, rotation=math.pi / 2, signal=signal_y, tag_name='ch_y', color='blue')
    # chain_xy = combine_chains(chain_x, chain_y, tag_name='ch_xy', color='orange')

    # Центр координат, оси
    x0, y0 = canvas_width / 2, canvas_height / 2
    # draw_point(canvas, x0, y0, r=5)
    # canvas.create_line(x0, 0, x0, canvas_height, fill='white')
    # canvas.create_line(0, y0, canvas_width, y0, fill='white')

    dump1 = get_data("291092-dump-contour0")
    dump2 = get_data("970014-dump-contour0")
    dump3 = get_data("66770-dump-contour0")
    datas = [dump1, dump2, dump3]
    datas = equilize_data(datas)

    t = 0
    dt = 2 * math.pi / datas[0].shape[1]
    line_x, line_y = None, None

    chains = [EpicycleChain2D(canvas, datas[0], tag_name='chain', color='orange'),
              EpicycleChain2D(canvas, datas[1], tag_name='chain', color='yellow'),
              EpicycleChain2D(canvas, datas[2], tag_name='chain', color='green')]


    first_time = True

    while t < 2 * math.pi:
        for chain in chains:
            v = chain.update_vectors_by_time(t)
            # v = chain.increase_time()
            chain.draw()

            draw_point(canvas, v.x, v.y, r=3, tag_name='point_tag', color='white')

        # line_x = canvas.create_line(vx.x, vx.y, vx.x, vy.y, fill='red')
        # line_y = canvas.create_line(vy.x, vy.y, vx.x, vy.y, fill='red')
        canvas.update()
        if first_time:
            input()
            first_time = False
            canvas.after(5000)

        # canvas.after(1)
        t += dt
        if t >= 2 * math.pi:
            canvas.after(1000)
            # canvas.delete('point_tag')
            t = 0
    canvas.after(1000)


