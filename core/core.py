import pygame
from time import perf_counter
from collections import deque

from utils.my_timer import Timer
from core.event_manger import EventManger
import game.game_module
from game.sprite import Sprite
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
    IS_DEBUG : bool = True
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
        self.debug_sprite : TextSprite
        self.fps_sprite : TextSprite
        self.cycle_timer : Timer = Timer(-1)
        self.frame_counter : int = 0

    def is_web(self) -> bool:
        return self.CURRENT_PLATFORM == WEBPLATFORM
    
    def setup_web(self, method : int = 1):
        if not self.is_web(): return
        if method == 1:
            platform.window.onfocus = self.continue_things
            platform.window.onblur = self.stop_things
            platform.window.onbeforeunload = self.save_game
        else:
            platform.EventTarget.addEventListener(platform.window, "blur", self.stop_things)
            platform.EventTarget.addEventListener(platform.window, "focus", self.continue_things)
    
    def load_game(self):
        self.settings.set_defualt({'Brightness' : 0, "ControlMethod" : None})

        self.load_settings()
        self.load_storage()
    
    def load_storage(self):
        if not self.is_web(): self.storage.load_from_file()
        else: 
            self.storage.load_from_web()
    
    def load_settings(self):
        if not self.is_web(): self.settings.load()
        else: self.settings.load_web()
    
    def save_game(self):
        self.save_settings()
        self.save_storage()
    
    def save_storage(self):
        if not self.is_web(): self.storage.save_to_file()
        else: self.storage.save_to_web()
    
    def save_settings(self):
        if not self.is_web(): self.settings.save()
        else: self.settings.save_web()

    def init(self, main_display : pygame.Surface):
        self.main_display = main_display
        
    
    def setup_debug_sprites(self):
        self.fps_sprite = TextSprite(pygame.Vector2(10, 535), 'bottomleft', 0, 'FPS : 0', 'fps_sprite', 
                            text_settings=(self.game.font_40, 'White', False), text_stroke_settings=('Black', 2),
                            text_alingment=(9999, 5), colorkey=(255, 0,0))

        self.debug_sprite = TextSprite(pygame.Vector2(15, 200), 'midright', 0, '', 'debug_sprite', 
                                text_settings=(self.game.font_40, 'White', False), text_stroke_settings=('Black', 2),
                                text_alingment=(9999, 5), colorkey=(255, 0,0), zindex=999)
        
        self.cycle_timer.set_duration(0.1)
    
    def start_game(self, event : pygame.Event):
        if event.type != self.START_GAME: return
        
        self.menu.prepare_exit()
        self.game.start_game()
        self.setup_debug_sprites()

        self.event_manager.bind(pygame.MOUSEBUTTONDOWN, Sprite.handle_mouse_event)
        self.event_manager.bind(pygame.FINGERDOWN, Sprite.handle_touch_event)
        self.event_manager.bind(pygame.KEYDOWN, self.detect_game_exit)

        
        if self.IS_DEBUG: 
            self.main_ui.add(self.fps_sprite)
            self.main_ui.add(self.debug_sprite)
        
    def detect_game_exit(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_ESCAPE:
                self.end_game(None)
            #elif event.key == pygame.K_F1:
                #pygame.image.save_extended(core.main_display, 'assets/screenshots/game_capture2.png', '.png')
    
    def end_game(self, event : pygame.Event = None):
        victory : bool
        if event:
            victory = event.victory
        else:
            victory = False
        tokens_gained = ((self.game.wave_count * 5)  + (self.game.score // 12) + 10) if (self.game.wave_count > 0) and (self.game.score > 0) else 0
        self.storage.upgrade_tokens += tokens_gained
        self.menu.prepare_entry(4)
        self.menu.enter_stage4(self.game.score, self.game.wave_count, tokens_gained, victory)
        if self.game.score > self.storage.high_score:
            self.storage.high_score = self.game.score
        if self.game.wave_count > self.storage.high_wave:
            self.storage.high_wave = self.game.wave_count
        
        self.main_ui.clear_all()
        self.game.end_game()
        

        self.event_manager.unbind(pygame.MOUSEBUTTONDOWN, Sprite.handle_mouse_event)
        self.event_manager.unbind(pygame.FINGERDOWN, Sprite.handle_touch_event)
        self.event_manager.unbind(pygame.KEYDOWN, self.detect_game_exit)
        if self.menu.USE_RESULT_THEME:
            self.bg_manager.play(self.menu.main_theme, 1, loops=-1)
        elif not victory:
            self.bg_manager.play(self.menu.fail_theme, 1, loops=1)
        else:
            self.bg_manager.play(self.menu.victory_theme, 1, loops=1)
        
        self.save_storage()

    
    def close_game(self, event : pygame.Event):
        if not self.is_web(): self.settings.save()
        else: self.settings.save_web()
        if not self.is_web(): self.storage.save_to_file()
        else: self.storage.save_to_web()
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

        self.event_manager.bind(self.START_GAME, self.start_game)
        self.event_manager.bind(self.END_GAME, self.end_game)

        self.event_manager.bind(pygame.WINDOWHIDDEN, self.handle_window_event)
        self.event_manager.bind(pygame.WINDOWSHOWN, self.handle_window_event)
        self.event_manager.bind(pygame.WINDOWFOCUSGAINED, self.handle_window_event)
        self.event_manager.bind(pygame.WINDOWFOCUSLOST, self.handle_window_event)

        self.event_manager.bind(pygame.FINGERDOWN, self.process_touch_event)
        self.event_manager.bind(pygame.FINGERMOTION, self.process_touch_event)
        self.event_manager.bind(pygame.FINGERUP, self.process_touch_event)
        
        #test code for emulating touch input
        self.event_manager.bind(pygame.MOUSEBUTTONDOWN, self.process_touch_event)
        self.event_manager.bind(pygame.MOUSEMOTION, self.process_touch_event)
        self.event_manager.bind(pygame.MOUSEBUTTONUP, self.process_touch_event)
    
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
            if event.touch: return
            if not self.IS_DEBUG: return
            finger_id : int = 10
            x : float = event.pos[0] / self.main_display.get_width()
            y : float = event.pos[1] / self.main_display.get_height()
            pygame.event.post(pygame.Event(pygame.FINGERDOWN, {'finger_id' : finger_id, 'x' : x, 'y' : y}))
        
        elif event.type == pygame.MOUSEMOTION:
            if event.touch: return
            if not self.IS_DEBUG: return
            finger_id : int = 10
            x : float = event.pos[0] / self.main_display.get_width()
            y : float = event.pos[1] / self.main_display.get_height()
            pygame.event.post(pygame.Event(pygame.FINGERMOTION, {'finger_id' : finger_id, 'x' : x, 'y' : y}))

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.touch: return
            if not self.IS_DEBUG: return
            finger_id : int = 10
            x : float = event.pos[0] / self.main_display.get_width()
            y : float = event.pos[1] / self.main_display.get_height()
            pygame.event.post(pygame.Event(pygame.FINGERUP, {'finger_id' : finger_id, 'x' : x, 'y' : y}))
    
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
    
    def _hints(self):
        global TextSprite
        from utils.ui.textsprite import TextSprite

core_object = Core()
setattr(core.menu, 'core_object', core_object)