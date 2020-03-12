import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"P({self.x}, {self.y})"

    def __getitem__(self, item):
        if item == 0:
            return self.x
        if item == 1:
            return self.y
        raise RuntimeError("Invalid index.")

    def get_iter(self):
        yield self.x
        yield self.y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Vector:
    def __init__(self, p1, p2):
        self.p_from = p1
        self.p_to = p2

    def __repr__(self):
        return f"V {self.p_from}->{self.p_to}"

    def get_iter(self):
        yield self.p_from.x
        yield self.p_from.y
        yield self.p_to.x
        yield self.p_to.y

    def norm(self):
        d_x = self.p_from[0] - self.p_to[0]
        d_y = self.p_from[1] - self.p_to[1]
        return math.sqrt(d_x * d_x + d_y * d_y)

    def __add__(self, other):
        return Vector(self.p_from, other.p_to)

    def __sub__(self, other):
        return Vector(self.p_to, other.p_to)

    def collides(self, v2):
        return self.overlays(v2) or self.intersects(v2)

    def intersects(self, v2):
        return self._check_bounding_box(v2) and \
               ori_area(self.p_from, self.p_to, v2.p_from) * ori_area(self.p_from, self.p_to, v2.p_to) <= 0 and \
               ori_area(v2.p_from, v2.p_to, self.p_from) * ori_area(v2.p_from, v2.p_to, self.p_to) <= 0

    def overlays(self, v2):
        return self.on_same_straight(v2) and self._in_xrange(v2.p_from.x, v2.p_to.x)

    def contains_point(self, point: Point):
        return self.overlays(Vector(point, point))

    def on_same_straight(self, v2):
        def straight_equation(x, y, v: Vector):
            x0, y0 = v.p_from.x, v.p_from.y
            x1, y1 = v.p_to.x, v.p_to.y
            return (x - x0) * (y1 - y0) - (y - y0) * (x1 - x0)
        return straight_equation(v2.p_from.x, v2.p_from.y, self) == 0 and \
               straight_equation(v2.p_to.x, v2.p_to.y, self) == 0

    def _in_xrange(self, x_left, x_right):
        return x_left < self.p_from.x < x_right or x_left < self.p_to.x < x_right

    def _in_yrange(self, y_down, y_up):
        return y_down < self.p_from.y < y_up or y_down < self.p_to.y < y_up

    def _check_bounding_box(self, v2):
        return self._check_bounds(self.p_from.x, self.p_to.x, v2.p_from.x, v2.p_to.x) and \
               self._check_bounds(self.p_from.y, self.p_to.y, v2.p_from.y, v2.p_to.y)

    def _check_bounds(self, a, b, c, d):
        max1, min1 = max(a, b), min(a, b)
        max2, min2 = max(c, d), min(c, d)
        return max(min1, min2) <= min(max1, max2)


class Num:
    def __init__(self, a):
        self.a = a


def ori_area(pa: Point, pb: Point, pc: Point):
    """
    Oriented area of triangle
    :param pa:
    :param pb:
    :param pc:
    :return:
    """
    return (pb.x - pa.x) * (pc.y - pa.y) - (pb.y - pa.y) * (pc.x - pa.x)
