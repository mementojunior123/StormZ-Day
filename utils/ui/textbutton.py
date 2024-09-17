import pygame
from math import floor
from utils.ui.ui_sprite import UiSprite
from utils.helpers import rotate_around_pivot_accurate
import button_templates

class TextButton(UiSprite):
    main_font = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    main_image = button_templates.blue_button_surf
    def __init__(self, surf: pygame.Surface, rect: pygame.Rect, tag: int, text : str, name: str | None = None, keep_og_surf=False, 
                 attributes: dict = None, data: dict = None, forced_og_surf: pygame.Surface = None, zindex: int = 0, 
                 text_settings : tuple[pygame.Font, pygame.Color, bool]|None = None, text_scale : float = 1, max_line_lentgh : int = 0):
        
        super().__init__(surf, rect, tag, name, True, attributes, data, forced_og_surf, zindex)
        self.text_settings : tuple[pygame.Font, pygame.Color, bool] = text_settings or (TextButton.main_font, 'Black', False)
        self._text : str = text
        self._text_percent : float = 1
        self._true_text : str = text
        self._text_scale : float = text_scale
        self.max_line_lentgh : int = max_line_lentgh
    
        
    def _render(self):
        if self.og_surf is None:
            self.og_surf = self.surf.copy()
        else:
            self.surf = self.og_surf.copy()
        self._render_text()
        scalex_offset, scaley_offset = self._scale.x - 1, self._scale.y - 1
        if abs(scalex_offset) > 0.001 or abs(scaley_offset) > 0.001:
            self.surf = pygame.transform.scale_by(self.surf, self.scale)
        opacity_offset =  1- self._opacity
        
        if abs(self._angle) > 0.001:
            if not self.use_pivot:
                self.surf, self.rect, self.position = rotate_around_pivot_accurate(self.surf, self.position, self._angle, self.position, pygame.Vector2(0,0))
            else:
                self.surf, self.rect, self._position = self._pivot.rotate_image(self.surf)

        if abs(opacity_offset) > 0.002:
            self.surf.set_alpha(self._opacity * 255)        
        for filter in self.filters:
            filter.apply(self.surf)
    
    def _render_text(self):
        if self._true_text == '': return
        surf_size = self.surf.get_size()
        centerx, centery = surf_size[0] //2, surf_size[1] // 2
        text_surf = self.text_settings[0].render(self._true_text, self.text_settings[2], self.text_settings[1], wraplength=self.max_line_lentgh)
        if self.text_scale != 1:
            text_surf = pygame.transform.scale_by(text_surf, self.text_scale)
        self.surf.blit(text_surf, text_surf.get_rect(center=(centerx, centery)))
    
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, new_val : str):
        prev_true_text = self._true_text
        self._text = new_val
        if self._text == '':
            self._true_text = ''
            if prev_true_text != '':
                self._render()
            return

        text_index = floor(self._text_percent * len(self._text))
        self._true_text = self._text[:text_index + 1]
        if self._true_text != prev_true_text:
            self._render()
    
    @property
    def text_progress(self):
        return self._text_percent
    
    @text_progress.setter
    def text_progress(self, new_val : float):
        prev_true_text = self._true_text
        self._text_percent = pygame.math.clamp(new_val, 0, 1)
        text_index = floor(self._text_percent * len(self._text))
        self._true_text = self._text[:text_index]
        if self._true_text != prev_true_text:
            self._render()
    
    @property
    def text_scale(self):
        return self._text_scale
    
    @text_scale.setter
    def text_scale(self, new_val):
        self._text_scale = new_val
        self._render()