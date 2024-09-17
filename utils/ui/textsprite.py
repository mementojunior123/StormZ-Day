import pygame
from math import floor
from utils.ui.ui_sprite import UiSprite
from utils.helpers import rotate_around_pivot_accurate
class TextSprite(UiSprite):
    main_font = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    def __init__(self, position : pygame.Vector2|tuple, rect_alignment : str|None, tag: int, text : str, name: str | None = None, attributes: dict = None, 
                 data: dict = None, zindex: int = 0, text_settings : tuple[pygame.Font, pygame.Color, bool]|None = None, 
                 text_stroke_settings : tuple[pygame.Color, int]|None = None, text_alingment : tuple[int, int]|None = None,       
                 colorkey : pygame.Color|tuple[int, int, int]|None = None):
        '''Text alignment is a tuple of (max_line_lentgh, newline_height). newline_height does nothing for now'''
        super().__init__(None, None, tag, name, False, attributes, data, None, zindex)
        self.text_settings : tuple[pygame.Font, pygame.Color, bool] = text_settings or (TextSprite.main_font, 'Black', False)
        self._text : str = text
        self._text_percent : float = 1
        self._true_text : str = text
        self.max_line_lentgh : int
        self.newline_height : int
        self.colorkey : pygame.Color|tuple[int, int, int]|None = colorkey
        if text_alingment:
            self.max_line_lentgh, self.newline_height, = text_alingment
        else:
            self.max_line_lentgh = 0
            self.newline_height = 5
        self._text_stroke_color : pygame.Color|str|None = None
        self._text_stroke_width : int|None = None
        if text_stroke_settings:
            self._text_stroke_color, self._text_stroke_width = text_stroke_settings
        self.rect_alignment = rect_alignment
        self._render_text(force_surf = True)
        self.rect = self.surf.get_rect()
        self.rect.__setattr__(self.rect_alignment, position) if self.rect_alignment is not None else self.rect.__setattr__('center', position)
        self.position = pygame.Vector2(self.rect.center)
        self._opacity = 1
    
        
    def _render(self):
        if self.rect_alignment:
            prev_rect = self.rect.copy()
            prev_mesure = prev_rect.__getattribute__(self.rect_alignment)
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
        if self.rect_alignment:
            self.rect.__setattr__(self.rect_alignment, prev_mesure)
            self._position = pygame.Vector2(self.rect.center)
    
    def _render_text(self, force_surf= False):
        if self._true_text == '' and force_surf == False: return
        font : pygame.Font
        color : pygame.Color|str
        AA_enabled : bool
        font, color, AA_enabled = self.text_settings
        if self._text_stroke_color and self._text_stroke_width:
            final_surf_size = (pygame.Vector2(self._text_stroke_width, self._text_stroke_width) * 2) + (1,1) + font.size(self._true_text)
            if self.colorkey:
                final_surf = pygame.Surface(final_surf_size)
                final_surf.fill(self.colorkey)
            else:
                final_surf = pygame.Surface(final_surf_size, pygame.SRCALPHA)

            first_text_sprite = font.render(self._true_text, AA_enabled, color, wraplength=self.max_line_lentgh)
            outline = font.render(self._true_text, AA_enabled, self._text_stroke_color, wraplength=self.max_line_lentgh)
            

            
            for ox in range(-1, 2):
                for oy in range(-1, 2):
                    if ox or oy or 1:
                        dx, dy = (ox + 1) * self._text_stroke_width, (oy + 1) * self._text_stroke_width
                        #if ((self._text_stroke_width + final_surf.get_width()) % 2):
                        #    dx += 0 if ox > 0 else 0
                        #if ((self.text_stroke_width + final_surf.get_height()) % 2):
                        #    dy += 0 if oy > 0 else 0
                        final_surf.blit(outline, (dx, dy))


            final_surf.blit(first_text_sprite, (self._text_stroke_width, self._text_stroke_width))            
            self.surf = final_surf
            if self.colorkey:
                self.surf.set_colorkey(self.colorkey)
        else:
            self.surf = font.render(self._true_text, AA_enabled, color, wraplength=self.max_line_lentgh, bgcolor=self.colorkey)
            if self.colorkey:
                self.surf.set_colorkey(self.colorkey)
    
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
    def text_stroke_width(self):
        return self._text_stroke_width
    
    @text_stroke_width.setter
    def text_stroke_width(self, new_val : int|None):
        if new_val != self._text_stroke_width:
            self._text_stroke_width = new_val
            self._render()

    @property
    def text_stroke_color(self):
        return self._text_stroke_color
    
    @text_stroke_color.setter
    def text_stroke_color(self, new_val : pygame.Color|str|None):
        if new_val != self._text_stroke_color:
            self._text_stroke_color = new_val
            self._render()