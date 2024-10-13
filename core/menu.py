import pygame
from utils.helpers import ColorType, scale_surf, to_roman, Callable, paint_upgrade_bar, reset_upgrade_bar, make_upgrade_bar
import random
from utils.ui.ui_sprite import UiSprite
from utils.ui.textsprite import TextSprite
from utils.ui.tooltip import ToolTip
from utils.ui.base_ui_elements import BaseUiElements
import utils.tween_module as TweenModule
import utils.interpolation as interpolation
from utils.my_timer import Timer
from utils.ui.brightness_overlay import BrightnessOverlay
from math import floor

class BaseMenu:
    font_40 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 70)
    font_150 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 150)

    def __init__(self) -> None:
        self.stage : int
        self.stages : list[list[UiSprite]]
        self.bg_color : ColorType
        self.temp : dict[UiSprite, Timer] = {}
        
    def init(self):
        self.bg_color = (94, 129, 162)
        self.stage = 1
        self.stage_data : list[dict] = [None, {}]
        self.stages = [None, []]
    
    def add_temp(self, element : UiSprite, time : float|Timer, override = False, time_source : Callable[[], float]|None = None, time_scale : float = 1):
        if element not in self.temp or override == True:
            timer = time if type(time) == Timer else Timer(time, time_source, time_scale)
            self.temp[element] = timer
    def alert_player(self, text : str, alert_speed : float = 1):
        text_sprite = TextSprite(pygame.Vector2(core_object.main_display.get_width() // 2, 90), 'midtop', 0, text, 
                        text_settings=(core_object.menu.font_60, 'White', False), text_stroke_settings=('Black', 2), colorkey=(0,255,0))
        
        text_sprite.rect.bottom = -5
        text_sprite.position = pygame.Vector2(text_sprite.rect.center)
        temp_y = text_sprite.rect.centery
        self.add_temp(text_sprite, 5)
        TInfo = TweenModule.TweenInfo
        goal1 = {'rect.centery' : 50, 'position.y' : 50}
        info1 = TInfo(interpolation.quad_ease_out, 0.3 / alert_speed)
        goal2 = {'rect.centery' : temp_y, 'position.y' : temp_y}
        info2 = TInfo(interpolation.quad_ease_in, 0.4 / alert_speed)
        
        on_screen_time = 1 / alert_speed
        info_wait = TInfo(lambda t : t, on_screen_time)
        goal_wait = {}

        chain = TweenModule.TweenChain(text_sprite, [(info1, goal1), (info_wait, goal_wait), (info2, goal2)], True)
        chain.register()
        chain.play()

    def add_connections(self):
        core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.bind(UiSprite.TAG_EVENT, self.handle_tag_event)
    
    def remove_connections(self):
        core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.unbind(UiSprite.TAG_EVENT, self.handle_tag_event)
    
    def __get_core_object(self):
        global core_object
        from core.core import core_object

    def render(self, display : pygame.Surface):
        sprite_list = [sprite for sprite in (self.stages[self.stage] + list(self.temp.keys())) if sprite.visible == True]
        sprite_list.sort(key = lambda sprite : sprite.zindex)
        for sprite in sprite_list:
            sprite.draw(display)
        
    
    def update(self, delta : float):
        to_del = []
        for item in self.temp:
            if self.temp[item].isover(): to_del.append(item)
            item.update(delta)
        for item in to_del:
            self.temp.pop(item)

        stage_data = self.stage_data[self.stage]
        for sprite in self.stages[self.stage]:
            if sprite: sprite.update(delta)
    
    def prepare_entry(self, stage : int = 1):
        self.add_connections()
        self.stage = stage
    
    def prepare_exit(self):
        self.stage = 0
        self.remove_connections()
        self.temp.clear()
    
    def goto_stage(self, new_stage : int):
        self.stage = new_stage

    def launch_game(self):
        new_event = pygame.event.Event(core_object.START_GAME, {})
        pygame.event.post(new_event)

    def get_sprite(self, stage, tag):
        """Returns the 1st sprite with a corresponding tag.
        None is returned if it was not found in the stage."""
        if tag is None or stage is None: return None

        the_list = self.stages[stage]
        for sprite in the_list:
            if sprite.tag == tag:
                return sprite
        return None
    
    def get_sprite_by_name(self, stage, name):
        """Returns the 1st sprite with a corresponding name.
        None is returned if it was not found in the stage."""
        if name is None or stage is None: return None

        the_list = self.stages[stage]
        sprite : UiSprite
        for sprite in the_list:
            if sprite.name == name:
                return sprite
        return None

    def get_sprite_index(self, stage, name = None, tag = None):
        '''Returns the index of the 1st occurence of sprite with a corresponding name or tag.
        None is returned if the sprite is not found'''
        if name is None and tag is None: return None
        the_list = self.stages[stage]
        sprite : UiSprite
        for i, sprite in enumerate(the_list):
            if sprite.name == name and name is not None:
                return i
            if sprite.tag == tag and tag is not None:
                return i
        return None
    
    def find_and_replace(self, new_sprite : UiSprite, stage : int, name : str|None = None, tag : int|None = None, sprite : UiSprite|None = None) -> bool:
        found : bool = False
        for index, sprite in enumerate(self.stages[stage]):
            if sprite == new_sprite and sprite is not None:
                found = True
                break
            if sprite.tag == tag and tag is not None:
                found = True
                break
            if sprite.name == name and name is not None:
                found = True
                break
        
        if found:
            self.stages[stage][index] = new_sprite
        else:
            print('Find and replace failed')
        return found
    
    def handle_tag_event(self, event : pygame.Event):
        if event.type != UiSprite.TAG_EVENT:
            return
        tag : int = event.tag
        name : str = event.name
        trigger_type : str = event.trigger_type
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                pass
                   
    
    def handle_mouse_event(self, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos : tuple = event.pos
            sprite : UiSprite
            for sprite in self.stages[self.stage]:
                if type(sprite) != UiSprite: continue
                if sprite.rect.collidepoint(mouse_pos):
                    sprite.on_click()

class Menu(BaseMenu):
    token_image : pygame.Surface = pygame.image.load('assets/graphics/ui/resized_token_green_colorkey.png')
    token_image.set_colorkey([0, 255, 0])
    token_image = scale_surf(token_image, 0.075)

    fail_theme : pygame.mixer.Sound = pygame.mixer.Sound('assets/audio/stress_theme.ogg')
    fail_theme.set_volume(0.35)

    victory_theme : pygame.mixer.Sound = fail_theme #pygame.mixer.Sound('assets/audio/stress_theme.ogg')
    victory_theme.set_volume(0.35)

    main_theme : pygame.mixer.Sound = fail_theme # pygame.mixer.Sound('assets/audio/stress_theme.ogg')
    main_theme.set_volume(0.35)
    USE_RESULT_THEME = True
    def init(self):
        self.ENTRY_TABLE : dict[int, Callable[[], None]] = {
            1 : self.enter_stage1,
            2 : self.enter_stage2,
            3 : self.enter_stage3,
            4 : self.enter_stage4,
            5 : self.enter_stage5,
            6 : self.enter_stage6,
            7 : self.enter_stage7,
            8 : self.enter_stage8,
            9 : self.enter_stage9,
            10 : self.enter_stage10,
            11 : self.enter_stage11,
            12 : self.enter_stage12,
            13 : self.enter_stage13,
            14 : self.enter_stage14
        }
        self.EXIT_TABLE : dict[int, Callable[[], None]] = {
            2 : self.exit_stage2,
            7 : self.exit_stage7,
            8 : self.exit_stage8,
            11 : self.exit_stage11,
            12 : self.exit_stage12,
            13 : self.exit_stage13,
            14 : self.exit_stage14
        }

        self.bg_color = (94, 129, 162)
        self.stage = 1
        self.stage_data : list[dict] = [{} for _ in range(20 + 1)]
        self.stage_data[0] = None
        window_size = core_object.main_display.get_size()
        window_x, window_y = window_size
        centerx = window_size[0] // 2
        upgrade_bar_surf1 = make_upgrade_bar()
        self.stages = [None, 
        [BaseUiElements.new_text_sprite('StormZ Day', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_button('BlueButton', 'Play', 1, 'midbottom', (centerx, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'play_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Settings', 1, 'bottomleft', (15, window_size[1] - 15), (0.4, 1.0), 
        {'name' : 'settings_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_text_sprite('Highscore : 0', (Menu.font_50, 'Black', False), 0, 'topleft', (15, 200), name='highscore_text'),
        BaseUiElements.new_text_sprite('Highest wave : 0', (Menu.font_50, 'Black', False), 0, 'topleft', (15, 260), name='highwave_text'),
        BaseUiElements.new_text_sprite('WASD to move', (Menu.font_50, 'Black', False), 0, 'topright', (945, 140)),
        BaseUiElements.new_text_sprite('Hold space to shoot', (Menu.font_50, 'Black', False), 0, 'topright', (945, 200)),
        BaseUiElements.new_text_sprite('Mouse to aim', (Menu.font_50, 'Black', False), 0, 'topright', (945, 260)),
        BaseUiElements.new_text_sprite('P to pause', (Menu.font_50, 'Black', False), 0, 'topright', (945, 320))], 

        #--> stage 2
        [BaseUiElements.new_text_sprite('Loadout', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        BaseUiElements.new_text_sprite('Weapon Equipped : Pistol', (Menu.font_50, 'Black', False), 0, 'midleft', (15, 100), name='weapon_equipped'),
        BaseUiElements.new_button('BlueButton', 'Modify', 1, 'midleft', (15, 145), (0.4, 1.0), 
        {'name' : 'modify_weapon'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_text_sprite('Armor Equipped : None', (Menu.font_50, 'Black', False), 0, 'midleft', (15, 295), name='armor_equipped'),
        BaseUiElements.new_button('BlueButton', 'Modify', 1, 'midleft', (15, 340), (0.4, 1.0), 
        {'name' : 'modify_armor'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('GreenButton', 'Ready', 1, 'bottomright', (window_x - 20, window_y - 15), (0.4, 1.0), 
        {'name' : 'ready_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Back', 2, 'bottomleft', (15, window_y - 15), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Shop', 3, 'midbottom', (centerx - 90, window_y - 15), (0.4, 1.0), 
        {'name' : 'shop_button', 'visible' : False}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Armory', 4, 'midbottom', (centerx + 90, window_y - 15), (0.4, 1.0), 
        {'name' : 'armory_button', 'visible' : False}, (Menu.font_40, 'Black', False)),
        ],

        #--> stage 3
        [BaseUiElements.new_text_sprite('Weapons', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        #BaseUiElements.new_button('GreenButton', 'Ready', 1, 'bottomright', (940, window_size[1] - 15), (0.4, 1.0), 
        #{'name' : 'ready_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        #BaseUiElements.new_button('BlueButton', 'Prev', 1, 'midbottom', (centerx - 100, window_size[1] - 25), (0.4, 1.0), 
        #{'name' : 'prev_button'}, (Menu.font_40, 'Black', False)),
        #BaseUiElements.new_button('BlueButton', 'Next', 1, 'midbottom', (centerx + 100, window_size[1] - 25), (0.4, 1.0), 
        #{'name' : 'next_button'}, (Menu.font_40, 'Black', False)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        *self.make_weapon_ui('Pistol', (100, 110), 'A budget starting weapon.'), 
        *self.make_weapon_ui('Rifle', (345, 110), 'Shoots quickly.'), 
        *self.make_weapon_ui('Shotgun', (590, 110), 'Shoots multiple pellets at once, dealing big damage.'), 
        *self.make_weapon_ui('Piercer', (835, 110), 'Bullets go trough enemies. Useful when enemies start to stack.')
        ],
        #--> stage 4
        [BaseUiElements.new_text_sprite('Results', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_button('BlueButton', 'Next', 1, 'midbottom', (centerx, window_size[1] - 15), (0.35, 1), 
        {'name' : 'next_button'}, (Menu.font_40, 'Black', False)),
        TextSprite(pygame.Vector2(centerx, 90), 'midtop', 0, 'Wave:', 'wave_title', None, None, 0, (Menu.font_50, 'Black', False), colorkey=[0,255,0]),
        TextSprite(pygame.Vector2(centerx, 120), 'midtop', 0, '0', 'wave_count', None, None, 0, (Menu.font_50, 'Black', False), colorkey=[0,255,0]),
        TextSprite(pygame.Vector2(560, 120), 'midleft', 0, 'New High!', 'wave_high', {'visible' : False}, None, 0, (Menu.font_50, 'Black', False), colorkey=[0,255,0]),
        TextSprite(pygame.Vector2(centerx, 210), 'midtop', 0, 'Score:', 'wave_title', None, None, 0, (Menu.font_50, 'Black', False), colorkey=[0,255,0]),
        TextSprite(pygame.Vector2(centerx, 240), 'midtop', 0, '0', 'score_count', None, None, 0, (Menu.font_50, 'Black', False), colorkey=[0,255,0]),
        TextSprite(pygame.Vector2(560, 240), 'midleft', 0, 'New High!', 'score_high', {'visible' : False}, None, 0, (Menu.font_50, 'Black', False), colorkey=[0,255,0]),
        TextSprite(pygame.Vector2(centerx, 310), 'midtop', 0, 'Tokens Gained:', 'token_title', None, None, 0, (Menu.font_50, 'Black', False), colorkey=[0,255,0]),
        TextSprite(pygame.Vector2(centerx, 340), 'midtop', 0, '0', 'token_count', None, None, 0, (Menu.font_50, 'Black', False), colorkey=[0,255,0]),
        TextSprite(pygame.Vector2(centerx, 390), 'midtop', 0, 'Current Token Count : 0', 'current_token_count', None, None, 0, (Menu.font_50, 'Black', False), colorkey=[0,255,0]),
        ],
        #--> stage 5
        [BaseUiElements.new_text_sprite('Armors', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        #BaseUiElements.new_button('GreenButton', 'Ready', 1, 'bottomright', (940, window_size[1] - 15), (0.4, 1.0), 
        #{'name' : 'ready_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        #BaseUiElements.new_button('BlueButton', 'Prev', 1, 'midbottom', (centerx - 100, window_size[1] - 25), (0.4, 1.0), 
        #{'name' : 'prev_button'}, (Menu.font_40, 'Black', False)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        *self.make_armor_ui('Light', (100, 110), 'Offers decent protection and keeps you moving fast.'), 
        *self.make_armor_ui('Balanced', (345, 110), 'The best of both worlds.'), 
        *self.make_armor_ui('Heavy', (590, 110), 'Makes you much more tanky, at the cost of your speed.'), 
        *self.make_armor_ui('Adaptative', (835, 110), 
'''Completely negates all damage while active, but falls apart
very quickly if you get overwhelmed.
Useful for skilled players.''')],
        #--> stage 6
        [
        BaseUiElements.new_text_sprite('Settings', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_text_sprite('Current control scheme : Simple', (Menu.font_50, 'Black', False), 0, 'topleft', (15, 90), name='scheme_title'),
        BaseUiElements.new_button('BlueButton', 'Choose', 1, 'topleft', (15, 140), (0.4, 1.0), 
        {'name' : 'choose_scheme_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_text_sprite('Reset data', (Menu.font_50, 'Black', False), 0, 'topright', (window_size[0] - 15, 90), name='scheme_title'),
        BaseUiElements.new_button('RedButton', 'Reset', 1, 'topright', (window_size[0] - 15, 140), (0.4, 1.0), 
        {'name' : 'choose_reset_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'bottomleft', (15, window_size[1] - 15), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        ],
        #--> stage 7
        [
        BaseUiElements.new_text_sprite('Choose control scheme', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        *self.make_control_scheme_ui('Mobile', (100, 200), 'Use this if you are playing on mobile or on a touchscreen.'),
        *self.make_control_scheme_ui('Simple', (345, 200), 'Shots will automatically go to the nearest enemy.\nUse the mouse or the arrow keys to aim manually.'),
        *self.make_control_scheme_ui('Mixed', (590, 200), 'Aim with the arrow keys when using SPACE to shoot.\nAim using the mouse when clicking to shoot.'), 
        *self.make_control_scheme_ui('Expert', (835, 200), 'Aim with the mouse.\nRecommended for more experienced players.')
        ],
        #--> stage 8
        [
        BaseUiElements.new_text_sprite('Are you sure? This action is irreversible.', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'midleft', (200, 200), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('RedButton', 'RESET', 1, 'midright', (740, 200), (0.4, 1.0), 
        {'name' : 'reset_button'}, (Menu.font_40, 'Black', False)),
        ],
        #--> stage 9
        [
        BaseUiElements.new_text_sprite('Shop', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_text_sprite('Weapons', (Menu.font_50, 'Black', False), 0, 'midtop', (225, 140)),
        BaseUiElements.new_button('BlueButton', 'Browse', 1, 'midtop', (225, 200), (0.4, 1.0), name='weapon_browse'),
        BaseUiElements.new_text_sprite('Armor', (Menu.font_50, 'Black', False), 0, 'midtop', (window_x - 225, 140)),
        BaseUiElements.new_button('BlueButton', 'Browse', 2, 'midtop', (window_x - 225, 200), (0.4, 1.0), name='armor_browse'),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        ],
        #--> stage 10
        [
        BaseUiElements.new_text_sprite('Armory', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_text_sprite('Weapons', (Menu.font_50, 'Black', False), 0, 'midtop', (225, 140)),
        BaseUiElements.new_button('BlueButton', 'Browse', 1, 'midtop', (225, 200), (0.4, 1.0), name='weapon_browse'),
        BaseUiElements.new_text_sprite('Armor', (Menu.font_50, 'Black', False), 0, 'midtop', (window_x - 225, 140)),
        BaseUiElements.new_button('BlueButton', 'Browse', 2, 'midtop', (window_x - 225, 200), (0.4, 1.0), name='armor_browse'),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        ],
        #--> stage 11
        [
        BaseUiElements.new_text_sprite('Armory-Weapons', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        BaseUiElements.new_button('BlueButton', 'Prev', 1, 'bottomleft', (20, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'prev_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Next', 1, 'bottomright', (window_x - 20, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'next_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Buy', 1, 'midbottom', (centerx, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'weapon_interact'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Upgrade', 1, 'midbottom', (centerx + 90, window_y - 15), (0.4, 1.0), 
        {'name' : 'upgrade_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_text_sprite("Cost : 0", (Menu.font_40, 'Black', False), 0, 'midbottom', (centerx + 90, window_y - 15), name='cost_sprite')
        
        ],
        #--> stage 12
        [
        BaseUiElements.new_text_sprite('Upgrade Weapon', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        ],
        #--> stage 13
        [
        BaseUiElements.new_text_sprite('Armory-Armor', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        BaseUiElements.new_button('BlueButton', 'Prev', 1, 'bottomleft', (20, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'prev_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Next', 1, 'bottomright', (window_x - 20, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'next_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Buy', 1, 'midbottom', (centerx, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'armor_interact'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Upgrade', 1, 'midbottom', (centerx + 90, window_y - 15), (0.4, 1.0), 
        {'name' : 'upgrade_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_text_sprite("Cost : 0", (Menu.font_40, 'Black', False), 0, 'midbottom', (centerx + 90, window_y - 15), name='cost_sprite')
        ],
        #--> stage 14
        [
        BaseUiElements.new_text_sprite('Upgrade Armor', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        ],
        ]
    
    def enter_stage1(self):
        self.stage = 1
        self.update_highscores_stage1()

    def update_highscores_stage1(self):
        new_highscore_text : str = f'Highscore : {core_object.storage.high_score}'
        new_highwave_text : str = f'Highest wave : {core_object.storage.high_wave}'
        new_score_sprite : UiSprite = BaseUiElements.new_text_sprite(new_highscore_text, (Menu.font_50, 'Black', False), 0, 'topleft', (15, 200),name='highscore_text')
        new_wave_sprite : UiSprite = BaseUiElements.new_text_sprite(new_highwave_text, (Menu.font_50, 'Black', False), 0, 'topleft', (15, 260), name='highwave_text')
        self.find_and_replace(new_score_sprite, 1, name='highscore_text')
        self.find_and_replace(new_wave_sprite, 1, name='highwave_text')

    def enter_stage2(self):
        self.stage = 2
        new_sprite1 : UiSprite = BaseUiElements.new_text_sprite(f'Weapon Equipped : {core_object.storage.weapon_equipped}', (Menu.font_50, 'Black', False), 0, 
                                                                'midleft', (15, 100), name='weapon_equipped')
        self.find_and_replace(new_sprite1, 2, name='weapon_equipped')
        armor_equipped : str = 'None' if core_object.storage.armor_equipped is None else core_object.storage.armor_equipped
        new_sprite2 : UiSprite = BaseUiElements.new_text_sprite(f'Armor Equipped : {armor_equipped}', (Menu.font_50, 'Black', False), 0, 
                                                                'midleft', (15, 295), name='armor_equipped')
        self.find_and_replace(new_sprite2, 2, name='armor_equipped')
        self.update_token_count(self.stage)

    def update_token_count(self, current_stage : int = 2):
        token_count : TextSprite = self.get_sprite_by_name(current_stage, 'token_count')
        token_count.text = f'{core_object.storage.upgrade_tokens}'
        token_count.rect = token_count.surf.get_rect(midright = (906, 40))

    def make_weapon_ui(self, weapon_name : str, midtop : tuple[int, int]|pygame.Vector2, tooltip : str) -> tuple[UiSprite]:
        weapon_title_text = f'{weapon_name}\nCost : {core_object.storage.COST_TABLE['Weapons'][weapon_name]}'
        weapon_title = BaseUiElements.new_text_sprite(weapon_title_text, (Menu.font_50, 'Black', False), 0, 'midtop', midtop, name = f'weapon_title_{weapon_name}')
        weapon_interact = BaseUiElements.new_button('BlueButton', 'Buy', 1, 'midtop', (midtop[0], midtop[1] + 80), (0.4, 1), 
                                                    name=f'weapon_interact_{weapon_name}')
        tooltip = ToolTip(pygame.Vector2(15, 440), 'bottomleft', 0, tooltip, weapon_title.rect.union(weapon_interact.rect), f'tooltip_{weapon_name}',
                          text_settings=(Menu.font_50, 'Black', False), colorkey=[0, 255, 0])
        return weapon_title, weapon_interact, tooltip
    
    def update_weapon_ui_stage3(self, weapon_name : str):
        weapon_title = self.get_sprite_by_name(self.stage, f'weapon_title_{weapon_name}')
        if not weapon_title: return
        midtop : tuple[int, int] = weapon_title.rect.midtop
        interact_text : str
        if weapon_name not in core_object.storage.owned_weapons:
            interact_text = 'Buy'
        elif weapon_name != core_object.storage.weapon_equipped:
            interact_text = 'Equip'
        else:
            interact_text = 'Equipped'
        new_weapon_interact = BaseUiElements.new_button('BlueButton', interact_text, 1, 'midtop', (midtop[0], midtop[1] + 60), 
                                                        (0.4, 1),name=f'weapon_interact_{weapon_name}')
        self.find_and_replace(new_weapon_interact, self.stage, name=f'weapon_interact_{weapon_name}')

    def make_armor_ui(self, armor_name : str, midtop : tuple[int, int]|pygame.Vector2, tooltip : str) -> tuple[UiSprite]:
        armor_title_text = f'{armor_name}\nCost : {core_object.storage.COST_TABLE['Armors'][armor_name]}'
        armor_title = BaseUiElements.new_text_sprite(armor_title_text, (Menu.font_50, 'Black', False), 0, 'midtop', midtop, name = f'armor_title_{armor_name}')
        armor_interact = BaseUiElements.new_button('BlueButton', 'Buy', 1, 'midtop', (midtop[0], midtop[1] + 80), (0.4, 1), 
                                                    name=f'armor_interact_{armor_name}')
        tooltip = ToolTip(pygame.Vector2(15, 440), 'bottomleft', 0, tooltip, armor_title.rect.union(armor_interact.rect), f'tooltip_{armor_name}',
                          text_settings=(Menu.font_50, 'Black', False), colorkey=[0, 255, 0])
        return armor_title, armor_interact, tooltip
    
    def update_armor_ui_stage5(self, armor_name : str):
        armor_title = self.get_sprite_by_name(self.stage, f'armor_title_{armor_name}')
        if not armor_title: return
        midtop : tuple[int, int] = armor_title.rect.midtop
        interact_text : str
        if armor_name not in core_object.storage.owned_armors:
            interact_text = 'Buy'
        elif armor_name != core_object.storage.armor_equipped:
            interact_text = 'Equip'
        else:
            interact_text = 'Unequip'
        new_armor_interact = BaseUiElements.new_button('BlueButton', interact_text, 1, 'midtop', (midtop[0], midtop[1] + 60), 
                                                        (0.4, 1),name=f'armor_interact_{armor_name}')
        self.find_and_replace(new_armor_interact, self.stage, name=f'armor_interact_{armor_name}')
    
    def make_control_scheme_ui(self, name : str, midtop : pygame.Vector2|tuple[int, int], tooltip : str ) -> tuple[UiSprite, UiSprite]:
        button = BaseUiElements.new_button('BlueButton', name, 1, 'midtop', midtop, (0.4, 1.0), 
        {'name' : f'button_{name}'}, (Menu.font_40, 'Black', False))
        tooltip = ToolTip(pygame.Vector2(15, 440), 'bottomleft', 0, tooltip, button.rect, f'tooltip_{name}',
                          text_settings=(Menu.font_50, 'Black', False), colorkey=[0, 255, 0])
        return button, tooltip
    
    def exit_stage2(self):
        pass

    def enter_stage3(self):
        self.stage_data[3]['prev_stage'] = self.stage
        self.stage = 3
        for weapon in core_object.storage.ALL_WEAPONS:
            self.update_weapon_ui_stage3(weapon)
        self.update_token_count(self.stage)

    def exit_stage3(self):
        prev_stage : int = self.stage_data[3]['prev_stage']
        self.stage_data[3].clear()
        self.enter_any_stage(prev_stage)


    def enter_stage5(self):
        self.stage_data[5]['prev_stage'] = self.stage
        self.stage = 5
        for armor in core_object.storage.ALL_ARMORS:
            self.update_armor_ui_stage5(armor)
        self.update_token_count(self.stage)
    
    def exit_stage5(self):
        prev_stage : int = self.stage_data[5]['prev_stage']
        self.stage_data[5].clear()
        self.enter_any_stage(prev_stage)


    def enter_stage4(self, score : int, wave_count : int, tokens_gained : int, game_won : bool = False):
        prev_highscore : int = core_object.storage.high_score
        prev_wave_record : int = core_object.storage.high_wave
        self.get_sprite_by_name(4, 'wave_count').text = f'{wave_count}'
        score_count : TextSprite = self.get_sprite_by_name(4, 'score_count')
        score_count.text = f'{score}'
        score_count.rect = score_count.surf.get_rect(midtop = (480, 240))
        self.get_sprite_by_name(4, 'token_count').text = f'{tokens_gained}'
        self.get_sprite_by_name(4, 'wave_high').visible = (wave_count > prev_wave_record)
        self.get_sprite_by_name(4, 'score_high').visible = (score > prev_highscore)
        current_token_count : TextSprite = self.get_sprite_by_name(4, 'current_token_count')
        current_token_count.text = f'Current Token Count : {core_object.storage.upgrade_tokens}'
        current_token_count.rect.centerx = 480
        if game_won:
            time = 2
            overlay : BrightnessOverlay = BrightnessOverlay(0, pygame.Rect(0,0, *core_object.main_display.get_size()), 0, 'fade_in_overlay', zindex=100)
            overlay.brightness = -255
            TInfo = TweenModule.TweenInfo
            goal1 = {'brightness' : 0}
            info1 = TInfo(interpolation.linear, time)
            TweenModule.new_tween(overlay, info1, goal1)
            self.add_temp(overlay, time + 0.01)
    
    def enter_stage6(self):
        self.stage = 6
        text_sprite = BaseUiElements.new_text_sprite(f'Current control scheme : {core_object.settings.info['ControlMethod']}', 
                                                     (Menu.font_50, 'Black', False), 0, 'topleft', (15, 90), name='scheme_title')
        self.find_and_replace(text_sprite, 6, name='scheme_title')
    
    def enter_stage7(self):
        self.stage_data[7]['prev_stage'] = self.stage
        self.stage = 7
    
    def exit_stage7(self):
        old_stage : int = self.stage_data[7].get('prev_stage', None)
        if not old_stage: old_stage = 1
        if old_stage == 7: old_stage = 1
        self.stage_data[7].clear()
        self.enter_any_stage(old_stage)
    
    def enter_stage8(self):
        self.stage_data[8]['prev_stage'] = self.stage
        self.stage = 8

    def exit_stage8(self):
        old_stage : int = self.stage_data[8].get('prev_stage', None)
        if not old_stage: old_stage = 1
        if old_stage == 8: old_stage = 1
        self.stage_data[8].clear()
        self.enter_any_stage(old_stage)

    def enter_stage9(self):
        self.stage = 9
        self.update_token_count(self.stage)

    def enter_stage10(self):
        self.stage = 10
        self.update_token_count(self.stage)
    
    def enter_stage11(self, goto_weapon_equipped : bool = False):
        prev_stage : int = self.stage if self.stage != 12 else 2
        self.stage = 11
        weapon_equipped_index : int = core_object.storage.ALL_WEAPONS.index(core_object.storage.weapon_equipped)
        current_weapon_index : int = weapon_equipped_index if goto_weapon_equipped else self.stage_data[11].get('weapon_index', weapon_equipped_index)
        self.stage_data[11] = {'weapon_index' : current_weapon_index, 
                               'all_weapons_lentgh' : len(core_object.storage.ALL_WEAPONS), 
                               'current_weapon' : core_object.storage.ALL_WEAPONS[current_weapon_index],
                               'prev_stage' : prev_stage}
        
        self.replace_stage11_weapon_ui(None, self.stage_data[11]['current_weapon'])
        self.update_token_count(self.stage)
        self.udpdate_stage11_weapon_interact(self.stage_data[11]['current_weapon'])
    
    def make_stage11_weapon_ui(self, weapon_name : str):
        window_size = core_object.main_display.get_size()
        window_x, window_y = window_size
        centerx = window_size[0] // 2
        weapon_title : UiSprite = BaseUiElements.new_text_sprite(weapon_name, (Menu.font_50, 'Black', False), 0, 'midtop', (centerx, 100), name='weapon_title')
        all_base_stats = core_object.storage.BASE_WEAPON_STATS[weapon_name]
        base_stats_paragraph = '\n'.join(['Base Stats:'] + [f'{key} : {all_base_stats[key]}' for key in all_base_stats]) if all_base_stats else ''
        base_stats : UiSprite = BaseUiElements.new_text_sprite(base_stats_paragraph, (Menu.font_50, 'Black', False), 0, 'topleft', (15, 175), name='base_weapon_stats')
        all_weapon_perks = core_object.storage.current_weapon_perks[weapon_name]
        weapon_perks_paragraph = '\n'.join(['Perks:'] + [core_object.storage.format_perk(key, all_weapon_perks[key]) for key in all_weapon_perks]) if all_weapon_perks else ''
        weapon_perks : UiSprite = BaseUiElements.new_text_sprite(weapon_perks_paragraph, (Menu.font_50, 'Black', False), 0, 'topright', (945, 175), name='the_weapon_perks')
        tooltip : UiSprite = BaseUiElements.new_text_sprite(core_object.storage.WEAPON_TOOLTIP_TABLE.get(weapon_name, '???'), (Menu.font_50, 'Black', False), 0,
                                                            'bottomleft', (15, window_y - 100), name='tooltip')
        return (weapon_title, base_stats, weapon_perks, tooltip)
    
    def remove_stage11_weapon_ui(self, weapon_name : str):
        if not self.get_sprite_by_name(11, 'weapon_title'): return
        self.stages[11].remove(self.get_sprite_by_name(11, 'weapon_title'))
        self.stages[11].remove(self.get_sprite_by_name(11, 'base_weapon_stats'))
        self.stages[11].remove(self.get_sprite_by_name(11, 'the_weapon_perks'))
        self.stages[11].remove(self.get_sprite_by_name(11, 'tooltip'))

    def add_stage11_weapon_ui(self, weapon_name : str):
        for ui_sprite in self.make_stage11_weapon_ui(weapon_name):
            self.stages[11].append(ui_sprite)
    
    
    
    def replace_stage11_weapon_ui(self, old_weapon_name : str, weapon_name : str):
        self.remove_stage11_weapon_ui(old_weapon_name)
        self.add_stage11_weapon_ui(weapon_name)
    
    def update_stage11_weapon_ui(self, weapon_name : str):
        self.remove_stage11_weapon_ui(weapon_name)
        self.add_stage11_weapon_ui(weapon_name)
    
    def udpdate_stage11_weapon_interact(self, weapon_name : str):
        cost : int = core_object.storage.COST_TABLE['Weapons'][weapon_name]
        window_size = core_object.main_display.get_size()
        window_x, window_y = window_size
        centerx = window_size[0] // 2
        new_text : str
        current_weapon : str = self.stage_data[11]['current_weapon']
        cost_visible : bool = False
        if current_weapon == core_object.storage.weapon_equipped:
            new_text = 'Equipped'
            self.get_sprite_by_name(11, 'upgrade_button').visible = True
        elif current_weapon in core_object.storage.owned_weapons:
            new_text = 'Equip'
            self.get_sprite_by_name(11, 'upgrade_button').visible = True
        else:
            new_text = 'Buy'
            self.get_sprite_by_name(11, 'upgrade_button').visible = False
            cost_visible = True
        new_sprite : UiSprite = BaseUiElements.new_button('BlueButton', new_text, 1, 'midbottom', (centerx - 90, window_size[1] - 15), (0.4, 1.0), 
        {'name' : 'weapon_interact'}, (Menu.font_40, 'Black', False))
        self.find_and_replace(new_sprite, 11, name='weapon_interact')
        cost_sprite = BaseUiElements.new_text_sprite(f"Cost : {cost}", (Menu.font_50, 'Black', False), 0, 
                                                     'bottomleft', (centerx + 22, window_y - 30), name='cost_sprite')
        cost_sprite.visible = cost_visible
        self.find_and_replace(cost_sprite, 11, name='cost_sprite')
    
    def exit_stage11(self):
        self.remove_stage11_weapon_ui(self.stage_data[11]['current_weapon'])
        prev_stage : int = self.stage_data[11]['prev_stage']
        self.enter_any_stage(prev_stage)
        #self.stage_data[11].clear()
    
    def enter_stage12(self, weapon_name : str):
        self.stage = 12
        self.stage_data[12]['weapon'] = weapon_name
        self.stage_data[12]['upgrade_sprites'] = []
        self.update_token_count(self.stage)
        self.replace_stage12_updgrade_ui(weapon_name)
    
    def make_stage12_updgrade_ui(self, weapon_name : str):
        window_size = core_object.main_display.get_size()
        window_x, window_y = window_size
        centerx = window_size[0] // 2
        weapon_title : UiSprite = BaseUiElements.new_text_sprite(weapon_name, (Menu.font_50, 'Black', False), 0, 'midtop', (centerx, 100), name='weapon_title')

        for ui_sprite in (weapon_title,):
            self.stages[12].append(ui_sprite)
        self.make_stage12_upgrade_section(weapon_name)
    
    def make_stage12_upgrade_section(self, weapon_name : str):
        curr_x : int = 15
        curr_y : int = 142
        for perk in core_object.storage.WEAPON_AVAILABLE_PERKS[weapon_name]:
            max_level : int = core_object.storage.WEAPON_AVAILABLE_PERKS[weapon_name][perk]
            current_level : int|None = core_object.storage.current_weapon_perks[weapon_name].get(perk, None)
            header_text : str
            cost_text : str
            button_text : str = 'Upgrade'
            if current_level is None:
                header_text = core_object.storage.format_perk(perk, 1)
                cost_text = f'Cost : {core_object.storage.COST_TABLE['Weapon Perks'][weapon_name][perk][1]}'
            elif current_level < max_level:
                header_text = core_object.storage.format_perk_improvement(perk, current_level, current_level + 1)
                #header_text = core_object.storage.format_perk(perk, current_level + 1)
                cost_text = f'Cost : {core_object.storage.COST_TABLE['Weapon Perks'][weapon_name][perk][current_level + 1]}'
            else:
                header_text = core_object.storage.format_perk(perk, current_level)
                cost_text = f'Cost : MAXED'
                button_text = 'MAXED'
            
            header_sprite = BaseUiElements.new_text_sprite(header_text, (Menu.font_50, 'Black', False), 0, 'topleft', (curr_x, curr_y))
            cost_sprite = BaseUiElements.new_text_sprite(cost_text, (Menu.font_50, 'Black', False), 0, 'topleft', (curr_x, curr_y + 30))
            button_sprite = BaseUiElements.new_button('BlueButton', button_text, 1, 'topleft', (curr_x, curr_y + 60), (0.4, 1), name=f'upgrade_perk_{perk}')
            tooltip_sprite = ToolTip(pygame.Vector2(15, 440), 'topleft', 0, core_object.storage.PERK_TOOLTIP_TABLE[perk], 
                                     header_sprite.rect.unionall([cost_sprite.rect, button_sprite.rect]), text_settings=(Menu.font_50, 'Black', False), colorkey=[0, 255, 0])
            for ui_sprite in (header_sprite, cost_sprite, button_sprite, tooltip_sprite):
                self.stages[12].append(ui_sprite)
                self.stage_data[12]['upgrade_sprites'].append(ui_sprite)
            
            curr_y += 165
            if curr_y > 400:
                curr_y = 142
                curr_x += 370
    
    def upgrade_stage12_weapon_perk(self, perk_name : str):
        current_weapon : str = self.stage_data[12]['weapon']
        current_level : int|None = core_object.storage.current_weapon_perks[current_weapon].get(perk_name, None)
        max_level : int = core_object.storage.WEAPON_AVAILABLE_PERKS[current_weapon][perk_name]
        if current_level:
            if current_level >= max_level:
                self.alert_player('This upgrade is already maxed out!')
                return
        
        next_level : int = current_level + 1 if current_level is not None else 1
        cost : int = core_object.storage.COST_TABLE['Weapon Perks'][current_weapon][perk_name][next_level]
        if cost > core_object.storage.upgrade_tokens:
            self.alert_player('Not enough tokens!')
        else:
            core_object.storage.upgrade_tokens -= cost
            core_object.storage.current_weapon_perks[current_weapon][perk_name] = next_level
            self.replace_stage12_updgrade_ui(current_weapon)
        self.update_token_count(self.stage)
            
    
    def remove_stage12_upgrade_ui(self):
        if not self.get_sprite_by_name(12, 'weapon_title'): return
        self.stages[12].remove(self.get_sprite_by_name(12, 'weapon_title'))
        upg_sprite : UiSprite
        for upg_sprite in self.stage_data[12]['upgrade_sprites']:
            if upg_sprite in self.stages[12]: self.stages[12].remove(upg_sprite)
        self.stage_data[12]['upgrade_sprites'].clear()
    
    def replace_stage12_updgrade_ui(self, new_weapon_name : str):
        self.remove_stage12_upgrade_ui()
        self.make_stage12_updgrade_ui(new_weapon_name)
    
    def exit_stage12(self):
        self.remove_stage12_upgrade_ui()
        self.stage_data[12].clear()
    
    def enter_stage13(self, goto_armor_equipped : bool = False):
        prev_stage : int = self.stage if self.stage != 14 else 2
        self.stage = 13
        armor_equipped_index : int = core_object.storage.ALL_ARMORS.index(core_object.storage.armor_equipped) if core_object.storage.armor_equipped else 0
        current_armor_index : int = armor_equipped_index if goto_armor_equipped else self.stage_data[13].get('armor_index', armor_equipped_index)
        self.stage_data[13] = {'armor_index' : current_armor_index, 
                               'all_armors_lentgh' : len(core_object.storage.ALL_ARMORS), 
                               'current_armor' : core_object.storage.ALL_ARMORS[current_armor_index],
                               'prev_stage' : prev_stage}
        
        self.replace_stage13_armor_ui(None, self.stage_data[13]['current_armor'])
        self.update_token_count(self.stage)
        self.udpdate_stage13_armor_interact()
    
    def make_stage13_armor_ui(self, armor_name : str):
        window_size = core_object.main_display.get_size()
        window_x, window_y = window_size
        centerx = window_size[0] // 2
        armor_title : UiSprite = BaseUiElements.new_text_sprite(armor_name, (Menu.font_50, 'Black', False), 0, 'midtop', (centerx, 100), name='armor_title')
        all_base_stats = core_object.storage.BASE_ARMOR_STATS[armor_name]
        base_stats_paragraph = '\n'.join(['Base Stats:'] + [f'{key} : {all_base_stats[key]}' for key in all_base_stats]) if all_base_stats else ''
        base_stats : UiSprite = BaseUiElements.new_text_sprite(base_stats_paragraph, (Menu.font_50, 'Black', False), 0, 'topleft', (15, 175), name='base_armor_stats')
        all_armor_perks = core_object.storage.current_armor_perks[armor_name]
        armor_perks_paragraph = '\n'.join(['Perks:'] + [core_object.storage.format_perk(key, all_armor_perks[key]) for key in all_armor_perks]) if all_armor_perks else ''
        armor_perks : UiSprite = BaseUiElements.new_text_sprite(armor_perks_paragraph, (Menu.font_50, 'Black', False), 0, 'topright', (945, 175), name='the_armor_perks')
        tooltip : UiSprite = BaseUiElements.new_text_sprite(core_object.storage.ARMOR_TOOLTIP_TABLE.get(armor_name, '???'), (Menu.font_50, 'Black', False), 0,
                                                            'bottomleft', (15, window_y - 100), name='tooltip')
        return (armor_title, base_stats, armor_perks, tooltip)
    
    def remove_stage13_armor_ui(self, armor_name : str):
        if not self.get_sprite_by_name(13, 'armor_title'): return
        self.stages[13].remove(self.get_sprite_by_name(13, 'armor_title'))
        self.stages[13].remove(self.get_sprite_by_name(13, 'base_armor_stats'))
        self.stages[13].remove(self.get_sprite_by_name(13, 'the_armor_perks'))
        self.stages[13].remove(self.get_sprite_by_name(13, 'tooltip'))

    def add_stage13_armor_ui(self, armor_name : str):
        for ui_sprite in self.make_stage13_armor_ui(armor_name):
            self.stages[13].append(ui_sprite)
    
    
    
    def replace_stage13_armor_ui(self, old_armor_name : str, armor_name : str):
        self.remove_stage13_armor_ui(old_armor_name)
        self.add_stage13_armor_ui(armor_name)
    
    def update_stage13_armor_ui(self, armor_name : str):
        self.remove_stage13_armor_ui(armor_name)
        self.add_stage13_armor_ui(armor_name)
    
    def udpdate_stage13_armor_interact(self, curr_armor : str = None):
        window_size = core_object.main_display.get_size()
        window_x, window_y = window_size
        centerx = window_size[0] // 2
        new_text : str
        current_armor : str = self.stage_data[13]['current_armor']
        cost_visible : bool = False
        cost : int = core_object.storage.COST_TABLE['Armors'][current_armor]
        if current_armor == core_object.storage.armor_equipped:
            new_text = 'Unequip'
            self.get_sprite_by_name(13, 'upgrade_button').visible = True
        elif current_armor in core_object.storage.owned_armors:
            new_text = 'Equip'
            self.get_sprite_by_name(13, 'upgrade_button').visible = True
        else:
            new_text = 'Buy'
            self.get_sprite_by_name(13, 'upgrade_button').visible = False
            cost_visible = True
        new_sprite : UiSprite = BaseUiElements.new_button('BlueButton', new_text, 1, 'midbottom', (centerx - 90, window_size[1] - 15), (0.4, 1.0), 
        {'name' : 'armor_interact'}, (Menu.font_40, 'Black', False))
        self.find_and_replace(new_sprite, 13, name='armor_interact')
        cost_sprite = BaseUiElements.new_text_sprite(f"Cost : {cost}", (Menu.font_50, 'Black', False), 0, 
                                                     'bottomleft', (centerx + 22, window_y - 30), name='cost_sprite')
        cost_sprite.visible = cost_visible
        self.find_and_replace(cost_sprite, 13, name='cost_sprite')
    
    def exit_stage13(self):
        self.remove_stage13_armor_ui(self.stage_data[13]['current_armor'])
        prev_stage : int = self.stage_data[13]['prev_stage']
        self.enter_any_stage(prev_stage)
        #self.stage_data[13].clear()
    
    def enter_stage14(self, armor_name : str):
        self.stage = 14
        self.stage_data[14]['armor'] = armor_name
        self.stage_data[14]['upgrade_sprites'] = []
        self.update_token_count(self.stage)
        self.replace_stage14_updgrade_ui(armor_name)
    
    def make_stage14_updgrade_ui(self, armor_name : str):
        window_size = core_object.main_display.get_size()
        window_x, window_y = window_size
        centerx = window_size[0] // 2
        armor_title : UiSprite = BaseUiElements.new_text_sprite(armor_name, (Menu.font_50, 'Black', False), 0, 'midtop', (centerx, 100), name='armor_title')

        for ui_sprite in (armor_title,):
            self.stages[14].append(ui_sprite)
        self.make_stage14_upgrade_section(armor_name)
    
    def make_stage14_upgrade_section(self, armor_name : str):
        curr_x : int = 15
        curr_y : int = 150
        for perk in core_object.storage.ARMOR_AVAILABLE_PERKS[armor_name]:
            max_level : int = core_object.storage.ARMOR_AVAILABLE_PERKS[armor_name][perk]
            current_level : int|None = core_object.storage.current_armor_perks[armor_name].get(perk, None)
            header_text : str
            cost_text : str
            button_text : str = 'Upgrade'
            if current_level is None:
                header_text = core_object.storage.format_perk(perk, 1)
                cost_text = f'Cost : {core_object.storage.COST_TABLE['Armor Perks'][armor_name][perk][1]}'
            elif current_level < max_level:
                header_text = core_object.storage.format_perk_improvement(perk, current_level, current_level + 1)
                #header_text = core_object.storage.format_perk(perk, current_level + 1)
                cost_text = f'Cost : {core_object.storage.COST_TABLE['Armor Perks'][armor_name][perk][current_level + 1]}'
            else:
                header_text = core_object.storage.format_perk(perk, current_level)
                cost_text = f'Cost : MAXED'
                button_text = 'MAXED'
            
            header_sprite = BaseUiElements.new_text_sprite(header_text, (Menu.font_50, 'Black', False), 0, 'topleft', (curr_x, curr_y))
            cost_sprite = BaseUiElements.new_text_sprite(cost_text, (Menu.font_50, 'Black', False), 0, 'topleft', (curr_x, curr_y + 30))
            button_sprite = BaseUiElements.new_button('BlueButton', button_text, 1, 'topleft', (curr_x, curr_y + 60), (0.4, 1), name=f'upgrade_perk_{perk}')
            tooltip_sprite = ToolTip(pygame.Vector2(15, 440), 'topleft', 0, core_object.storage.PERK_TOOLTIP_TABLE[perk], 
                                     header_sprite.rect.unionall([cost_sprite.rect, button_sprite.rect]), text_settings=(Menu.font_50, 'Black', False), colorkey=[0, 255, 0])
            for ui_sprite in (header_sprite, cost_sprite, button_sprite, tooltip_sprite):
                self.stages[14].append(ui_sprite)
                self.stage_data[14]['upgrade_sprites'].append(ui_sprite)
            
            curr_y += 165
            if curr_y > 500:
                curr_y = 150
                curr_x += 285
    
    def upgrade_stage14_armor_perk(self, perk_name : str):
        current_armor : str = self.stage_data[14]['armor']
        current_level : int|None = core_object.storage.current_armor_perks[current_armor].get(perk_name, None)
        max_level : int = core_object.storage.ARMOR_AVAILABLE_PERKS[current_armor][perk_name]
        if current_level:
            if current_level >= max_level:
                self.alert_player('This upgrade is already maxed out!')
                return
        
        next_level : int = current_level + 1 if current_level is not None else 1
        cost : int = core_object.storage.COST_TABLE['Armor Perks'][current_armor][perk_name][next_level]
        if cost > core_object.storage.upgrade_tokens:
            self.alert_player('Not enough tokens!')
        else:
            core_object.storage.upgrade_tokens -= cost
            core_object.storage.current_armor_perks[current_armor][perk_name] = next_level
            self.replace_stage14_updgrade_ui(current_armor)
        self.update_token_count(self.stage)
            
    
    def remove_stage14_upgrade_ui(self):
        if not self.get_sprite_by_name(14, 'armor_title'): return
        self.stages[14].remove(self.get_sprite_by_name(14, 'armor_title'))
        upg_sprite : UiSprite
        for upg_sprite in self.stage_data[14]['upgrade_sprites']:
            if upg_sprite in self.stages[14]: self.stages[14].remove(upg_sprite)
        self.stage_data[14]['upgrade_sprites'].clear()
    
    def replace_stage14_updgrade_ui(self, new_armor_name : str):
        self.remove_stage14_upgrade_ui()
        self.make_stage14_updgrade_ui(new_armor_name)
    
    def exit_stage14(self):
        self.remove_stage14_upgrade_ui()
        self.stage_data[14].clear()

    def goto_stage(self, new_stage : int):
        self.exit_any_stage()
        self.enter_any_stage(new_stage)
    
    def exit_any_stage(self):
        if self.stage in self.EXIT_TABLE:
            self.EXIT_TABLE[self.stage]()
    
    def enter_any_stage(self, new_stage : int):
        if new_stage in self.ENTRY_TABLE:
            self.ENTRY_TABLE[new_stage]()
        else:
            self.stage = new_stage

    def update(self, delta : float):
        super().update(delta)
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case _: pass
    
    def handle_tag_event(self, event : pygame.Event):
        if event.type != UiSprite.TAG_EVENT:
            return
        tag : int = event.tag
        name : str = event.name
        the_sprite : UiSprite = event.sprite
        trigger_type : str = event.trigger_type
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                if name == "play_button":
                    self.goto_stage(2)
                elif name == "settings_button":
                    self.enter_stage6()
            
            case 2:
                if name == 'ready_button':
                    self.launch_game()
                elif name == 'back_button':
                    self.goto_stage(1)
                elif name == 'shop_button':
                    if not the_sprite.visible: return
                    self.goto_stage(9)
                elif name == 'armory_button':
                    if not the_sprite.visible: return
                    self.goto_stage(10)
                elif name == 'modify_armor':
                    self.enter_stage13()
                elif name == 'modify_weapon':
                    self.enter_stage11(True)
            
            case 3:
                if name == 'back_button':
                    self.exit_stage3()
                elif name == 'ready_button':
                    self.launch_game()
                elif name == 'prev_button':
                    self.enter_stage2()
                elif name == 'next_button':
                    self.enter_stage5()
                
                elif name[:16] == 'weapon_interact_':
                    weapon_name = name[16:]
                    if weapon_name == core_object.storage.weapon_equipped:
                        self.alert_player('You are already equpping this item!', 1.5)
                    elif weapon_name in core_object.storage.owned_weapons:
                        core_object.storage.weapon_equipped = weapon_name
                    else:
                        cost : int = core_object.storage.COST_TABLE['Weapons'][weapon_name]
                        if core_object.storage.upgrade_tokens >= cost:
                            core_object.storage.upgrade_tokens -= cost
                            self.update_token_count(self.stage)
                            core_object.storage.owned_weapons.append(weapon_name)
                            core_object.storage.weapon_equipped = weapon_name
                        else:
                            self.alert_player('Not enough tokens!')
                    for weapon in core_object.storage.ALL_WEAPONS:
                        self.update_weapon_ui_stage3(weapon)
                    self.update_token_count(self.stage)

            case 4:
                if name == 'next_button':
                    if not self.USE_RESULT_THEME:
                        core_object.bg_manager.stop_all_music()
                        core_object.bg_manager.play(self.main_theme, 1)
                    self.enter_stage1()
            
            case 5:
                if name == 'back_button':
                    self.exit_stage5()
                elif name == 'ready_button':
                    self.launch_game()
                elif name == 'prev_button':
                    self.enter_stage3()
                
                elif name[:15] == 'armor_interact_':
                    armor_name = name[15:]
                    if armor_name == core_object.storage.armor_equipped:
                        core_object.storage.armor_equipped = None
                    elif armor_name in core_object.storage.owned_armors:
                        core_object.storage.armor_equipped = armor_name
                    else:
                        cost : int = core_object.storage.COST_TABLE['Armors'][armor_name]
                        if core_object.storage.upgrade_tokens >= cost:
                            core_object.storage.upgrade_tokens -= cost
                            self.update_token_count(self.stage)
                            core_object.storage.owned_armors.append(armor_name)
                            core_object.storage.armor_equipped = armor_name
                        else:
                            self.alert_player('Not enough tokens!')
                    for armor in core_object.storage.ALL_ARMORS:
                        self.update_armor_ui_stage5(armor)
                    self.update_token_count(self.stage)
            
            case 6:
                if name == 'choose_scheme_button':
                    self.enter_stage7()
                elif name == 'back_button':
                    self.enter_stage1()
                elif name == 'choose_reset_button':
                    self.enter_stage8()
                
            case 7:
                if name[:7] == 'button_':
                    scheme_name = name[7:]
                    core_object.settings.info['ControlMethod'] = scheme_name
                    core_object.save_settings()
                    self.exit_stage7()

            case 8:
                if name == 'back_button':
                    self.exit_stage8()
                elif name == 'reset_button':
                    core_object.storage.reset()
                    self.exit_stage8()
                    self.alert_player('Data Reset!')
            
            case 9:
                if name == 'back_button':
                    self.goto_stage(2)
                
                elif name == 'weapon_browse':
                    self.goto_stage(3)

                elif name == 'armor_browse':
                    self.goto_stage(5)
            
            case 10:
                if name == 'back_button':
                    self.goto_stage(2)
                
                elif name == 'weapon_browse':
                    self.enter_stage11(True)

                elif name == 'armor_browse':
                    self.goto_stage(13)
            
            case 11:
                if name == 'back_button':
                    self.exit_stage11()
                
                elif name == 'prev_button':
                    self.stage_data[11]['weapon_index'] -= 1
                    self.stage_data[11]['weapon_index'] %= self.stage_data[11]['all_weapons_lentgh']
                    new_weapon : str = core_object.storage.ALL_WEAPONS[self.stage_data[11]['weapon_index']]
                    self.replace_stage11_weapon_ui(self.stage_data[11]['current_weapon'], new_weapon)
                    self.stage_data[11]['current_weapon'] = new_weapon
                    self.udpdate_stage11_weapon_interact(new_weapon)

                elif name == 'next_button':
                    self.stage_data[11]['weapon_index'] += 1
                    self.stage_data[11]['weapon_index'] %= self.stage_data[11]['all_weapons_lentgh']
                    new_weapon : str = core_object.storage.ALL_WEAPONS[self.stage_data[11]['weapon_index']]
                    self.replace_stage11_weapon_ui(self.stage_data[11]['current_weapon'], new_weapon)
                    self.stage_data[11]['current_weapon'] = new_weapon
                    self.udpdate_stage11_weapon_interact(new_weapon)
                
                elif name == 'weapon_interact':
                    current_weapon : str = self.stage_data[11]['current_weapon']
                    if current_weapon == core_object.storage.weapon_equipped:
                        pass
                    elif current_weapon in core_object.storage.owned_weapons:
                        core_object.storage.weapon_equipped = current_weapon
                        self.udpdate_stage11_weapon_interact(current_weapon)
                    else:
                        cost : int = core_object.storage.COST_TABLE['Weapons'][current_weapon]
                        if core_object.storage.upgrade_tokens >= cost:
                            core_object.storage.upgrade_tokens -= cost
                            self.update_token_count(self.stage)
                            core_object.storage.owned_weapons.append(current_weapon)
                            core_object.storage.weapon_equipped = current_weapon
                            self.udpdate_stage11_weapon_interact(current_weapon)
                        else:
                            self.alert_player('Not enough tokens!')

                elif name == 'upgrade_button':
                    if not the_sprite.visible: return
                    current_weapon : str = self.stage_data[11]['current_weapon']
                    if current_weapon in core_object.storage.owned_weapons:
                        self.exit_stage11()
                        self.enter_stage12(current_weapon)
                    else:
                        self.alert_player('You do not own this weapon!')


            case 12:
                if name == 'back_button':
                    self.goto_stage(11)
                elif name[:13] == 'upgrade_perk_':
                    self.upgrade_stage12_weapon_perk(name[13:])

            case 13:
                if name == 'back_button':
                    self.exit_stage13()
                
                elif name == 'prev_button':
                    self.stage_data[13]['armor_index'] -= 1
                    self.stage_data[13]['armor_index'] %= self.stage_data[13]['all_armors_lentgh']
                    new_armor : str = core_object.storage.ALL_ARMORS[self.stage_data[13]['armor_index']]
                    self.replace_stage13_armor_ui(self.stage_data[13]['current_armor'], new_armor)
                    self.stage_data[13]['current_armor'] = new_armor
                    self.udpdate_stage13_armor_interact()

                elif name == 'next_button':
                    self.stage_data[13]['armor_index'] += 1
                    self.stage_data[13]['armor_index'] %= self.stage_data[13]['all_armors_lentgh']
                    new_armor : str = core_object.storage.ALL_ARMORS[self.stage_data[13]['armor_index']]
                    self.replace_stage13_armor_ui(self.stage_data[13]['current_armor'], new_armor)
                    self.stage_data[13]['current_armor'] = new_armor
                    self.udpdate_stage13_armor_interact()
                
                elif name == 'armor_interact':
                    current_armor : str = self.stage_data[13]['current_armor']
                    if current_armor == core_object.storage.armor_equipped:
                        core_object.storage.armor_equipped = None
                        self.udpdate_stage13_armor_interact()
                    elif current_armor in core_object.storage.owned_armors:
                        core_object.storage.armor_equipped = current_armor
                        self.udpdate_stage13_armor_interact()
                    else:
                        cost : int = core_object.storage.COST_TABLE['Armors'][current_armor]
                        if core_object.storage.upgrade_tokens >= cost:
                            core_object.storage.upgrade_tokens -= cost
                            self.update_token_count(self.stage)
                            core_object.storage.owned_armors.append(current_armor)
                            core_object.storage.armor_equipped = current_armor
                            self.udpdate_stage13_armor_interact(current_armor)
                        else:
                            self.alert_player('Not enough tokens!')
                
                elif name == 'upgrade_button':
                    if not the_sprite.visible: return
                    current_armor : str = self.stage_data[13]['current_armor']
                    if current_armor in core_object.storage.owned_armors:
                        self.exit_stage13()
                        self.enter_stage14(current_armor)
                    else:
                        self.alert_player('You do not own this armor!')

            case 14:
                if name == 'back_button':
                    self.goto_stage(13)
                elif name[:13] == 'upgrade_perk_':
                    self.upgrade_stage14_armor_perk(name[13:])