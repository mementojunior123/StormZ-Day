import pygame
from pygame import Vector2
from math import ceil
from typing import Generator, Any

class RayCastMask:
    @staticmethod
    def from_ray_include_points(ray_start : Vector2, ray_end : Vector2) -> 'RayCastMask':
        delta : Vector2 = ray_end - ray_start
        points : list[tuple[int, int]] = get_points(ray_start, ray_end)
        rect : pygame.Rect = pygame.Rect(1,1,1,1)
        rect.size = (abs(ceil(delta.x)), abs(ceil(delta.y))) 
        rect.topleft = (round(min(ray_start.x, ray_end.x)), round(min(ray_start.y, ray_end.y)))
        mask : pygame.Mask = pygame.Mask((rect.size[0] + 1, rect.size[1] + 1))
        offset = get_offset(ray_start, ray_end)
        for point in points:
            mask.set_at((point[0] - offset[0], point[1] - offset[1]))
        return RayCastMask(mask, points, rect, ray_start, ray_end)
    
    @staticmethod
    def from_ray_ignore_points(ray_start : Vector2, ray_end : Vector2) -> 'RayCastMask':
        delta : Vector2 = ray_end - ray_start
        rect : pygame.Rect = pygame.Rect(1,1,1,1)
        rect.size = (abs(round(delta.x)), abs(round(delta.y))) 
        rect.topleft = (round(min(ray_start.x, ray_end.x)), round(min(ray_start.y, ray_end.y)))
        mask : pygame.Mask = pygame.Mask((rect.size[0] + 2, rect.size[1] + 2))
        offset = get_offset(ray_start, ray_end)
        for point in get_points_gen(ray_start, ray_end):
            mask.set_at((point[0] - offset[0], point[1] - offset[1]))
        return RayCastMask(mask, None, rect, ray_start, ray_end)
    
    @staticmethod
    def from_ray_surf(ray_start : Vector2, ray_end : Vector2) -> 'RayCastMask':
        delta : Vector2 = ray_end - ray_start
        offset = get_offset(ray_start, ray_end)
        rect : pygame.Rect = pygame.Rect(1,1,1,1)
        rect.size = (abs(ceil(delta.x)), abs(ceil(delta.y))) 
        rect.topleft = (round(min(ray_start.x, ray_end.x)), round(min(ray_start.y, ray_end.y)))
        mask_size : tuple[int, int] = (rect.size[0] + 1, rect.size[1] + 1)
        surf : pygame.Surface = pygame.surface.Surface(mask_size)

        pygame.draw.line(surf, 'White', ray_start - offset, ray_end - offset)
        surf.set_colorkey([0,0,0])
        mask : pygame.Mask = pygame.mask.from_surface(surf)
        return RayCastMask(mask, None, rect, ray_start, ray_end)


    def __init__(self, mask : pygame.Mask, points : list[tuple[int, int]]|None, rect : pygame.Rect, start : pygame.Vector2, end : pygame.Vector2) -> None:
        self.start : pygame.Vector2 = start
        self.end : pygame.Vector2 = end
        self.mask : pygame.Mask = mask
        self.points : list[tuple[int, int]]|None = points
        self.rect : pygame.Rect = rect
    
    def collide_rect(self, other_rect : pygame.Rect) -> bool:
        if other_rect.clipline(self.start, self.end): return True
        return False
    
    def collide_mask(self, other_mask : pygame.Mask, other_offset : pygame.Vector2|tuple[int, int]) -> bool:
        return self.mask.overlap(other_mask, other_offset)

def half_normaize(vec : Vector2) -> Vector2:
    if vec.x == vec.y:
        return vec.normalize()
    elif abs(vec.x) > abs(vec.y):
        return vec / abs(vec.x)
    else:
        return vec / abs(vec.y)

def get_points(ray_start : Vector2, ray_end : Vector2) -> list[tuple[int, int]]:
    ray_offset : Vector2 = ray_end - ray_start
    ray_normal : Vector2 = half_normaize(ray_offset)

    target_x : int
    target_y : int
    current_pos : Vector2 = ray_start.copy()

    axis = 0 if ray_normal.x > ray_normal.y else 1
    max_iter : int = ceil(get_max(ray_start, ray_end)[axis] - get_offset(ray_start, ray_end)[axis])
    point_list : list[tuple[int, int]] = [None for _ in range(max_iter)]
    for i in range(max_iter):
        target_x = round(current_pos.x)
        target_y = round(current_pos.y)
        point : tuple[int, int] = (target_x, target_y)
        point_list[i] = point
        current_pos += ray_normal

    return point_list

def get_points_gen(ray_start : Vector2, ray_end : Vector2) -> Generator[tuple[int, int], Any, Any]:
    ray_offset : Vector2 = ray_end - ray_start
    ray_normal : Vector2 = half_normaize(ray_offset)

    target_x : int
    target_y : int
    current_pos : Vector2 = ray_start.copy()

    axis = 0 if abs(ray_normal.x) > abs(ray_normal.y) else 1
    max_iter : int = ceil(get_max(ray_start, ray_end)[axis] - get_offset(ray_start, ray_end)[axis])
    for i in range(max_iter):
        target_x = round(current_pos.x)
        target_y = round(current_pos.y)
        point : tuple[int, int] = (target_x, target_y)
        yield point
        current_pos += ray_normal

def get_offset(ray_start : Vector2, ray_end : Vector2) -> tuple[int, int]:
    return (round(min(ray_start.x, ray_end.x)), round(min(ray_start.y, ray_end.y)))

def get_max(ray_start : Vector2, ray_end : Vector2) -> tuple[int, int]:
    return (max(ray_start.x, ray_end.x), max(ray_start.y, ray_end.y))

def transcribe_grid(offset : tuple[int, int], MAX : tuple[int, int], point_list : list[tuple[int, int]]) -> list[list[int]]:
    x_offset, y_offset = offset
    grid = [[0 for _ in range(MAX[0] - x_offset + 1)] for _ in range(MAX[1] - y_offset + 1)]
    for point in point_list:
        x, y = point
        grid[y - y_offset][x - x_offset] = 1
    return grid

def get_grid(ray_start : Vector2, ray_end : Vector2) -> list[list[int]]:
    points = get_points(ray_start, ray_end)
    offset = get_offset(ray_start, ray_end)
    MAX = get_max(ray_start, ray_end)
    return transcribe_grid(offset, MAX, points)


def _sprite_hint():
    global Sprite
    from game.sprite import Sprite