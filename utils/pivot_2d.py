import pygame
from typing import Any
def rotate_around_pivot_accurate(image : pygame.Surface, pos : pygame.Vector2, angle : float,
                        offset : pygame.Vector2 = None, debug = False, colorkey : pygame.Color|None = None):
    
    if colorkey is not None:
        prev_colorkey = image.get_colorkey()
        image.set_colorkey(colorkey)

    new_image = pygame.transform.rotate(image, -angle)
    new_pos = pos - offset.rotate(angle)

    new_rect = new_image.get_rect(center = round(new_pos))
    if colorkey is not None: image.set_colorkey(prev_colorkey)
    if debug:
        return new_image, new_rect, new_pos, [pygame.Vector2(0,0)]
    else:
        return new_image, new_rect, new_pos

def rotate_around_pivot_pos_only(pos : pygame.Vector2, angle : float, offset : pygame.Vector2):
    return pos - offset.rotate(angle)


class Pivot2D:
    def __init__(self, pos : pygame.Vector2, og_image : pygame.Surface|None = None, colorkey : pygame.Color|None = None) -> None:
        self._origin : pygame.Vector2 = pos
        self._pivot_offset : pygame.Vector2 = pygame.Vector2(0,0)
        self._angle : float = 0
        self._position : pygame.Vector2 = self._origin.copy()
        self.is_cached : bool = True
        self.original_image : pygame.Surface|None = og_image
        self.img_colorkey : pygame.Color|None = colorkey
    
    @property
    def origin(self):
        return self._origin
    
    @origin.setter
    def origin(self, new_val : pygame.Vector2):
        self._origin = new_val
        self.is_cached = False
    
    @property
    def angle(self):
        return self._angle
    
    @angle.setter
    def angle(self, new_val : float):
        self._angle = new_val
        self.is_cached = False
    
    @property
    def pivot_offset(self):
        return self._pivot_offset
    
    @pivot_offset.setter
    def pivot_offset(self, new_val : pygame.Vector2):
        self._pivot_offset = new_val
        self.is_cached = False

    
    @property
    def position(self) -> pygame.Vector2:
        if not self.is_cached: 
            self._position = rotate_around_pivot_pos_only(self._origin, self._angle, self._pivot_offset)
        return self._position
    
    @position.setter
    def position(self, new_value : pygame.Vector2):
        offset = new_value - self.position
        self.origin += offset
    
    def rotate_image(self, image : pygame.Surface) -> tuple[pygame.Surface, pygame.Rect, pygame.Vector2]:
        return rotate_around_pivot_accurate(image, self._origin, self._angle, self._pivot_offset, debug=False, colorkey=self.img_colorkey)
    
    def rotate_og_image(self):
        return self.rotate_image(self.original_image)
    
    def rotate_image_debug(self, image : pygame.Surface) -> tuple[pygame.Surface, pygame.Rect, pygame.Vector2, Any]:
        return rotate_around_pivot_accurate(image, self._origin, self._angle, self._pivot_offset, debug=True, colorkey=self.img_colorkey)