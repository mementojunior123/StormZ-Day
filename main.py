import pygame
import asyncio

pygame.init()

GAME_ICON = pygame.image.load('icon.png')
GAME_TITLE : str = "StormZ Day"
pygame.display.set_icon(GAME_ICON)
window_size = (960, 540)
window = pygame.display.set_mode(window_size)
pygame.mixer.set_num_channels(48)
pygame.display.set_caption(GAME_TITLE)


from core.core import Core, core_object
core = core_object
core.init(window)
core.FPS = 600
if core.is_web(): core.setup_web(1)
core._hints()

from game.sprite import Sprite
Sprite._core_hint()

from utils.animation import Animation, AnimationTrack, _sprite_hint
_sprite_hint()

core.menu.init()
core.game.init()

clock = pygame.Clock()
font_40 = pygame.font.Font('assets/fonts/Pixeltype.ttf', 40)

core.game.active = False
core.menu.add_connections()
core.bg_manager.play(core.menu.main_theme, 1)

async def main():
    core.load_game()
    if core.settings.info['ControlMethod']:
        core.menu.enter_stage1()
    else:
        core.menu.stage = 7
    if core.IS_DEBUG: core.storage.upgrade_tokens = 999
    core.set_brightness(core.settings.info['Brightness'])
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
        if core.cycle_timer.isover(): 
            core.fps_sprite.text = f'FPS : {core.get_fps():0.0f}'
            core.cycle_timer.restart()
        if core.settings.info['Brightness'] != 0:
            window.blit(core.brightness_map, (0,0), special_flags=core.brightness_map_blend_mode)
            
        pygame.display.update()
        core.frame_counter += 1
        clock.tick(core.FPS)
        await asyncio.sleep(0)

asyncio.run(main())


