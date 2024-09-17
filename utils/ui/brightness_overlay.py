import pygame
from utils.ui.ui_sprite import UiSprite
from utils.helpers import rotate_around_pivot_accurate

class BrightnessOverlay(UiSprite):
    def __init__(self, brightness : int, rect: pygame.Rect, tag: int, name: str | None = None, attributes: dict = None, data: dict = None, zindex: int = 0):
        super().__init__(None, rect, tag, name, None, attributes, data, None, zindex)
        self._experimental_blend : bool = True
        self._opacity = 1
        self._brightness = brightness
        if self._experimental_blend:
            self._blend_mode = pygame.BLEND_RGB_ADD if self._brightness >= 0 else pygame.BLEND_RGB_MULT
            abs_brightness = abs(self._brightness) if self._brightness >= 0 else 255 - abs(self._brightness)
        else:
            self._blend_mode = pygame.BLEND_RGB_ADD if self._brightness >= 0 else pygame.BLEND_RGB_SUB
            abs_brightness = abs(self._brightness)

        self.surf = pygame.surface.Surface(self.rect.size)
        self.surf.fill((abs_brightness, abs_brightness, abs_brightness))
    
    @property
    def brightness(self):
        return self._brightness
    
    @brightness.setter
    def brightness(self, new_val : int):
        self._brightness = new_val
        self._blend_mode = pygame.BLEND_RGB_ADD if self._brightness >= 0 else pygame.BLEND_RGB_MULT
        self._render()
    
    def _render(self):
        if self._experimental_blend:
            self._blend_mode = pygame.BLEND_RGB_ADD if self._brightness >= 0 else pygame.BLEND_RGB_MULT
            abs_brightness = abs(self._brightness) if self._brightness >= 0 else 255 - abs(self._brightness)
        else:
            self._blend_mode = pygame.BLEND_RGB_ADD if self._brightness >= 0 else pygame.BLEND_RGB_SUB
            abs_brightness = abs(self._brightness)
        self.surf = pygame.surface.Surface(self.rect.size)
        self.surf.fill((abs_brightness, abs_brightness, abs_brightness))
        scalex_offset, scaley_offset = self._scale.x - 1, self._scale.y - 1
        if abs(scalex_offset) > 0.001 or abs(scaley_offset) > 0.001:
            self.surf = pygame.transform.scale_by(self.surf, self.scale)

        
        
        if abs(self._angle) > 0.001:
            if not self.use_pivot:
                self.surf, self.rect, self.position = rotate_around_pivot_accurate(self.surf, self.position, self._angle, self.position, pygame.Vector2(0,0))
            else:
                self.surf, self.rect, self._position = self._pivot.rotate_image(self.surf)

        opacity_offset =  1- self._opacity
        if abs(opacity_offset) > 0.002:
            self.surf.set_alpha(self._opacity * 255)

        for filter in self.filters:
            filter.apply(self.surf)
    
    def draw(self, display : pygame.Surface):
        if self.visible:
            display.blit(self.surf, self.rect, special_flags=self._blend_mode)