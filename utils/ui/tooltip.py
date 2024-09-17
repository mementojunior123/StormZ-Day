import pygame
from utils.ui.textsprite import TextSprite
from utils.helpers import ColorType
class ToolTip(TextSprite):
    def __init__(self, position : pygame.Vector2|tuple, rect_alignment : str|None, tag: int, text : str, area : pygame.Rect, 
                 name: str | None = None, attributes: dict = None, data: dict = None, zindex: int = 0, 
                 text_settings : tuple[pygame.Font, pygame.Color, bool]|None = None, text_stroke_settings : tuple[pygame.Color, int]|None = None, 
                 text_alingment : tuple[int, int]|None = None, colorkey : ColorType|None = None):     
        self.hover_area : pygame.Rect = area
        self.is_hovered : bool = False
        super().__init__(position, rect_alignment, tag, text, name, attributes, data, zindex, 
                         text_settings, text_stroke_settings, text_alingment, colorkey)
        
        
    
    def update(self, delta: float):
        self.is_hovered = self.hover_area.collidepoint(pygame.mouse.get_pos())
    
    def draw(self, display: pygame.Surface):
        if self.visible and self.is_hovered:
            display.blit(self.surf, self.rect)
