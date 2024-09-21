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
        self.bg_color = (94, 129, 162)
        self.stage = 1
        self.stage_data : list[dict] = [{} for _ in range(20 + 1)]
        self.stage_data[0] = None
        window_size = core_object.main_display.get_size()
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

        #stage1 --> stage 2
        [BaseUiElements.new_text_sprite('Upgrades', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        BaseUiElements.new_button('GreenButton', 'Ready', 1, 'bottomright', (940, window_size[1] - 15), (0.4, 1.0), 
        {'name' : 'ready_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Next', 1, 'midbottom', (centerx + 100, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'next_button'}, (Menu.font_40, 'Black', False)),
        
        *self.make_general_upgrade_bar('Firerate', pygame.Vector2(180, 110), 'Shoot faster. 20% per stack.'),
        *self.make_general_upgrade_bar('Damage', pygame.Vector2(465, 110), 'Deal more damage. 20% per stack.'),
        *self.make_general_upgrade_bar('Vitality', pygame.Vector2(750, 110), 'Get more health. 20% per stack.')
        ],

        #stage 2 --> stage 3
        [BaseUiElements.new_text_sprite('Weapons', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
         BaseUiElements.new_button('GreenButton', 'Ready', 1, 'bottomright', (940, window_size[1] - 15), (0.4, 1.0), 
        {'name' : 'ready_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Prev', 1, 'midbottom', (centerx - 100, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'prev_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Next', 1, 'midbottom', (centerx + 100, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'next_button'}, (Menu.font_40, 'Black', False)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        *self.make_weapon_ui('Pistol', (100, 110), 'A budget starting weapon.'), 
        *self.make_weapon_ui('Rifle', (345, 110), 'Shoots quickly.'), 
        *self.make_weapon_ui('Shotgun', (590, 110), 'Shoots multiple pellets at once, dealing big damage.'), 
        *self.make_weapon_ui('Piercer', (835, 110), 'Bullets go trough enemies. Useful when enemies start to stack.')
        ],
        #stage 3 --> stage 4
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
        #stage 4 --> stage 5
        [BaseUiElements.new_text_sprite('Armors', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
         BaseUiElements.new_button('GreenButton', 'Ready', 1, 'bottomright', (940, window_size[1] - 15), (0.4, 1.0), 
        {'name' : 'ready_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 10), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Prev', 1, 'midbottom', (centerx - 100, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'prev_button'}, (Menu.font_40, 'Black', False)),
        UiSprite(Menu.token_image, Menu.token_image.get_rect(topright = (955, 15)), 0, 'token_image'),
        TextSprite(pygame.Vector2(903, 40), 'midright', 0, '3', 'token_count', None, None, 0, (Menu.font_50, 'White', False), ('Black', 2), colorkey=[0,255,0]),
        *self.make_armor_ui('Light', (100, 110), 'Offers decent protection and keeps you moving fast.'), 
        *self.make_armor_ui('Balanced', (345, 110), 'The best of both worlds.'), 
        *self.make_armor_ui('Heavy', (590, 110), 'Makes you much more tanky, at the cost of your speed.'), 
        *self.make_armor_ui('Adaptative', (835, 110), 
'''Completely negates all damage while active, but falls apart
very quickly if you get overwhelmed.
Useful for skilled players.''')],
        #stage 5 --> stage 6
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
        #stage 6 --> stage 7
        [
        BaseUiElements.new_text_sprite('Choose control scheme', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        *self.make_control_scheme_ui('Mobile', (100, 200), 'Use this if you are playing on mobile or on a touchscreen.'),
        *self.make_control_scheme_ui('Simple', (345, 200), 'Shots will automatically go to the nearest enemy.\nUse the mouse or the arrow keys to aim manually.'),
        *self.make_control_scheme_ui('Mixed', (590, 200), 'Aim with the arrow keys when using SPACE to shoot.\nAim using the mouse when clicking to shoot.'), 
        *self.make_control_scheme_ui('Expert', (835, 200), 'Aim with the mouse.\nRecommended for more experienced players.')
        ],
        #stage 7 --> stage 8
        [
        BaseUiElements.new_text_sprite('Are you sure? This action is irreversible.', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 25)),
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'midleft', (200, 200), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('RedButton', 'RESET', 1, 'midright', (740, 200), (0.4, 1.0), 
        {'name' : 'reset_button'}, (Menu.font_40, 'Black', False)),
        ]
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
        for upgrade in core_object.storage.general_upgrades:
            self.update_general_upgrade_bar(upgrade)
        self.update_token_count()

    def make_general_upgrade_bar(self, name : str, midtop : pygame.Vector2, tooltip : str):
        upgrade_bar_surf1 = make_upgrade_bar()
        title = TextSprite(midtop, 'midtop', 0, f'{name} I\nCost : 2', f'{name}_upg_title', {}, {}, 0, 
                           (Menu.font_50, 'Black', False), colorkey=[0, 255, 0])
        bar = UiSprite(upgrade_bar_surf1.copy(), upgrade_bar_surf1.get_rect(midtop = midtop + (0, 75)), 0, f'{name}_upg_bar')

        button = BaseUiElements.new_button('BlueButton', 'Buy', 1, 'midtop', midtop + (0, 200), (0.35, 1), 
        {'name' : f'buy_{name}'}, (Menu.font_40, 'Black', False))

        tooltip = ToolTip(pygame.Vector2(15, 440), 'bottomleft', 0, tooltip, title.rect.unionall([bar.rect, button.rect]), f'tooltip_{name}',
                          text_settings=(Menu.font_50, 'Black', False), colorkey=[0, 255, 0])
        return title, bar, button, tooltip

    def update_general_upgrade_bar(self, name : str):
        upgrade_bar = self.get_sprite_by_name(2, f'{name}_upg_bar')
        if not upgrade_bar: return
        upgrade_level : int = core_object.storage.general_upgrades[name]
        upgrade_title : TextSprite = self.get_sprite_by_name(2, f'{name}_upg_title')
        midtop : pygame.Vector2 = pygame.Vector2(upgrade_title.rect.midtop)
        reset_upgrade_bar(upgrade_bar.surf)
        for i in range(upgrade_level):
            paint_upgrade_bar(upgrade_bar.surf, i)
            if i >= 4: break

        if upgrade_level >= 5:
            new_button = BaseUiElements.new_button('BlueButton', 'MAXED', 1, 'midtop', midtop + (0, 200), (0.35, 1), 
                                                   {'name' : f'buy_{name}'}, (Menu.font_40, 'Black', False))
            self.find_and_replace(new_button, 2, name= f'buy_{name}')
            upgrade_title.text = f'{name} {'MAXED'}\nCost : MAXED'
        else:
            new_button = BaseUiElements.new_button('BlueButton', 'Buy', 1, 'midtop', midtop + (0, 220), (0.35, 1), 
                                                   {'name' : f'buy_{name}'}, (Menu.font_40, 'Black', False))
            self.find_and_replace(new_button, 2, name=f'buy_{name}')
            upgrade_title.text = f'{name} {to_roman(upgrade_level + 1)}\nCost : {core_object.storage.COST_TABLE['General Upgrades'][name][upgrade_level+1]}'

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
        self.stage = 3
        for weapon in core_object.storage.ALL_WEAPONS:
            self.update_weapon_ui_stage3(weapon)
        self.update_token_count(self.stage)
    
    def enter_stage5(self):
        self.stage = 5
        for armor in core_object.storage.ALL_ARMORS:
            self.update_armor_ui_stage5(armor)
        self.update_token_count(self.stage)

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
        self.stage_data[7].clear()
        self.enter_any_stage(old_stage)
    
    def enter_stage8(self):
        self.stage_data[8]['prev_stage'] = self.stage
        self.stage = 8

    def exit_stage8(self):
        old_stage : int = self.stage_data[8].get('prev_stage', None)
        if not old_stage: old_stage = 1
        self.stage_data[8].clear()
        self.enter_any_stage(old_stage)

    def enter_any_stage(self, new_stage : int):
        match new_stage:
            case 1|7:
                self.enter_stage1()
            case 2:
                self.enter_stage2()
            case 3:
                self.enter_stage3()
            case 4:
                self.enter_stage4()
            case 5:
                self.enter_stage5()
            case 6:
                self.enter_stage6()
            case 8:
                self.enter_stage8()
            case _:
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
        trigger_type : str = event.trigger_type
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                if name == "play_button":
                    self.enter_stage2()
                elif name == "settings_button":
                    self.enter_stage6()
            case 2:
                if name[:4] == 'buy_':
                    upg_name = name[4:]
                    current_level : int = core_object.storage.general_upgrades[upg_name] 
                    if current_level < 5:
                        cost : int = core_object.storage.COST_TABLE['General Upgrades'][upg_name][current_level + 1]
                        if core_object.storage.upgrade_tokens >= cost:
                            core_object.storage.upgrade_tokens -= cost
                            core_object.storage.general_upgrades[upg_name] += 1
                            self.update_general_upgrade_bar(upg_name)
                            self.update_token_count()
                        else:
                            self.alert_player('Not enough tokens!')
                    else:
                        self.alert_player('This stat is already maxed!')
    
                elif name == 'ready_button':
                    self.launch_game()
                
                elif name == 'back_button':
                    self.enter_stage1()
                elif name == 'next_button':
                    self.enter_stage3()
            
            case 3:
                if name == 'back_button':
                    self.enter_stage1()
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
                    self.enter_stage1()
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