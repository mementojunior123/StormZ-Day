import pygame
from time import perf_counter
from collections import deque

from utils.my_timer import Timer
from core.event_manger import EventManger
import game.game_module
from core.settings import Settings
from core.bg_manager import BgManager
from core.ui import Ui
from core.menu import Menu
import core.menu
from game.game_module import Game
from core.game_storage import GameStorage
from core.task_scheduler import TaskScheduler
from utils.tween_module import TweenTrack, TweenChain
from utils.animation import AnimationTrack
import sys
import platform
from typing import Any

WEBPLATFORM = 'emscripten'

class Core:
    CORE_EVENT = pygame.event.custom_type()
    START_GAME = pygame.event.custom_type()
    END_GAME = pygame.event.custom_type()
    IS_DEBUG : bool = False
    def __init__(self) -> None:
        self.FPS = 60
        self.PERFORMANCE_MODE = False
        self.WEBPLATFORM = 'emscripten'
        self.CURRENT_PLATFORM = sys.platform
        self.main_display : pygame.Surface
        self.brightness_map = pygame.Surface((2000, 2000), pygame.SRCALPHA)
        pygame.draw.rect(self.brightness_map, (255, 255, 255, 0), (0,0, 2000, 2000))
        self.event_manager = EventManger()
        self.make_connections()

        self.active_fingers : dict[int, tuple[float, float]] = {}
        self.dt : float = 1
        self.last_dt_measurment : float = 0

        self.settings = Settings()
        self.bg_manager = BgManager()
        self.main_ui = Ui()
        self.menu = Menu()
        self.game = Game()
        self.storage = GameStorage()
        self.task_scheduler = TaskScheduler()
        self.delta_stream : deque[float] = deque([1 for _ in range(30)])
        self.dirty_display_rects : list[pygame.Rect] = []
        self.brightness_map_blend_mode = pygame.BLENDMODE_NONE

        self.global_timer : Timer = Timer(-1, perf_counter, 1)
        Timer.time_source = self.global_timer.get_time

        self.window_bools : dict = {'Shown' : True, 'input_focused' : True}

    def is_web(self) -> bool:
        return self.CURRENT_PLATFORM == WEBPLATFORM
    
    def setup_web(self, method : int = 1):
        if not self.is_web(): return
        if method == 1:
            platform.window.onfocus = self.continue_things
            platform.window.onblur = self.stop_things
        else:
            platform.EventTarget.addEventListener(platform.window, "blur", self.stop_things)
            platform.EventTarget.addEventListener(platform.window, "focus", self.continue_things)

    def init(self, main_display : pygame.Surface):
        self.main_display = main_display
    
    def close_game(self, event : pygame.Event):
        self.settings.save()
        pygame.quit()
        exit()
    
    def update_dt(self, target_fps : int|float = 60):
        if self.last_dt_measurment == 0:
            self.dt = 1
            self.last_dt_measurment = perf_counter()
        else:
            mark = perf_counter()
            self.dt = (mark - self.last_dt_measurment) * target_fps
            self.last_dt_measurment = mark
    
    def set_debug_message(self, text : str):
        debug_textsprite : TextSprite = core_object.main_ui.get_sprite('debug_sprite')
        if not debug_textsprite: return
        debug_textsprite.text = text
    
    def set_brightness(self, new_val : int):
        brightness = new_val
        abs_brightness = abs(new_val)
        if brightness >= 0:
            pygame.draw.rect(self.brightness_map, (abs_brightness, abs_brightness, abs_brightness), (0,0, 2000, 2000))
            self.brightness_map_blend_mode = pygame.BLEND_RGB_ADD
        else:
            pygame.draw.rect(self.brightness_map, (abs_brightness, abs_brightness, abs_brightness), (0,0, 2000, 2000))
            self.brightness_map_blend_mode = pygame.BLEND_RGB_SUB
    
    def make_connections(self):
        self.event_manager.bound_actions[pygame.QUIT] = [self.close_game]

        self.event_manager.bind(pygame.WINDOWHIDDEN, self.handle_window_event)
        self.event_manager.bind(pygame.WINDOWSHOWN, self.handle_window_event)
        self.event_manager.bind(pygame.WINDOWFOCUSGAINED, self.handle_window_event)
        self.event_manager.bind(pygame.WINDOWFOCUSLOST, self.handle_window_event)

        self.event_manager.bind(pygame.FINGERDOWN, self.process_touch_event)
        self.event_manager.bind(pygame.FINGERMOTION, self.process_touch_event)
        self.event_manager.bind(pygame.FINGERUP, self.process_touch_event)
    
    def process_touch_event(self, event : pygame.Event):
        if event.type == pygame.FINGERDOWN:
            x = event.x * self.main_display.get_width()
            y = event.y * self.main_display.get_height()
            self.active_fingers[event.finger_id] = (x,y)
        
        elif event.type == pygame.FINGERUP:
            self.active_fingers.pop(event.finger_id, None)
        
        elif event.type == pygame.FINGERMOTION:
            x = event.x * self.main_display.get_width()
            y = event.y * self.main_display.get_height()
            self.active_fingers[event.finger_id] = (x,y)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.active_fingers[10] = (event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            self.active_fingers[10] = (event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            self.active_fingers.pop(10, None)
    
    def process_core_event():
        pass

    def handle_window_event(self, event : pygame.Event):
        platform : str = sys.platform[0:]
        if platform != 'emscripten': return
        return
        if event.type == pygame.WINDOWFOCUSLOST:
            self.window_bools['input_focused'] = False
            self.set_debug_message('Window Unfocused')
            self.stop_things()

        elif event.type == pygame.WINDOWHIDDEN:
            self.window_bools['Shown'] = False
            self.set_debug_message('Window Hidden')
            self.global_timer.pause()
            self.game.pause()

        elif event.type == pygame.WINDOWSHOWN:
            self.window_bools['Shown'] = True
            return
            self.set_debug_message('Window Shown')
            self.global_timer.unpause()
        
        elif event.type == pygame.WINDOWFOCUSGAINED:
            self.window_bools['input_focused'] = True
            self.set_debug_message('Window Focused')
            self.continue_things()

    def check_window_focus(self):
        platform : str = sys.platform[0:]
        if platform != 'emscripten': return True
        result = pygame.display.get_active()
        self.set_debug_message('Window Focused') if result else self.set_debug_message('Window Unfocused')
        return pygame.key.get_focused()
    
    def stop_things(self, event : Any|None = None):
        self.global_timer.pause()
        self.game.pause()
        if event is not None: self.window_bools['input_focused'] = False 
    
    def continue_things(self, event : Any|None = None):
        self.global_timer.unpause() 
        if event is not None: self.window_bools['input_focused'] = True 


    def update(self):
        self.task_scheduler.update()
        TweenTrack.update_all()
        TweenChain.update_all()
        self.update_delta_stream()
        self.bg_manager.update()
        AnimationTrack.update_all_elements()
    
    def update_delta_stream(self):
        target_lentgh = round(30 / self.dt)
        current_lentgh = len(self.delta_stream)
        if current_lentgh == target_lentgh:
            self.delta_stream.popleft()
        elif current_lentgh > target_lentgh:
            self.delta_stream.popleft()
            self.delta_stream.popleft()
        self.delta_stream.append(self.dt)
    
    def get_fps(self):
        total = 0
        for delta in self.delta_stream:
            total += delta
        
        average = total / len(self.delta_stream)
        return 60 / average
    
    def __hints(self):
        global TextSprite
        from utils.ui.textsprite import TextSprite

core_object = Core()
setattr(core.menu, 'core_object', core_object)