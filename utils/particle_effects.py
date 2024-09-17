import pygame
from utils.my_timer import Timer
from utils.animation import Animation
import utils.interpolation as interpolation
from random import random
from math import sin, radians, cos
from game.sprite import Sprite
from utils.pivot_2d import Pivot2D

def __random_float(a, b):
    return random() * (b-a) + a

def rand_float(iterable):
    if iterable is None: return iterable
    t = type(iterable)
    if t == int or t == float: return iterable
    return __random_float(iterable[0], iterable[1])


def vec_from_angle(angle, magnitude = 1) -> pygame.Vector2:
    x = sin(radians(angle))
    y = cos(radians(angle)) * -1
    return pygame.Vector2(x, y) * magnitude


class Particle(Sprite):
    active_elements : list['Particle'] = []
    inactive_elements : list['Particle']  = []
    test_image = pygame.surface.Surface((4,4))
    pygame.draw.rect(test_image, 'White', (0, 0, 4, 4))

    def __init__(self) -> None:
        self._position = pygame.Vector2(0,0)
        self.lifetime : float = 0
        self.lifetime_timer : Timer = Timer(-1)
        self.pivot : Pivot2D|None = None

        self.velocity : pygame.Vector2
        self.accelaration : pygame.Vector2
        self.drag : float

        self.update_method : str = 'simulated'
        self.image : pygame.Surface
        self.rect : pygame.Rect
        self.textures : list[pygame.Surface]
        self.active = False
        self.kill_offscreen = True
        Particle.inactive_elements.append(self)
    
    def spawn(self, pos, lifetime, update_method, main_texture : pygame.Surface, velocity = None, accel = None, drag = None, 
              alt_textures = None, anim : Animation = None, destroy_offscreen : bool = False, angle = None, mag = None, copy_surf = False):
        self.position = pos

        if copy_surf is False:
            self.image = main_texture
            self.textures = alt_textures or []
        else:
            self.image = main_texture.copy()
            if alt_textures is None: self.textures = []
            else: self.textures = [surf.copy() for surf in alt_textures]

        self.rect = self.image.get_rect()
        self.rect.center = self.position

        self.lifetime = lifetime
        self.lifetime_timer.set_duration(lifetime)

        self.update_method = update_method
        self.velocity = velocity or pygame.Vector2(0,0)
        if angle is not None:
            if mag is None: mag = 1
            self.velocity += vec_from_angle(angle, mag)
        self.accelaration = accel or pygame.Vector2(0,0)
        self.drag = drag or 0
        self.active = True
        self.kill_offscreen= destroy_offscreen

        if anim:
            self.anim_track = anim.load(self)
            self.anim_track.play()
        else:
            self.anim_track = None
        
        Particle.unpool(self)
    
    def update(self, delta : float):
        if self.lifetime_timer.isover():
            self.destroy()
            return
        if self.kill_offscreen:
            if self.rect.colliderect(Particle.bounding_box) is False:
                self.destroy()
                return
        if self.update_method == 'simulated':

            self.velocity += self.accelaration * 0.5 * delta
            self.position += self.velocity * delta
            self.velocity += self.accelaration * 0.5 * delta

            self.velocity *=  ((1 - self.drag) ** delta)
            self.rect.center = self.position
            if self.anim_track is not None:
                self.anim_track.update()
        
        elif self.update_method == 'animated':
            self.anim_track.update()
    
    def draw(self, display : pygame.Surface):
        display.blit(self.image, self.rect)
    
    @classmethod
    def pool(cls, element):
        '''Transfers an element from active to inactive state. Nothing changes if the element is already inactive.'''
        if element in cls.active_elements:
            cls.active_elements.remove(element)
        
        if element not in cls.inactive_elements:
            cls.inactive_elements.append(element)
    
    @classmethod
    def unpool(cls, element):
        '''Transfers an element from inactive to active state. Nothing changes if the element is already active.'''
        if element not in cls.active_elements:
            cls.active_elements.append(element)
        
        if element in cls.inactive_elements:
            cls.inactive_elements.remove(element)
    
    @classmethod
    def clear_elements(cls):
        '''Pools every element of the class'''
        element: cls
        for element in cls.active_elements:
            cls.inactive_elements.append(element)
        cls.active_elements.clear() 
    
    
    def destroy(self):
        cls = self.__class__
        cls.pool(self)
        self.active = False
    
    def is_active(self):
        return self in Particle.active_elements

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
    
