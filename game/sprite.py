import pygame
from utils.animation import AnimationTrack, Animation
from typing import Any
from utils.helpers import is_sorted
from utils.pivot_2d import Pivot2D
from inspect import isclass

class Sprite:
    '''Base class for all game objects.'''
    active_elements : list['Sprite'] = []
    inactive_elements : list['Sprite']  = []
    ordered_sprites : list['Sprite'] = []
    registered_classes : list['Sprite'] = []
    SPRITE_CLICKED : int = pygame.event.custom_type()

    def __init__(self) -> None:
        self._position : pygame.Vector2
        self.pivot : Pivot2D|None = None
        self._image : pygame.Surface
        self.rect : pygame.Rect
        self.mask : pygame.Mask
        self.dynamic_mask : bool = False
        self.zindex : int
        self.animation_tracks : dict[str, AnimationTrack]
        Sprite.inactive_elements.append(self)
        self._zombie : bool = False
    
    @property
    def image(self) -> pygame.Surface:
        return self._image
    
    @image.setter
    def image(self, new_surf : pygame.Surface):
        self._image = new_surf
        if self.dynamic_mask:
            if new_surf is None:
                self.mask = None
            else:
                self.mask = pygame.mask.from_surface(new_surf)
    
    def align_rect(self):
        self.rect.center = round(self.true_position)
    
    def move_rect(self, anchor : str, position : pygame.Vector2|int):
        self.rect.__setattr__(anchor, position)
        self.true_position = pygame.Vector2(self.rect.center)
    
    def clamp_rect(self, area : pygame.Rect):
        if self.rect.left < area.left: self.move_rect('left', area.left)
        if self.rect.right > area.right: self.move_rect('right', area.right)
        if self.rect.top < area.top: self.move_rect('top', area.top)
        if self.rect.bottom > area.bottom: self.move_rect('bottom', area.bottom)
    
    @property
    def position(self) -> pygame.Vector2:
        if not hasattr(self, 'pivot'): self.pivot = None
        if self.pivot is None:
            return self._position
        else:
            return self.pivot.origin
    
    @position.setter
    def position(self, new_val : pygame.Vector2):
        if not hasattr(self, 'pivot'): self.pivot = None
        if self.pivot is None:
            self._position = new_val
        else:
            self.pivot.origin = new_val
        
        self.align_rect()
    
    @property
    def true_position(self) -> pygame.Vector2:
        if not hasattr(self, 'pivot'): self.pivot = None
        if self.pivot is None:
            return self._position
        else:
            return self.pivot.position
    
    @true_position.setter
    def true_position(self, new_val):
        if not hasattr(self, 'pivot'): self.pivot = None
        if self.pivot is None:
            self._position = new_val
        else:
            self.pivot.position = new_val
        
        self.align_rect()
    
    @property
    def angle(self) -> float:
        if not hasattr(self, 'pivot'): self.pivot = None
        return self.pivot.angle
    
    @angle.setter
    def angle(self, new_val : float):
        if not hasattr(self, 'pivot'): self.pivot = None
        self.pivot.angle = new_val
        self.image, self.rect, new_pos = self.pivot.rotate_og_image() if self.pivot.original_image else self.pivot.rotate_image()
        self.align_rect()

    @classmethod
    def register_class(cls, class_to_register : 'Sprite'):
        if class_to_register not in cls.registered_classes:
            cls.registered_classes.append(class_to_register)
    
    @property
    def active(self):
        return (self in self.__class__.active_elements) or (self in Sprite.active_elements)

    @classmethod
    def pool(cls, element):
        '''Transfers an element from active to inactive state. Nothing changes if the element is already inactive.'''
        if element in cls.active_elements:
            cls.active_elements.remove(element)
        
        if element in Sprite.active_elements:
            Sprite.active_elements.remove(element)
        
        if element not in cls.inactive_elements:
            cls.inactive_elements.append(element)

        if element not in Sprite.inactive_elements:
            Sprite.inactive_elements.append(element)
    
    @classmethod
    def unpool(cls, element):
        '''Transfers an element from inactive to active state. Nothing changes if the element is already active.'''

        if element not in cls.active_elements:
            cls.active_elements.append(element)
        
        if element not in Sprite.active_elements:
            Sprite.active_elements.append(element)


        if element in cls.inactive_elements:
            cls.inactive_elements.remove(element)

        if element in Sprite.inactive_elements:
            Sprite.inactive_elements.remove(element)


    
    @classmethod
    def pool_elements(cls):
        '''Pools every element of the class'''
        while len(cls.active_elements) > 0:
            cls.pool(cls.active_elements[0])
    
    @staticmethod
    def pool_all_sprites():
        while len(Sprite.active_elements) > 0:
            element = Sprite.active_elements[0]
            cls = element.__class__
            cls.pool(element)


    @classmethod
    def spawn(cls):
        pass

    def clean_instance(self):
        self.image = None
        self.rect = None
        self._position = None
        self.pivot = None
        self.mask = None
        self.zindex = None
        self.animation_tracks = None

    def kill_instance(self):
        self.clean_instance()
        self.self_destruct()
    
    def kill_instance_safe(self):
        self._zombie = True
    
    @classmethod
    def clean_all_instances(cls):
        for element in cls.active_elements:
            element.clean_instance()
    
    @classmethod
    def kill_all_instances(cls):
        for element in cls.active_elements:
            element.clean_instance()
        cls.pool_elements()
    
    @classmethod
    def clean_all_sprites(cls):
        for element in Sprite.active_elements:
            element.clean_instance()
    
    @classmethod
    def kill_all_sprites(cls):
        for element in Sprite.active_elements:
            element.clean_instance()
        Sprite.pool_all_sprites()
    
    def update(self, delta : float):
        pass
    
    @classmethod
    def update_class(cls, delta : float):
        pass

    def self_destruct(self):
        cls = self.__class__
        cls.pool(self)
    
    @staticmethod
    def clear_zombies(elements : list['Sprite']):
        to_kill : list[Sprite] = []
        for element in elements:
            if element._zombie:
                element._zombie = False
                to_kill.append(element)
        for element in to_kill:
            element.kill_instance()

    @classmethod
    def update_all(cls, delta : float):
        element : cls
        for element in cls.active_elements:
            element.update(delta)
        Sprite.clear_zombies(cls.active_elements)
    
    @classmethod
    def update_all_sprites(cls, delta : float):
        element : Sprite
        for element in Sprite.active_elements:
            element.update(delta)
        Sprite.clear_zombies(Sprite.active_elements)
    
    @classmethod
    def update_all_registered_classes(cls, delta : float):
        sprite_subclass : Sprite
        for sprite_subclass in Sprite.registered_classes:
            sprite_subclass.update_class(delta)
    
    def play_animation(self, animation : Animation, time_scale = 1):
        track = animation.load(self)
        track.play()
        if time_scale != 1:
            track.set_time_scale(time_scale)
        
        self.animation_tracks[animation.name] = track

    def animate(self):
        for name in self.animation_tracks:
            val = self.animation_tracks[name]
            val.update()
    
    def draw(self, display : pygame.Surface):
        display.blit(self.image, self.rect)
    
    @classmethod
    def draw_all(cls, display):
        element : cls
        for element in cls.active_elements:
            element.draw(display)

    @property
    def x(self):
       return self.position.x
    @x.setter
    def x(self, value):
        self.position.x = value
    @property
    def y(self):
        return self.position.y
    @y.setter
    def y(self, value):
        self.position.y = value


    def is_colliding(self, other : 'Sprite'):
        if not self.rect.colliderect(other.rect): return False
        if self.mask.overlap(other.mask,(other.rect.x - self.rect.x ,other.rect.y - self.rect.y)): return True
        return False

    def is_collding_rect(self, other : 'Sprite'):
        return self.rect.colliderect(other.rect)

    def get_colliding(self, collision_groups : list[list['Sprite']]):
        '''Returns the first sprite colliding this sprite within collision_group or None if there arent any. Uses mask collision.'''
        try:
            collision_groups[0]
        except TypeError:
            collision_groups = [collision_groups]
        for collision_group in collision_groups:
            actual_group = collision_group.active_elements if isclass(collision_group) else collision_group
            for element in actual_group:
                if self.is_colliding(element) and not element._zombie: return element     
        return None
    
    def get_rect_colliding(self, collision_groups : list[list['Sprite']]):
        '''Returns the first sprite colliding this sprite within collision_group or None if there arent any. Uses a bounding box check.'''
        try:
            collision_groups[0]
        except TypeError:
            collision_groups = [collision_groups]
        for collision_group in collision_groups:
            actual_group = collision_group.active_elements if isclass(collision_group) else collision_group
            for element in actual_group:
                if self.is_collding_rect(element) and not element._zombie: return element
        return None
    
    def get_all_colliding(self, collision_groups : list[list['Sprite']]) -> list['Sprite']:
        '''Returns all entities colliding this sprite within collision_group. Uses mask collision.'''
        try:
            collision_groups[0]
        except TypeError:
            collision_groups = [collision_groups]
        return_val = []
        for collision_group in collision_groups:
            actual_group = collision_group.active_elements if isclass(collision_group) else collision_group
            for element in actual_group:
                if self.is_colliding(element) and not element._zombie:
                    return_val.append(element)
        return return_val

    def get_all_rect_colliding(self, collision_groups : list[list['Sprite']]):
        '''Returns all entities colliding this sprite within collision_group. Uses a bounding box check.'''
        try:
            collision_groups[0]
        except TypeError:
            collision_groups = [collision_groups]
        return_val = []
        for collision_group in collision_groups:
            actual_group = collision_group.active_elements if isclass(collision_group) else collision_group
            for element in actual_group:
                if self.is_collding_rect(element) and not element._zombie: return_val.append(element)
        return return_val

    def on_collision(self, other : 'Sprite'):
        pass

    def is_active(self):
        return self in self.__class__.active_elements
    
    @classmethod
    def draw_all_sprites(cls, display):
        #if not is_sorted(cls.active_elements, key=lambda sprite : sprite.zindex):
        cls.active_elements.sort(key=lambda sprite : sprite.zindex)
        element : Sprite
        for element in cls.active_elements:
            element.draw(display)

    
    @classmethod
    def get_sprite_class_by_name(cls, name : str) -> 'Sprite':
        for sprite_class in cls.registered_classes:
            if sprite_class.__name__ == name:
                return sprite_class
        return None
    
    @classmethod
    def handle_mouse_event(cls, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.touch: return
            press_pos : tuple = event.pos
            hit = [sprite for sprite in Sprite.active_elements if sprite.rect.collidepoint(press_pos)]
            if len(hit) == 0: return
            hit.sort(key = lambda sprite : sprite.zindex)
            new_event = pygame.event.Event(Sprite.SPRITE_CLICKED, {'main_hit' : hit[-1], 'all_hit' : hit, 'pos' : press_pos,
                                                                   'finger_id' : -1})
            pygame.event.post(new_event)
    
    @classmethod
    def handle_touch_event(cls, event : pygame.Event):
        if event.type == pygame.FINGERDOWN:
            x = event.x * core_object.main_display.get_width()
            y = event.y * core_object.main_display.get_height()
            press_pos : tuple[int, int] = (round(x), round(y))
            hit = [sprite for sprite in Sprite.active_elements if sprite.rect.collidepoint(press_pos)]
            if len(hit) == 0: return
            hit.sort(key = lambda sprite : sprite.zindex)
            new_event = pygame.event.Event(Sprite.SPRITE_CLICKED, {'main_hit' : hit[-1], 'all_hit' : hit, 'pos' : press_pos,
                                                                   'finger_id' : event.finger_id})
            pygame.event.post(new_event)
    
    @classmethod
    def _core_hint(cls):
        global core_object
        from core.core import core_object
            