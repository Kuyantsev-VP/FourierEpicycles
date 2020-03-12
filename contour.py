import uuid
from datetime import datetime
import numpy as np
from scipy.interpolate import interp1d
from PIL import Image, ImageTk
import math
import tkinter as tk
import os
import itertools

from util import choose_color_dialog, ask_string


from tkinter import colorchooser, simpledialog


class Contour:
    def __init__(self, pil_image=None, dump_file=None, name=None):
        self.d = 7

        if name is None:
            self.name = str(uuid.uuid1())
        else:
            self.name = name

        # self.pil_image = pil_image

        assert pil_image is not None or dump_file is not None, \
            "Can't create contour. No image or dump file was specified."

        default_color = 'white'
        self.color = default_color
        self.epicycle_color = default_color
        self.filled = False

        if dump_file:
            with open(dump_file, 'r') as f:
                w = int(f.readline().strip())
                h = int(f.readline().strip())

                if pil_image:
                    image = ImageTk.PhotoImage(pil_image)
                    image_w = image.width()
                    image_h = image.height()
                    # TODO use warning window instead of assert here
                    assert w == image_w and h == image_h, f"Provided image shape does not correspond to dump file. " \
                                                          f"Image shape: ({image_w},{image_h}). " \
                                                          f"Shape specified in file: ({w},{h})"
                self.data = []
                for line in f:
                    if len(line) == 0:
                        continue
                    x, y = line.split()
                    self.data.append([float(x), float(y)])
                self.data = np.array(self.data)
                return

        if pil_image:

            self.image = ImageTk.PhotoImage(pil_image)
            self.w = self.image.width()
            self.h = self.image.height()

            # self.x0 = self.w / 2
            # self.y0 = self.h / 2

            data = []
            self._init_contour_on_canvas(data)

            data = np.array(data).reshape(-1, 2)
            self.edges_count = data.shape[0]
            # data[0] = data[0] - self.x0
            # data[1] = data[1] - self.y0
            self.data = data
            # self.x = self.data[:, 0]
            # self.y = self.data[:, 1]

        # self.dump()

    def size(self):
        return self.data.shape[0]

    def get_polygon_array(self):
        return self.data.ravel()

    def dump(self, path):
        # TODO делать дамп имени, цветов и угловых точек (в формате как в яндекс-контестах: число точек, точки)
        with open(os.path.join(path, self.name + '.contour'), 'w') as out:
            out.write(f"{self.w}\n{self.h}\n")
            for row in self.data:
                out.write(f"{row[0]} {row[1]}\n")

    # def dump(self):
    #     now = datetime.now().microsecond
    #     # datetime.time()
    #     with open(f"{str(now)}-dump-contour{self.number}", 'w') as out:
    #         for i in range(self.data.shape[1]):
    #             out.write(f"{self.data[0, i]}, {self.data[1, i]}\n")

    def smooth_edges(self, interp_radius, *args, **kwargs):
        pass

    def fill_with_points_between(self, step=1):
        if self.filled:
            return
        data = self.data
        # assert len(data) % 2 == 0
        if len(data) <= 2:
            return
        res_data = []
        x_prev, y_prev = data[0][0], data[0][1]
        for x, y in data[1:]:
            res_data.extend(self._points_between_generator(x_prev, y_prev, x, y, step))
            x_prev, y_prev = x, y
        res_data.extend(self._points_between_generator(x_prev, y_prev, data[0][0], data[0][1], step))
        self.data = np.array(res_data)
        self.filled = True

    def get_aligning_mask(self, total_point_count):
        points_to_add_count = total_point_count - self.size()
        relation = points_to_add_count / self.size()
        points_per_interval = 1 + points_to_add_count // self.size()
        additional_points_relation = relation - points_to_add_count // self.size()

        if additional_points_relation == 0:
            return [points_per_interval]
        mask_size = 1
        ones_fraction = float(additional_points_relation)
        while abs(ones_fraction - round(ones_fraction)) > 0.05 and mask_size < self.size() - 1:
            mask_size += 1
            ones_fraction = additional_points_relation * mask_size
        ones_count = round(ones_fraction)

        if ones_count == mask_size + 1:
            ones_count -= 1
        assert ones_count <= mask_size, f"Unexpected case during aligning point count of contour '{self.name}' (ones_count found badly)"

        step = mask_size // ones_count
        mask = [points_per_interval] * mask_size
        for i in range(0, mask_size, step):
            mask[i] += 1
        return mask

    def align_point_count(self, total_point_count):
        # найти соотношение длины маски и кол-ва единиц в ней, исходя из числа
        # (total_point_count - self.size()) / self.size() - (total_point_count - self.size()) // self.size()
        # маска определяет количество дополнительных точек, которые нужно добавлять не каждый раз
        # (total_point_count - self.size()) // self.size() это число определяет количество точек, которые нужно добавлять каждый раз
        # рандомом кидать едины на маску и проверять, что в половине маски единиц примерно в два раза меньше, чем во всей маске - это для равномерности
        # пройти по всем точкам
        #   клонировать точку, если натыкаюсь на 1 в соответствующем элементе маски - маску фигачить генератором (chain кажется)
        #   если точек столько сколько надо, то КОНЕЦ
        # добавить в самый конец столько точек, сколько еще не хватает до полного

        def get_mask(additional_points_relation):
            if additional_points_relation == 0:
                return [0]
            mask_size = 1
            ones_fraction = float(additional_points_relation)
            while round(ones_fraction) == 0 or \
                    (abs(ones_fraction - round(ones_fraction)) > 0.05 and mask_size < self.size() - 1):
                mask_size += 1
                ones_fraction = additional_points_relation * mask_size
            ones_count = round(ones_fraction)

            if ones_count == mask_size + 1:
                ones_count -= 1
            assert ones_count <= mask_size, f"Unexpected case during aligning point count of contour '{self.name}' (ones_count found badly)"

            step = mask_size // ones_count
            mask = [0] * mask_size
            for i in range(0, mask_size, step):
                mask[i] = 1
            return mask

        points_to_add_count = total_point_count - self.size()
        relation = points_to_add_count / self.size()
        points_per_interval = points_to_add_count // self.size()
        additional_points_relation = relation - points_per_interval
        mask = get_mask(additional_points_relation)

        res_data = np.array([self.data[-1]] * total_point_count)
        start = 0
        end = 0
        points_added = 0
        for coords, additional in zip(self.data, itertools.cycle(mask)):
            end += points_per_interval + additional
            res_data[start: end] = [coords[0], coords[1]]
            points_added += end - start
            if points_added > total_point_count:
                break
            start = end
        self.data = res_data
        self.points_added = points_added

    def _points_between_generator(self, x1, y1, x2, y2, step):
        x_delta, y_delta = abs(x2 - x1), abs(y2 - y1)
        length = math.sqrt(x_delta * x_delta + y_delta * y_delta)
        num_points = int(length / step)
        for inner_x, inner_y in zip(np.linspace(start=x1, stop=x2, num=num_points, endpoint=True),
                                    np.linspace(start=y1, stop=y2, num=num_points, endpoint=True)):
            yield [inner_x, inner_y]

    def _init_contour_on_canvas(self, init_data):
        self.root = tk.Toplevel()
        self.canvas = tk.Canvas(self.root, width=self.w, height=self.h)
        if self.image is not None:
            self.canvas.create_image(self.w/2, self.h/2, image=self.image)
        self.canvas.pack()

        root = self.root
        c = self.canvas
        d = self.d

        last = None
        polygon = None

        id_num_mapping = dict()

        def refresh_polygon():
            nonlocal polygon
            if len(init_data) == 0:
                return
            c.delete(polygon)
            polygon = c.create_polygon(*init_data, fill='', outline=self.color, tag=self.name + "_polygon")

        def empty(event):
            pass

        def replace_point_by_id(event, id):
            x = event.x
            y = event.y

            num = id_num_mapping[id]
            c.coords(id, x - d, y - d, x + d, y + d)  # update coordinates on canvas
            init_data[num] = x  # update coordinates of polygon
            init_data[num + 1] = y
            refresh_polygon()

        def create_contour_point(event):
            nonlocal last
            nonlocal self
            nonlocal polygon
            x = event.x
            y = event.y
            last = c.create_oval(x - d, y - d, x + d, y + d, fill='green', activefill='yellow', tag=self.name + "_point")

            last_p_id = int(last)
            replace_point = lambda event: replace_point_by_id(event, last_p_id)
            c.tag_bind(last_p_id, '<B3-Motion>', replace_point)

            init_data.append(x)
            init_data.append(y)

            id_num_mapping[last] = len(init_data) - 2
            refresh_polygon()

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

        def finish_contour(event):
            root.destroy()
            root.quit()

        def cancel_contour():
            init_data.clear()
            root.destroy()
            root.quit()

        def choose_contour_color():
            color = colorchooser.askcolor(parent=self.root, title="Choose color for contour '" + self.name + "'",
                                          initialcolor=self.color)
            if color:
                self.color = color[1]
                b_choose_contour_color['bg'] = self.color
            refresh_polygon()

        def choose_epicycle_color():
            color = colorchooser.askcolor(parent=self.root, title="Choose color of epicycles", initialcolor=self.color)
            if color:
                self.epicycle_color = color[1]
                b_choose_epicycle_color['bg'] = self.epicycle_color

        def select_contour_name():
            name = simpledialog.askstring(parent=self.root, title='Contour name',
                                          prompt='Select contour name', initialvalue=self.name)
            if name:
                self.name = name

        b_choose_contour_color = tk.Button(root, text='Choose contour color', command=choose_contour_color, background=self.color)
        b_choose_contour_color.pack(side=tk.LEFT)

        b_choose_epicycle_color = tk.Button(root, text='Choose color of epicycles', command=choose_epicycle_color, background=self.epicycle_color)
        b_choose_epicycle_color.pack(side=tk.LEFT)

        b_finish_contour = tk.Button(root, text='Finish contour')
        b_finish_contour.bind("<Button-1>", finish_contour)
        b_finish_contour.pack(side=tk.BOTTOM)

        b_select_contour_name = tk.Button(root, text='Select contour name', command=select_contour_name)
        b_select_contour_name.pack(side=tk.BOTTOM)

        b_cancel_creating = tk.Button(root, text="Cancel", command=cancel_contour)
        b_cancel_creating.pack(side=tk.BOTTOM)

        c.bind("<Button-1>", create_contour_point)
        # root.bind("<Button-1>", create_contour_point)
        c.bind("<Button-2>", replace_last_contour_point)
        # root.bind("a", add_contour_point)
        root.bind("e", finish_contour)

        root.mainloop()