class ParticleEffect:
    elements : list['ParticleEffect'] = []
    data : dict[str, dict] = {}
    def __init__(self, data, persistance, dynamic_origin = False) -> None:
        self.data = data
        ParticleEffect.elements.append(self)
        self.tracks : list[ParticleEffectTrack] = []
        self.plays_remaining = None
        self.destroy_on_end = True
        self.is_persistent = persistance
        self.dynamic_origin = dynamic_origin
        self.position = pygame.Vector2(0,0)
    
    @classmethod
    def load_effect(cls, name, persistance = False, dynamic_origin = False):
        if name in cls.data:
            return ParticleEffect(cls.data[name], persistance, dynamic_origin)
        return None
    
    def emit(self, track : 'ParticleEffectTrack'):
        new_particle : Particle = Particle.inactive_elements[0]

        offset = pygame.Vector2(rand_float(self.data['offset_x']), rand_float(self.data['offset_y']))
        if not self.dynamic_origin:
            new_pos = track.origin + offset
        else:
            new_pos = self.position + offset

        life = rand_float(self.data['lifetime'])
        if (self.data['velocity_x'] is None) or (self.data['velocity_y'] is None):
            velocity = None
        else:
            velocity = pygame.Vector2(rand_float(self.data['velocity_x']), rand_float(self.data['velocity_y']))
        drag = rand_float(self.data['drag'])
        accel = pygame.Vector2(rand_float(self.data['accel_x']), rand_float(self.data['accel_y']))
        kill_offscreen = self.data.get('destroy_offscreen', True)
        angle = rand_float(self.data['angle'])
        mag = rand_float(self.data['speed'])
        new_particle.spawn(new_pos, life, self.data['update_method'], self.data['main_texture'], 
                           velocity=velocity, accel=accel, drag=drag, alt_textures=self.data['alt_textures'], anim=self.data['animation'], 
                           destroy_offscreen=kill_offscreen, angle=angle, mag=mag, copy_surf = self.data['copy_surface'])
        
        track.active.append(new_particle)
        track.total_count += 1
    
    def play(self, pos : pygame.Vector2):
        new_track = ParticleEffectTrack(pos, self.data['cooldown'])
        self.tracks.append(new_track)
        for _ in range(self.data['init_spawn_count']):
            self.emit(new_track)

    def update(self):
        if len(self.tracks) <= 0 and self.is_persistent == False:
            self.destroy()
            return
        to_del = []
        for track in self.tracks:
            self.continue_track(track)
            if track.ended: 
                to_del.append(track)

        for track in to_del:
            self.tracks.remove(track)

    def continue_track(self, track : 'ParticleEffectTrack'):
        if track.timer.isover() and track.total_count < self.data['target_spawn_count']:
            count, remainder = divmod(track.timer.get_time() , track.timer.duration)
            track.timer.restart()
            if track.can_emit:
                for _ in range(round(count)):
                    self.emit(track)
            track.timer.start_time -= remainder

            

        if (len(track.active) == 0) and ((track.total_count >= self.data['target_spawn_count']) or (track.can_emit == False)):
            track.ended = True
        
        to_del = []
        for part in track.active:
            if part.is_active() == False:
                to_del.append(part)

        for part in to_del:
            track.active.remove(part)

    def stop(self):
        for track in self.tracks:
            track.stop_emission()
    
    def cancel_all(self):
        for track in self.tracks:
            track.cleanup()
        self.tracks.clear()


    def destroy(self):
        ParticleEffect.elements.remove(self)
        self.stop()
    
    @classmethod
    def update_all(cls):
        for element in cls.elements:
            element.update()
    
    def shedule_destruction(self):
        self.destroy_on_end = True


class ParticleEffectTrack:
    def __init__(self, origin, cooldown) -> None:
        self.total_count = 0
        self.active : list[Particle] = []
        self.timer : Timer = Timer(cooldown)
        self.origin = origin
        self.ended = False
        self.can_emit = True
    
    def cleanup(self):
        for part in self.active:
            part.destroy()
        self.active.clear()
    
    def stop_emission(self):
        self.can_emit = False

TEMPLATE = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [0,0], 'velocity_y' : [0,0], 'angle' : None, 'speed' : None,
            'accel_x' : [0,0], 'accel_y' : [0,0], 'drag' : [0, 0],
            'init_spawn_count' : 0, 'cooldown' : 0.25, 'target_spawn_count' : 0, 'lifetime' : [0,0], 'part_per_wave' : 1,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : None,
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : False}

