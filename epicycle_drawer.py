import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageTk#, ImageGrab
import io
# import imageio
#from util import getter, draw_outlined_point
from util import clear_folder
from util import draw_point
import os
import shutil
from contour import Contour
from fourier import EpicycleChain2D
from geom import Point
import numpy as np
import math
import itertools

class Drawer:
    """
    0.  singleton
    1.  имеет свой root и canvas с актуальной информацией о контурах и прочем разном
    2.  при создании нового контура создается свой рут, в котором на canvas то же самое, что находится в drawer в текущий момент
        результат создания фигарится на основной canvas
        при создании нужно каким-то образом давать возможность выбора цвета
    3.  все контуры подгоняет под одинаковое количество точек (для синхронности отрисовки)
    4.  запускает анимацию (возможно уже на новом root,canvas) с отрисовкой епициклов (нихуя они не эпи)
    5.  делает дамп картинок в папку проекта


    надо сделать удобный способ переносить данные с одного root,canvas на другой (добавлять, вытаскивать и тд)
    надо сделать возможность загрузки изображения
    надо сделать что-то вроде папки проекта, куда скидываются дампы контуров
    надо сделать возможность выбора цвета контура
    надо подогнать класс Contour под взаимодействие с Drawer:
        * не передавать отдельные параметры canvas, а тупо "копировать" конфиг старого canvas
        * ...

    кнопки:
        * задать имя проекту (дефолт = Project_<now_date>)
        * выбрать цвет фона в анимации
        * выбрать начало координат (дефолт = центр)

        * удалить контур
        * загрузить контур
        * ---редактировать контуры

        * предварительный просмотр (без эпициклов)
        * начать анимацию

    """
    def __init__(self):
        # TODO переделать на наследование от Tkinter
        # self.root = tk.Tk()
        # self.canvas = tk.Canvas(self.root, width=500, height=500, bg='white')
        self.buttons = []
        self.contours = []
        self.polygons = []
        self.project_path = ""
        self.canvas_initial_state = None
        self.is_fit = False
        self.origin_id = None
        self.width = None
        self.height = None
        self.background_color = 'black'
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, width=500, height=500, bg='white')
        self.create_initial_buttons()
        self.x0 = None
        self.y0 = None
        # self.mainloop()
        pass

    def mainloop(self):
        # self.save_canvas_state()
        self.root.mainloop()

    def save_canvas_initial_state(self):
        ps = self.canvas.postscript(colormode='color', pagewidth=self.width, pageheight=self.height, width=self.width, height=self.height)
        pil_image = Image.open(io.BytesIO(ps.encode('utf-8')))
        self.canvas_initial_state = pil_image
        pil_image.save('canvas_dump.png')
        # self.root.mainloop()

    def save_canvas_snapshot(self, gif_resource_path, canvas, num):
        width = canvas['width']
        height = canvas['height']
        # ps = self.canvas.postscript(
        #     file=os.path.join(gif_resource_path, "test.eps"),
        #     colormode='color', pagewidth=width, pageheight=height, width=width, height=height)

        # self.canvas.postscript(
        #     file=os.path.join(gif_resource_path, "circles.eps"),
        #     colormode='color', pagewidth=width, pageheight=height, width=width, height=height)
        ps = canvas.postscript(
            # file=os.path.join(gif_resource_path, "circles.eps"),
                colormode='color', pagewidth=width, pageheight=height, width=width, height=height)
        pil_image = Image.open(io.BytesIO(ps.encode('utf-8')))
        # pil_image.show()
        name = "ss" + str(num).rjust(7, '0') + ".png"
        snapshot_path = os.path.join(gif_resource_path, name)
        pil_image.save(snapshot_path)

    def clear_polygons(self):
        for poly_id in self.polygons:
            self.canvas.delete(poly_id)

    def apply_contours(self):
        self.clear_polygons()
        for cont in self.contours:
            polygon_points = cont.get_polygon_array()
            poly_id = self.canvas.create_polygon(*polygon_points, fill='',
                                                 outline=cont.color,
                                                 tag=cont.name + '_polygon')
            self.polygons.append(poly_id)
        self.canvas.tag_raise(self.origin_id)
        self.canvas.update()

    def create_initial_buttons(self):
        def choose_project_path():
            self.project_path = filedialog.askdirectory()
            biba = 1
            clear_folder(self.project_path)
            # files = os.listdir(self.project_path)
            # for file in files:
            #     file_path = os.path.join(self.project_path, file)
            #     if os.path.isfile(file_path) or os.path.islink(file_path):
            #         os.unlink(file_path)
            #     elif os.path.isdir(file_path):
            #         shutil.rmtree(file_path)

            b_choose_project_path.destroy()
            self.create_main_buttons()

        b_choose_project_path = tk.Button(self.root, text='Choose project folder', command=choose_project_path)
        b_choose_project_path.pack(side=tk.BOTTOM)

    # def align_contours_by_point_count(self):
    #     # self.contours.append(Contour(dump_file=r"D:\Documents\PythonProj\Contour1.contour", name='Contour' + str(len(self.contours) + 1)))
    #     # self.contours.append(Contour(dump_file=r"D:\Documents\PythonProj\Contour2.contour", name='Contour' + str(len(self.contours) + 1)))
    #
    #     if self.is_fit or len(self.contours) == 0:
    #         return
    #     for cont in self.contours:
    #         cont.fill_with_points_between()
    #         # cont.dump(self.project_path)
    #
    #     max_point_count = 0
    #     largest_cont = None
    #     contours_to_extend = list(self.contours)
    #     for cont in self.contours:
    #         if cont.size() > max_point_count:
    #             max_point_count = cont.size()
    #             largest_cont = cont
    #     contours_to_extend.remove(largest_cont)
    #
    #     for cont in contours_to_extend:
    #         cont.align_point_count(max_point_count)
    #     self.is_fit = True

    def init_timelines(self):
        for cont in self.contours:
            cont.fill_with_points_between()

        max_point_count = 0
        largest_cont = None
        common_dt = 0
        contours = list(self.contours)
        for cont in self.contours:
            if cont.size() > max_point_count:
                max_point_count = cont.size()
                common_dt = 2 * math.pi / max_point_count
                largest_cont = cont
        # contours.remove(largest_cont)

        self.timelines = []
        timelines = []
        max_timeline_len = 0
        for cont in contours:
            dt = math.pi * 2 / cont.size()
            timeline = np.arange(0, 2 * math.pi, dt).tolist()
            if cont == largest_cont:
                timelines.append(timeline)
                continue
            mask = cont.get_aligning_mask(max_point_count)
            pre_aligned_timeline = []
            for t, num_tik in zip(timeline, itertools.cycle(mask)):
                pre_aligned_timeline.extend([t] * num_tik)
            # pre_aligned_timeline.extend([pre_aligned_timeline[-1] * (max_point_count - len(pre_aligned_timeline))])
            if len(pre_aligned_timeline) > max_timeline_len:
                max_timeline_len = len(pre_aligned_timeline)
            timelines.append(pre_aligned_timeline)
        for tl in timelines:
            tl.extend([tl[-1] * (max_timeline_len - len(tl))])
            self.timelines.append(np.array(tl))
        return list(self.timelines), common_dt

    def get_starting_point(self):
        return self.canvas.coords(self.origin_id)

    def create_main_buttons(self):
        def __load_img_to_canvas():
            self.is_fit = False

            self.contours.clear()

            image_path = filedialog.askopenfile().name
            pil_image = Image.open(image_path)
            self.image_path = image_path
            image = ImageTk.PhotoImage(pil_image)

            h = image.height()
            w = image.width()
            self.width = w
            self.height = h

            self.canvas.destroy()
            self.canvas = tk.Canvas(self.root, width=w, height=h)
            self.canvas.pack()
            self.canvas.create_image(w/2, h/2, image=image)

            self.save_canvas_initial_state()

            # self.origin_id = draw_outlined_point(self.canvas, x=self.width / 2, y=self.height / 2,
            #                                      r=5, color='red', outline_color='white', activefill='yellow')
            x=self.width / 2
            y=self.height / 2
            r=5

            self.origin_id = self.canvas.create_oval(x - r, y - r, x + r, y + r, tag='sdafsa', 
                fill='red', outline='white', activefill='yellow')
            # self.canvas.update()

            def replace_point(event):
                x = event.x
                y = event.y
                d = 5
                self.x0 = x
                self.y0 = y
                self.canvas.coords(self.origin_id, x - d, y - d, x + d, y + d)  # update coordinates on canvas
            self.canvas.tag_bind(self.origin_id, '<B1-Motion>', replace_point)

            self.x0 = x
            self.y0 = y
            self.canvas.pack()

            self.canvas.update()
            
            self.mainloop()

        def __add_contour():
            self.is_fit = False
            cont = Contour(pil_image=self.canvas_initial_state, name='Contour' + str(len(self.contours) + 1))
            if cont.size() > 0:
                self.contours.append(cont)
                cont.dump(self.project_path)
                self.apply_contours()

        def __create_gif():
            import imageio
            gif_resource_path = os.path.join(self.project_path, "gif_resource")
            gif_path = os.path.join(self.project_path, "out.gif")
            files = sorted(os.listdir(gif_resource_path))
            with imageio.get_writer(gif_path, mode='I') as writer:
                for filename in files:
                    resource_path = os.path.join(gif_resource_path, filename)
                    image = imageio.imread(resource_path)
                    writer.append_data(image)

        def __run_animation():
            assert len(self.contours) > 0
            # TODO сообщение пользователю, что нет контуров и return
            timelines, dt = self.init_timelines()
            origin_point = np.array([self.x0, self.y0])

            chains = []
            contour_colors = []
            anim_root = tk.Toplevel()
            anim_canvas = tk.Canvas(anim_root, width=self.width, height=self.height)
            bg = anim_canvas.create_rectangle(0, 0, self.width, self.height,
                                         fill=self.background_color, outline=self.background_color)
            anim_canvas.tag_lower(bg)

            for cont in self.contours:
                cont.data = cont.data - origin_point
                chains.append(EpicycleChain2D(anim_canvas, cont, origin_point, tag_name='chain'))
                contour_colors.append(cont.color)
            anim_canvas.pack()

            gif_resource_path = os.path.join(self.project_path, "gif_resource")
            os.makedirs(gif_resource_path)  # , 777)

            num_chains = len(chains)
            for i1, times in enumerate(zip(*timelines)):
                for i in range(num_chains):
                    chain = chains[i]
                    t = times[i]
                    v = chain.update_vectors_by_time(t)
                    chain.draw()
                    draw_point(anim_canvas, v.x, v.y, r=3, tag_name='point_tag', color=contour_colors[i])
                anim_canvas.update()
                self.save_canvas_snapshot(gif_resource_path, anim_canvas, i1)
            for i2, times in enumerate(zip(*timelines)):
                for i in range(num_chains):
                    chain = chains[i]
                    t = times[i]
                    v = chain.update_vectors_by_time(t)
                    p = draw_point(anim_canvas, v.x, v.y, r=3, tag_name='point_tag', color=self.background_color)
                    anim_canvas.tag_raise(p)
                    chain.draw()
                anim_canvas.update()
                self.save_canvas_snapshot(gif_resource_path, anim_canvas, i1 + i2 + 1)
            anim_canvas.after(1000)

            __create_gif()

            anim_root.destroy()
            anim_root.quit()


        def __preview():

            # показать все контуры целиком, с соблюдением цветов:
            #   * фона
            #   * контура
            #   * вектора

            pass

        def __choose_background_color():
            color = colorchooser.askcolor(parent=self.root, title="Choose background color",
                                          initialcolor=self.background_color)
            if color:
                self.background_color = color[1]
                b_choose_bg_color['bg'] = self.background_color


        b_create_gif = tk.Button(self.root, text="Create gif", command=__create_gif)
        b_create_gif.pack(side=tk.BOTTOM)

        b_load_pic = tk.Button(self.root, text='Load picture', command=__load_img_to_canvas)
        b_load_pic.pack(side=tk.BOTTOM)

        b_create_contour = tk.Button(self.root, text='Create contour', command=__add_contour)
        b_create_contour.pack(side=tk.BOTTOM)

        b_run_animation = tk.Button(self.root, text="ЗАПУЗЫРИТЬ АНИМАЦИЮ", command=__run_animation)
        b_run_animation.pack(side=tk.BOTTOM)

        b_preview = tk.Button(self.root, text='Preview', command=__preview)
        b_preview.pack(side=tk.BOTTOM)

        b_choose_bg_color = tk.Button(self.root, text='Choose background color', command=__choose_background_color)
        b_choose_bg_color.pack(side=tk.BOTTOM)

        self.buttons.append(b_load_pic)
        self.buttons.append(b_create_contour)

    def clear_buttons(self):
        for b in self.buttons:
            b.destroy()

    def add_contour(self):
        pass

    def draw_animation(self):
        pass


