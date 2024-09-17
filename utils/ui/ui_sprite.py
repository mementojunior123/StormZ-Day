import pygame
from utils.helpers import rotate_around_pivot_accurate, ColorType
from utils.pivot_2d import Pivot2D



class UiFilter:
    def __init__(self, surf_or_color : pygame.Surface|pygame.Color, blend_mode : int) -> None:
        self.value : pygame.Surface|pygame.Color = surf_or_color
        self.blend_mode = blend_mode

    def apply(self, surface : pygame.Surface):
        t = type(self.value)
        if t == pygame.Surface:
            surface.blit(self.value, (0,0), special_flags=self.blend_mode)
        elif t == pygame.Color:
            surface.fill(self.value, special_flags=self.blend_mode)
        

class UiSprite:
    TAG_EVENT = pygame.event.custom_type()
    def __init__(self, surf : pygame.Surface, rect : pygame.Rect, tag : int, name : str|None = None, keep_og_surf = False, 
                 attributes : dict = None, data : dict = None, forced_og_surf : pygame.Surface = None, zindex : int = 0,
                 colorkey : ColorType|str|None = None):
        self.surf : pygame.Surface = surf
        if colorkey and (surf is not None):
            self.surf.set_colorkey(colorkey)
        self.og_surf : None|pygame.Surface
        if keep_og_surf:
            if forced_og_surf: self.og_surf = forced_og_surf
            else: self.og_surf = self.surf.copy()
        else:
            self.og_surf = None

        self.rect : pygame.Rect = rect if rect is not None else self.surf.get_rect() if self.surf is not None else None
        self.tag : int = tag
        self.name : str|None = name
        self.zindex : int = zindex
        
        self.visible : bool = True
        self.interactible : bool = True
        self.clickable : bool = True if self.tag != 0 else False
        self.use_pivot : bool = False
        self.has_per_pixel_alpha : bool = False
        if self.surf:
            if self.surf.get_alpha() == None: 
                self.has_per_pixel_alpha = True
            else:
                self.has_per_pixel_alpha = False
        
        if not attributes is None:
            for key in attributes:
                val = attributes[key]
                self.__setattr__(key, val)
        
        self.creation_attributes = attributes

        self.data = {} if data is None else data
        if self.surf:
            self._opacity : float = ((self.surf.get_alpha() or 255) / 255) or 1
        
        self._scale : pygame.Vector2 = pygame.Vector2(1,1)
        if self.rect:
            self._position = pygame.Vector2(self.rect.center)
        else:
            self._position = pygame.Vector2(0,0)
        self.filters : list[UiFilter] = []
        self._angle : float = 0
        self._pivot : Pivot2D = Pivot2D(self.position)
        self._pivot_origin : pygame.Vector2
        self._pivot_offset : pygame.Vector2
    
    def __getitem__(self, index):
        if index == 0: return self.surf
        if index == 1: return self.rect

    def _render(self):
        if self.og_surf is None:
            self.og_surf = self.surf.copy()
        else:
            pass
        has_modified = False
        scalex_offset, scaley_offset = self._scale.x - 1, self._scale.y - 1
        if abs(scalex_offset) > 0.001 or abs(scaley_offset) > 0.001:
            surf_to_mod = self.surf if has_modified else self.og_surf
            self.surf = pygame.transform.scale_by(surf_to_mod, self.scale)
            has_modified = True

        
        
        if abs(self._angle) > 0.001:
            surf_to_mod = self.surf if has_modified else self.og_surf
            if not self.use_pivot:
                self.surf, self.rect, self.position = rotate_around_pivot_accurate(surf_to_mod, self.position, self._angle, self.position, pygame.Vector2(0,0))
            else:
                self.surf, self.rect, self._position = self._pivot.rotate_image(surf_to_mod)
            has_modified = True

        opacity_offset =  1- self._opacity
        if abs(opacity_offset) > 0.002:
            if not has_modified: self.surf = self.og_surf.copy()
            self.surf.set_alpha(self._opacity * 255)
            has_modified = True
        for filter in self.filters:
            if not has_modified: self.surf = self.og_surf.copy()
            filter.apply(self.surf)

    @property
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, val):
        self._opacity = val
        if self.surf.get_alpha() is None: self.surf = self.surf.convert_alpha()
        self.surf.set_alpha(self._opacity * 255)
    
    @property
    def position(self) -> pygame.Vector2:
        return self._position
    
    @position.setter
    def position(self, new_val : pygame.Vector2):
        if self.use_pivot: raise AttributeError('Cannot set position when in Pivot mode: set UiSprite.position to false')
        self._position = new_val

    @property
    def pivot_origin(self) -> pygame.Vector2:
        return self._pivot.origin
    
    @pivot_origin.setter
    def pivot_origin(self, new_val : pygame.Vector2):
        if not self.use_pivot: raise AttributeError('To use the pivot, set UiSprite.use_pivot to True')
        self._pivot.origin = new_val
    
    @property
    def pivot_offset(self) -> pygame.Vector2:
        return self._pivot.pivot_offset
    
    @pivot_offset.setter
    def pivot_offset(self, new_val : pygame.Vector2):
        if not self.use_pivot: raise AttributeError('To use the pivot, set UiSprite.use_pivot to True')
        self._pivot.pivot_offset = new_val
        self._render()

    @property
    def angle(self) -> float:
        return self._angle
    
    @angle.setter
    def angle(self, val : float):
        self._angle = val
        self._pivot.angle = val
        self._render()
    
    @property
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, val):
        self._scale = val if type(val) == pygame.Vector2 else pygame.Vector2(val, val)
        self._render()
    
    def reset(self):
        self.surf = self.og_surf.copy()
        self._scale = pygame.Vector2(1,1)
        self._opacity = 1
        self._angle = 0
        self.filters = []
    
    def draw(self, display : pygame.Surface):
        if self.visible:
            display.blit(self.surf, self.rect)
    
    def on_click(self):
        if not self.clickable: return
        if not self.interactible: return
        attributes = {"tag" : self.tag, "name" : self.name, 'trigger_type' : 'click'}
        event = pygame.event.Event(UiSprite.TAG_EVENT, attributes)
        pygame.event.post(event)
    
    #def copy(self):
        #new_copy = UiSprite(self.surf.copy(), self.rect.copy(), self.tag, self.name, keep_og_surf=True, 
                            #attributes=self.creation_attributes, data=self.data, forced_og_surf=self.og_surf)
        #return new_copy