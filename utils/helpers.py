import pygame
from math import copysign
from typing import Callable, Any, Union
from random import random
from collections import OrderedDict

def to_roman(num : int) -> str:

    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])

ColorType = Union[list[int], tuple[int, int, int], pygame.Color]

class Task:
    def __init__(self, callback : Callable, *args, **kwargs) -> None:
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
    
    def execute(self):
        self.callback(*self.args, **self.kwargs)

def scale_surf(surf : pygame.Surface, scale : float):
    return pygame.transform.scale_by(surf, scale)

def rotate_around_pivot(image : pygame.Surface, rect : pygame.Rect, angle : float, 
                        anchor : pygame.Vector2 = None, offset : pygame.Vector2= None, return_new_pos = False):
    
    if anchor:
        real_anchor_point = anchor or pygame.Vector2(rect.center) + offset
        offset= offset or real_anchor_point - pygame.Vector2(rect.center)

    elif offset:
        real_anchor_point = offset + pygame.Vector2(rect.center)
        offset = offset

    new_offset = offset.rotate(angle)
    old_center = rect.center

    new_image = pygame.transform.rotate(image, -angle)
    new_rect = new_image.get_rect(center = old_center)
    new_pos = real_anchor_point - new_offset
    new_rect.center = round(new_pos)
    if return_new_pos:
        return new_image, new_rect, new_pos
    else:
        return new_image, new_rect

def rotate_around_center(image : pygame.Surface, pos : pygame.Vector2, angle : float) -> tuple[pygame.Surface, pygame.Rect]:
    new_image = pygame.transform.rotate(image, -angle)
    new_rect = new_image.get_rect(center = round(pos))
    return new_image, new_rect

def rotate_around_pivot_accurate(image : pygame.Surface, pos : pygame.Vector2, angle : float, 
                        anchor : pygame.Vector2 = None, offset : pygame.Vector2 = None, debug = False):
    
    if anchor is not None:
        real_anchor_point = anchor
        offset = offset or (real_anchor_point - pos).rotate(-angle)

    elif offset is not None:
        real_anchor_point = pos + offset.rotate(angle)
        offset = offset
    else:
        raise ValueError('Either offset or anchor must be provided')
    new_offset = offset.rotate(angle)

    new_image = pygame.transform.rotate(image, -angle)  
    new_pos = real_anchor_point - new_offset


    new_rect = new_image.get_rect(center = round(new_pos))
    if debug:
        return new_image, new_rect, new_pos, [real_anchor_point]
    else:
        return new_image, new_rect, new_pos

def sign(x):
    return copysign(1, x)
def is_sorted(iterable : list[object], key : Callable[[object], float|int]):
    current_val = key(iterable[0])
    for obj in iterable:
        val = key(obj)
        if val < current_val: return False
    return True

def average(values : list[float]):
    return sum(values) / len(values)

def random_float(a : float, b : float):
    return pygame.math.lerp(a, b, random())


def make_upgrade_bar(width : int = 100, length : int = 20, count = 5, border : int = 3, border_color : str|ColorType = 'Black', 
                     bg_color : str|ColorType = (90, 90, 90)):
    surf = pygame.surface.Surface((width + border * 2, (length + border) * count + border))
    surf.fill(border_color)
    pygame.draw.rect(surf, bg_color, (border, border, width, (length + border) * count - border))
    for i in range(count):
        pygame.draw.rect(surf, border_color, (0, (border + length) * i, width + border * 2, border))
    return surf

def paint_upgrade_bar(surf : pygame.Surface, index : int, width : int = 100, length : int = 20, border : int = 3, color : str|ColorType = 'Green'):
    pygame.draw.rect(surf, color, (border, (length + border) * index + border, width, length))

def reset_upgrade_bar(surf : pygame.Surface, count : int = 5, width : int = 100, length : int = 20, border : int = 3, bg_color : str|ColorType = (90, 90, 90)):
    for index in range(count):
        pygame.draw.rect(surf, bg_color, (border, (length + border) * index + border, width, length))

def make_right_arrow(height : int, width : int, color : ColorType|str = (255, 0, 0), colorkey : ColorType|str = (0, 255, 0)) -> pygame.Surface:
    surface = pygame.surface.Surface((width, height))
    surface.set_colorkey(colorkey)
    surface.fill(colorkey)
    pygame.draw.polygon(surface, color, [(0,0), (width, height // 2), (0, height)])
    return surface

def make_circle(radius : int, color : ColorType|str, colorkey : ColorType|str = (0, 255, 0)) -> pygame.Surface:
    d = radius * 2
    surface : pygame.Surface = pygame.Surface((d, d))
    surface.set_colorkey(colorkey)
    surface.fill(colorkey)
    pygame.draw.circle(surface, color, (radius, radius), radius)
    return surface


def load_alpha_to_colorkey(path : str, colorkey : ColorType|str):
    image = pygame.image.load(path).convert_alpha()
    new_surf = pygame.surface.Surface(image.get_size())
    new_surf.set_colorkey(colorkey)
    new_surf.fill(colorkey)
    new_surf.blit(image, (0,0))
    return new_surf

def tuple_vec_average(l : list[tuple[float, float]]) -> float:
    x_sum : float = 0
    y_sum : float = 0
    count : int = 0
    for x, y in l:
        x_sum += x
        y_sum += y
        count += 1
    x_sum /= count
    y_sum /= count
    return (x_sum, y_sum)