# class Contour:
#     def __init__(self, w, h, pic_name=None, root=None, canvas=None, data=None, solid=True, step=1, number=0):
#         self.root = root
#         self.canvas = canvas
#         self.number = number
#
#         self.d = 5
#         self.uid = uuid.uuid1()
#
#         self.w = w
#         self.h = h
#         self.x0 = w / 2
#         self.y0 = h / 2
#         if data is None:
#             data = []
#             self._init_contour_on_canvas(data, pic_name)
#             # TODO bring reshaping here
#             if solid:
#                 self.edges = np.array(data).reshape(-1, 2).T
#                 data = self._complete_with_points_between(data, step)
#             data = np.array(data).reshape(-1, 2).T
#             data[0] = data[0] - self.x0
#             data[1] = data[1] - self.y0
#         self.data = data
#         self.x = self.data[0, :]
#         self.y = self.data[1, :]
#         # self.dump()
#
#     def size(self):
#         return self.data.shape[1]
#
#     def dump(self):
#         now = datetime.now().microsecond
#         # datetime.time()
#         with open(f"{str(now)}-dump-contour{self.number}", 'w') as out:
#             for i in range(self.data.shape[1]):
#                 out.write(f"{self.data[0, i]}, {self.data[1, i]}\n")
#
#     def smooth_edges(self, interp_radius, *args, **kwargs):
#         pass
#
#     def _complete_with_points_between(self, data, step):
#         assert len(data) % 2 == 0
#         if len(data) <= 2:
#             return data
#         res_data = []
#         x_prev, y_prev = data[0], data[1]
#         for x, y in zip(data[2:-1:2], data[3::2]):
#             res_data.extend(self._points_between_generator(x_prev, y_prev, x, y, step))
#             x_prev, y_prev = x, y
#         res_data.extend(self._points_between_generator(x_prev, y_prev, data[0], data[1], step))
#         return res_data
#
#     def _points_between_generator(self, x1, y1, x2, y2, step):
#         x_delta, y_delta = abs(x2 - x1), abs(y2 - y1)
#         length = math.sqrt(x_delta * x_delta + y_delta * y_delta)
#         num_points = int(length / step)
#         for inner_x, inner_y in zip(np.linspace(start=x1, stop=x2, num=num_points, endpoint=True),
#                                     np.linspace(start=y1, stop=y2, num=num_points, endpoint=True)):
#             yield inner_x
#             yield inner_y
#
#     def _init_contour_on_canvas(self, init_data, pic_name=None):
#         # init_root = tk.Tk()
#         # init_canvas = tk.Canvas(init_root, width=self.w, height=self.h)
#         # init_canvas.pack()
#
#         init_root = tk.Tk()
#         init_root.geometry('1000x1000')
#         init_canvas = tk.Canvas(init_root, width=999, height=999)
#         init_canvas.pack()
#         pilImage = Image.open(pic_name)
#         image = ImageTk.PhotoImage(pilImage)
#         imagesprite = init_canvas.create_image(500, 500, image=image)
#         init_canvas.pack()
#
#         c = init_canvas
#
#         d = self.d
#         uid = self.uid
#         last = None
#         polygon = None
#
#         def refresh_polygon():
#             nonlocal polygon
#             if polygon:
#                 c.delete(polygon)
#             polygon = c.create_polygon(*init_data, fill='', outline='black', tag='mark_' + str(uid))
#
#         def create_contour_point(event):
#             nonlocal last
#             nonlocal self
#             nonlocal polygon
#             x = event.x
#             y = event.y
#             last = c.create_oval(x - d, y - d, x + d, y + d, fill='green', tag='mark_' + str(uid))
#             init_data.append(x)
#             init_data.append(y)
#             refresh_polygon()
#             c.bind("<Button-1>", empty_func)
#
#         def replace_last_contour_point(event):
#             nonlocal last
#             nonlocal self
#             nonlocal polygon
#             x = event.x
#             y = event.y
#             init_data[-2] = x
#             init_data[-1] = y
#             c.coords(last, x - d, y - d, x + d, y + d)
#             refresh_polygon()
#             c.bind("<Button-3>", empty_func)
#
#         def add_contour_point(event):
#             c.bind('<Button-1>', create_contour_point)
#
#         def replace_last(event):
#             c.bind('<Button-3>', replace_last_contour_point)
#
#         def finish_contour(event):
#             init_root.destroy()
#
#         b_add = tk.Button(init_root, text='add point')
#         b_add.bind("<Button-1>", add_contour_point)
#         b_add.pack(side='top')
#
#         b_replace = tk.Button(init_root, text='replace last point')
#         b_replace.bind("<Button-1>", replace_last)
#         b_replace.pack(side='bottom')
#
#         b_finish = tk.Button(init_root, text='finish')
#         b_finish.bind("<Button-1>", finish_contour)
#         b_finish.pack(side='top')
#
#         init_root.bind("<Button-1>", create_contour_point)
#         init_root.bind("<Button-3>", replace_last_contour_point)
#         init_root.bind("a", add_contour_point)
#         init_root.bind("e", finish_contour)
#
#         init_root.mainloop()
