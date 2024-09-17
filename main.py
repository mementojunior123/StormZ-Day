import pygame
import asyncio

pygame.init()

GAME_ICON = pygame.image.load('icon.png')
GAME_TITLE : str = "StormZ Day"
pygame.display.set_icon(GAME_ICON)

window_size = (960, 540)
window = pygame.display.set_mode(window_size)

pygame.mixer.set_num_channels(48)

from core.core import Core, core_object

core = core_object
core.init(window)
core.FPS = 120
if core.is_web(): core.setup_web(1)


pygame.display.set_caption(GAME_TITLE)

from game.sprite import Sprite
Sprite._core_hint()

from utils.animation import Animation, AnimationTrack, _sprite_hint
_sprite_hint()

from utils.ui.base_ui_elements import BaseUiElements, UiSprite
from utils.ui.textsprite import TextSprite
from utils.helpers import rotate_around_pivot_accurate, sign
from utils.particle_effects import ParticleEffect, Particle
from utils.my_timer import Timer
import utils.interpolation as interpolation
import utils.tween_module as TweenModule

from game.test_player import TestPlayer
from game.player import Player
from game.projectiles import BaseProjectile, PeirceProjectile, NormalProjectile
from game.enemy import BaseZombie, NormalZombie, QuickZombie, TankZombie, RangedZombie
from game.background import Background

TestPlayer()
Player()
Background()
for _ in range(99):
    NormalProjectile()
    PeirceProjectile()

for _ in range(90):
    NormalZombie()
    QuickZombie()
    TankZombie()
    RangedZombie()
core.settings.set_defualt({'Brightness' : 0})
core.settings.load()

core.set_brightness(core.settings.info['Brightness'])

core.menu.init()
core.game.init()

clock = pygame.Clock()
font_40 = pygame.font.Font('assets/fonts/Pixeltype.ttf', 40)



def start_game(event : pygame.Event):
    if event.type != core.START_GAME: return
    
    core.menu.prepare_exit()
    core.game.start_game()

    core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, Sprite.handle_mouse_event)
    core_object.event_manager.bind(pygame.FINGERDOWN, Sprite.handle_touch_event)
    core_object.event_manager.bind(pygame.KEYDOWN, detect_game_over)

    
    if core.IS_DEBUG: core.main_ui.add(fps_sprite)
    if core.IS_DEBUG: core.main_ui.add(debug_sprite)
   
    
def detect_game_over(event : pygame.Event):
    if event.type == pygame.KEYDOWN: 
        if event.key == pygame.K_ESCAPE:
            if core.game.wave_count == 1: core.game.wave_count = 0
            end_game(None)
        elif event.key == pygame.K_F1:
            pygame.image.save_extended(core.main_display, 'assets/screenshots/game_capture2.png', '.png')
    

def end_game(event : pygame.Event = None):
    victory : bool
    if event:
        victory = event.victory
    else:
        victory = False
    tokens_gained = (core.game.wave_count * 5)  + (core.game.score // 12) + 10
    core.storage.upgrade_tokens += tokens_gained
    core.menu.prepare_entry(4)
    core.menu.enter_stage4(core.game.score, core.game.wave_count, tokens_gained, victory)
    if core.game.score > core.storage.high_score:
        core.storage.high_score = core.game.score
    if core.game.wave_count > core.storage.high_wave:
        core.storage.high_wave = core.game.wave_count
    
    core_object.main_ui.clear_all()
    core.game.end_game()
    

    core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, Sprite.handle_mouse_event)
    core_object.event_manager.unbind(pygame.FINGERDOWN, Sprite.handle_touch_event)
    core_object.event_manager.unbind(pygame.KEYDOWN, detect_game_over)
    if core.menu.USE_RESULT_THEME:
        core_object.bg_manager.play(core_object.menu.main_theme, 1, loops=-1)
    elif not victory:
        core_object.bg_manager.play(core_object.menu.fail_theme, 1, loops=1)
    else:
        core_object.bg_manager.play(core.menu.victory_theme, 1, loops=1)

if core.IS_DEBUG: core.storage.upgrade_tokens = 999
core.game.active = False
core.menu.add_connections()
core.menu.update_highscores_stage1()
core.event_manager.bind(core.START_GAME, start_game)
core.event_manager.bind(core.END_GAME, end_game)
core.bg_manager.play(core.menu.main_theme, 1)
def setup_debug_sprites():
    global fps_sprite
    global debug_sprite

    fps_sprite = TextSprite(pygame.Vector2(15 + 63 - 63, 10), 'topleft', 0, 'FPS : 0', 'fps_sprite', 
                            text_settings=(font_40, 'White', False), text_stroke_settings=('Black', 2),
                            text_alingment=(9999, 5), colorkey=(255, 0,0))

    debug_sprite = TextSprite(pygame.Vector2(15, 200), 'midright', 0, '', 'debug_sprite', 
                            text_settings=(font_40, 'White', False), text_stroke_settings=('Black', 2),
                            text_alingment=(9999, 5), colorkey=(255, 0,0), zindex=999)

core.frame_counter = 0
cycle_timer = Timer(0.1, core_object.global_timer.get_time)

setup_debug_sprites()

async def main():
    while 1:
        core.update_dt(60)
        for event in pygame.event.get():
            core.event_manager.process_event(event)

        if core.game.active == False:
            window.fill(core.menu.bg_color)
            core.menu.update(core.dt)
            core.menu.render(window)
        else:
            if core.game.state != core.game.STATES.paused:
                Sprite.update_all_sprites(core.dt)
                Sprite.update_all_registered_classes(core.dt)
                core.game.main_logic(core.dt)

            window.fill((94,129,162))    
            Sprite.draw_all_sprites(window)
            core.main_ui.update()
            core.main_ui.render(window)

        core.update()
        if cycle_timer.isover(): 
            fps_sprite.text = f'FPS : {core.get_fps():0.0f}'
            cycle_timer.restart()
        if core.settings.info['Brightness'] != 0:
            window.blit(core.brightness_map, (0,0), special_flags=core.brightness_map_blend_mode)
            
        pygame.display.update()
        core.frame_counter += 1
        clock.tick(core.FPS)
        await asyncio.sleep(0)

asyncio.run(main())


