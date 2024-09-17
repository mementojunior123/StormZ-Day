"I just copied roblox's homework on this one. For the better or the worse."

import pygame
import utils.interpolation as interpolation
from utils.my_timer import Timer
from typing import Callable, Any
from time import perf_counter

def new_tween(target : object, info : 'TweenInfo', goal : dict, use_compatibilty_lerp = True, update_manually = False, play_now = True,
              time_source : Callable[[], float]|None = None, time_factor : float = 1):
    new_track = TweenTrack(target, info, goal, use_compatibilty_lerp, time_source, time_factor)
    if not update_manually:
        TweenTrack.elements.append(new_track)
    if play_now:
        new_track.play()
    return new_track

class TweenTrack:
    elements : list['TweenTrack'] = []
    def __init__(self, target : object, info : 'TweenInfo', goal : dict[str, Any], use_compat_lerp = True,
              time_source : Callable[[], float]|None = None, time_factor : float = 1) -> None:
        self.target = target
        self.info = info
        self.goal = goal
        self.start : dict[str, Any] = {}
        self.timer : Timer = None
        self.use_compatibilty_lerp : bool = use_compat_lerp
        self.is_playing = False
        self.has_finished = False
        self._can_play = True
        
        self.time_source : Callable[[], float]|None = time_source
        self.time_factor : float = time_factor
    
    @staticmethod
    def stall_tween(time : float):
        return TweenTrack(None, TweenInfo(lambda t: 0, time), {})
    
    @staticmethod
    def get_chained_attribute(obj : object, name : str) -> Any:
        steps = name.split('.')
        step_count = len(steps)
        if step_count != 1:
            current = obj
            for index, step in enumerate(steps):
                current = current.__getattribute__(step)
                if index + 2 >= step_count: break
            final_target = current
            reach = steps[-1]
        else:
            final_target = obj
            reach = name
    
        return final_target.__getattribute__(reach)
    
    @staticmethod
    def set_chained_attribute(obj : object, name : str, value : Any):
        steps = name.split('.')
        step_count = len(steps)
        if step_count != 1:
            current = obj
            for index, step in enumerate(steps):
                current = current.__getattribute__(step)
                if index + 2 >= step_count: break
            final_target = current
            reach = steps[-1]
        else:
            final_target = obj
            reach = name
        final_target.__setattr__(reach, value)

    def play(self):
        if not self._can_play: return
        for attr in self.goal:
            self.start[attr] = self.get_chained_attribute(self.target, attr)
        self.timer = Timer(self.info.time, self.time_source, self.time_factor)
        self.has_finished = False
        self.is_playing = True
    
    def stop(self):
        self.is_playing = False
        self.timer = None
    
    def destroy(self):
        self.start.clear()
        self.goal.clear()
        self.info = None
        self.target = None
        self.is_playing = False
        self.timer = None
        self.is_playing = False
        self.has_finished = False
        self._can_play = False
        if self in TweenTrack.elements:
            TweenTrack.elements.remove(self)
    def pause(self):
        self.is_playing = False
        if self.timer:  
            self.timer.pause()
    
    def unpause(self):
        if self.timer:
            self.is_playing = True
            self.timer.unpause()
        else:
            self.play()

    def update(self):
        if not self.timer: return
        if not self.is_playing: return
        alpha = self.timer.get_time() / self.timer.duration
        if alpha > 1: 
            alpha = 1
            self.has_finished = True
            self.is_playing = False
        lerp_func : Callable[[Any, Any, float], Any]
        if self.use_compatibilty_lerp:
            lerp_func = interpolation.compatibilty_lerp
        else:
            lerp_func = interpolation.lerp
        for attr in self.goal:
            result = lerp_func(self.start[attr], self.goal[attr], self.info.easying_style(alpha))
            #print(f'{self.start[attr]} --> {self.goal[attr]} : {result}')
            self.set_chained_attribute(self.target, attr, result)
      
    @classmethod
    def update_all(cls):
        to_cleanup = []
        for element in cls.elements:
            element.update()
            if element.has_finished:
                to_cleanup.append(element)
        for element in to_cleanup:
            cls.elements.remove(element)


class TweenInfo:
    def __init__(self, easing_func : Callable[[float], float], time : float) -> None:
        self.easying_style = easing_func
        self.time = time


class TweenChain:
    elements : list['TweenChain'] = []
    def __init__(self, target : object, steps : list[tuple[TweenInfo, dict[str, Any]]], use_compat_lerp = True,
              time_source : Callable[[], float]|None = None, time_factor : float = 1) -> None:
        self.target = target
        self.current_step : int|None = None
        self.current_track : TweenTrack = None
        self.steps = steps
        self.timer : Timer = None
        self.use_compatibilty_lerp : bool = use_compat_lerp
        self.is_playing : bool = False
        self.has_finished : bool = False
        self.step_count = len(steps)

        self.time_source : Callable[[], float] = time_source
        self.time_factor : float = time_factor
    
    def register(self):
        TweenChain.elements.append(self)
    
    def play(self):
        self.current_step = 0
        first_track = self.get_track_from_step(0)
        first_track.play()
        self.current_track = first_track
        self.is_playing = True

    def stop(self):
        self.is_playing = False
        self.current_track = None
    
    def pause(self):
        self.is_playing = False
        if self.current_track.timer:
            self.current_track.timer.pause()
    
    def unpause(self):
        if self.current_track.timer:
            self.is_playing = True
            self.current_track.timer.unpause()
        else:
            self.play()

    def get_track_from_step(self, step : int):
        info1, goal1 = self.steps[step]
        return TweenTrack(self.target, info1, goal1, self.use_compatibilty_lerp, self.time_source, self.time_factor)
        
    def update(self):
        if not self.current_track: return
        if not self.is_playing: return
        self.current_track.update()
        if self.current_track.has_finished:
            self.current_step +=1
            if self.current_step >= self.step_count:
                self.has_finished = True
                self.is_playing = False
                self.current_track = None
                return
            self.current_track = self.get_track_from_step(self.current_step)
            self.current_track.play()
    
    @classmethod
    def update_all(cls):
        to_cleanup = []
        for element in cls.elements:
            element.update()
            if element.has_finished:
                to_cleanup.append(element)
        for element in to_cleanup:
            cls.elements.remove(element)