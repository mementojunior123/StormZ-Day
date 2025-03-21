import pygame
from game.sprite import Sprite
from core.core import core_object

from utils.animation import Animation
from utils.pivot_2d import Pivot2D

from game.projectiles import BaseProjectile
from game.enemy import BaseZombie
from utils.helpers import make_upgrade_bar, reset_upgrade_bar, load_alpha_to_colorkey, make_circle, closest_point, make_right_arrow
from utils.ui.ui_sprite import UiSprite
from utils.my_timer import Timer
from dataclasses import dataclass
from game.weapons import FiringModes, WeaponStats, WeaponBuff, WeaponBuffTypes, WEAPONS
from game.weapons import BaseWeapon, ShotgunWeapon , PeirceWeapon
from game.armor import ArmorBuff, ArmorBuffTypes, ArmorStats, ARMORS
from game.armor import BaseArmor

class PlayerJoystick:
    def __init__(self, position : pygame.Vector2, amplitude : float = 50, deadzone : float = 0.2) -> None:
        self.start_pos : pygame.Vector2 = position.copy()
        self.pos : pygame.Vector2 = position.copy()
        self.deadzone : float = deadzone

        self.grab_id : int|None = None
        self.grab_offset : pygame.Vector2|None = None
        self.is_grabbed : bool = False

        self.amplitude : float = amplitude
        circle1 = make_circle(self.amplitude * 0.5, (150, 150, 150)).convert_alpha()
        circle2 = make_circle(self.amplitude, (90, 90, 90))
        circle2 = circle2.convert_alpha()
        circle2.set_alpha(180)
        circle1.set_alpha(225)
        self.visual_component : UiSprite = UiSprite(circle1, circle1.get_rect(center = self.pos), 0, 'joystick', zindex=2)
        self.background : UiSprite = UiSprite(circle2, circle2.get_rect(center = self.start_pos), 0, 'joy_background', zindex=1)
        core_object.main_ui.add(self.visual_component)
        core_object.main_ui.add(self.background)

    def update(self):
        if not self.is_grabbed: 
            self.pos = self.start_pos.copy()
        else:
            self.pos = pygame.Vector2(core_object.active_fingers[self.grab_id]) + self.grab_offset
        self.clamp_pos()
        self.update_visuals()
    
    def grab(self, finger_id : int, grab_pos : pygame.Vector2|None, force_grab : bool = False):
        if self.is_grabbed: return
        if (not self.can_grab(grab_pos)) or (not force_grab): return
        if grab_pos is None: grab_pos = pygame.Vector2(core_object.active_fingers[finger_id])
        
        self.grab_id = finger_id
        self.is_grabbed = True
        self.grab_offset = pygame.Vector2(0,0)
    
    def stop_grab(self):
        self.pos = self.start_pos.copy()
        self.grab_id = None
        self.is_grabbed = False
        self.grab_offset = None
    
    def clamp_pos(self):
        offset : pygame.Vector2 = (self.pos - self.start_pos)
        if offset.magnitude() > self.amplitude:
            offset.scale_to_length(self.amplitude)
            self.pos = self.start_pos + offset

    def get_vector(self, do_update : bool = False) -> pygame.Vector2:
        if not self.is_grabbed: return pygame.Vector2(0,0)
        if do_update: self.update()
        offset : pygame.Vector2 = self.pos - self.start_pos
        if offset.magnitude() <= 0: return pygame.Vector2(0,0)
        distance : float = offset.magnitude()
        direction : pygame.Vector2 = offset.normalize()
        speed : float = 1 if distance > self.amplitude * self.deadzone else 0
        return direction * speed
    
    def can_grab(self, grab_pos : pygame.Vector2) -> bool:
        distance : float = (grab_pos - self.start_pos).magnitude()
        return (distance <= self.amplitude)
    
    def make_visuals(self):
        circle1 = make_circle(10, (150, 150, 150))
        circle2 = make_circle(self.amplitude, (90, 90, 90))
        self.visual_component : UiSprite = UiSprite(circle1, circle1.get_rect(center = self.pos), 0, 'joystick', zindex=2)
        self.background : UiSprite = UiSprite(circle2, circle2.get_rect(center = self.start_pos), 0, 'joy_background', zindex=1)

    def update_visuals(self):
        self.background.rect.center = round(self.start_pos)
        self.visual_component.rect.center = round(self.pos)

class Player(Sprite):
    active_elements : list['Player'] = []
    inactive_elements : list['Player'] = []
    offset = 0
    '''
    test_image : pygame.Surface = pygame.surface.Surface((50, 50))
    test_image.set_colorkey([0, 0, 255])
    test_image.fill([0, 0, 255])
    pygame.draw.circle(test_image, "Green", (25, 25), 25)
    '''
    test_image : pygame.Surface = load_alpha_to_colorkey('assets/graphics/player/main.png', [0, 255, 0])
    ui_heart_image : pygame.Surface = pygame.image.load("assets/graphics/ui/heart_green_colorkey.png")
    ui_heart_image.set_colorkey([0, 255, 0])
    ui_heart_image = pygame.transform.scale_by(ui_heart_image, 0.1)

    death_anim : Animation = Animation.get_animation("player_death")
    screen_transition : Animation = Animation.get_animation("player_screen_transition")
    hit_sound = pygame.mixer.Sound('assets/audio/hit.ogg')
    hit_sound.set_volume(0.15)

    shot_sfx = pygame.mixer.Sound('assets/audio/shot.ogg')
    shot_sfx.set_volume(0.10)

    fast_shot_sfx = pygame.mixer.Sound('assets/audio/fast_shot.ogg')
    fast_shot_sfx.set_volume(0.10)

    def __init__(self) -> None:
        super().__init__()
        self.max_hp : int
        self.hp : int

        self.main_heart : UiSprite|None = None
        self.ui_healthbar : UiSprite|None = None
        self.ui_aim_arrow : UiSprite|None = None
        self.current_aim_arrow_orientation : pygame.Vector2|None = None
        self.last_arrow_press_timer : Timer|None = None
        self.armor_healthbar : UiSprite|None = None
        self.weapon : BaseWeapon
        self.armor : BaseArmor|None

        self.equipped_weapon_perks : dict[str, int]|None = None
        self.equipped_armor_perks : dict[str, int]|None = None

        self.current_direction : pygame.Vector2
        self.last_shot_direction : pygame.Vector2

        self.movement_joystick : PlayerJoystick|None
        self.aim_joystick : PlayerJoystick|None
        self.finger_id_stack : list[int]|None
        self.arrow_map : dict[int, Timer|bool]|None

        self.dynamic_mask = True
        Player.inactive_elements.append(self)

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2):
        element = cls.inactive_elements[0]
        cls.unpool(element)

        element.image = cls.test_image
        element.rect = element.image.get_rect()

        element.current_direction = pygame.Vector2(0,0)
        element.last_shot_direction = pygame.Vector2(1,0)
        element.last_arrow_press_timer = Timer(0, time_source=core_object.game.game_timer.get_time)
        if core_object.settings.info['ControlMethod'] == "Mobile":
            amplitudes = {'Small' : 40, 'Medium' : 70, 'Large' : 90}
            diffs = {'Small' : 0, 'Medium' : -8, 'Large' : -18}
            diff = diffs[core_object.settings.info['JoystickSize']]
            amplitude = amplitudes[core_object.settings.info['JoystickSize']]
            element.movement_joystick = PlayerJoystick(pygame.Vector2(80 - diff, 460 + diff), amplitude=amplitude)
            element.aim_joystick = PlayerJoystick(pygame.Vector2(880 + diff, 460 + diff), amplitude=amplitude)
            element.finger_id_stack = []
        else:
            element.movement_joystick = None
            element.aim_joystick = None
            element.finger_id_stack = None
        element.arrow_map = {pygame.K_UP : False, pygame.K_DOWN : False, pygame.K_LEFT : False, pygame.K_RIGHT : False}

        element.position = new_pos
        element.align_rect()
        element.zindex = 50

        element.pivot = Pivot2D(element._position, element.image, (0, 0, 255))
        element.max_hp = 5 
        element.hp = element.max_hp
        
        use_debug_weapon = 'debug' if (pygame.key.get_pressed()[pygame.K_o]) and core_object.IS_DEBUG else False
        element.weapon = WEAPONS[use_debug_weapon or core_object.storage.weapon_equipped]
        element.weapon.get_game_source()

        element.weapon.stats.reset()
        element.equipped_weapon_perks = core_object.storage.current_weapon_perks[core_object.storage.weapon_equipped]
        firerate_level : int = element.equipped_weapon_perks.get('Firerate', 0)
        damage_level : int = element.equipped_weapon_perks.get('Damage', 0)
        element.weapon.stats.apply_perma_buff(WeaponBuff(WeaponBuffTypes.firerate_mult, 0.2 * firerate_level))
        element.weapon.stats.apply_perma_buff(WeaponBuff(WeaponBuffTypes.dmg_mult, 0.2 * damage_level))
        element.weapon.ready_shot_cooldown()

        element.armor = ARMORS[core_object.storage.armor_equipped]
        if element.armor:
            element.armor.get_game_source()
            element.armor.stats.reset()
            
        if core_object.storage.armor_equipped:
            element.equipped_armor_perks = core_object.storage.current_armor_perks[core_object.storage.armor_equipped]
            element.max_hp *= (1 + element.equipped_armor_perks.get('Vitality', 0) * 0.2)
            element.hp = element.max_hp

        bar_image = make_upgrade_bar(150, 25, 1)
        element.ui_healthbar = UiSprite(bar_image, bar_image.get_rect(topright = (950, 20)), 0, 'healthbar')
        core_object.main_ui.add(element.ui_healthbar)
        element.update_healthbar()

        if element.armor:
            bar_image2 = make_upgrade_bar(150, 25, 1)
            element.armor_healthbar = UiSprite(bar_image2, bar_image2.get_rect(topright = (950, element.ui_healthbar.rect.bottom + 10)), 0, 'a_healthbar')
            core_object.main_ui.add(element.armor_healthbar)
            element.update_armor_healthbar()
        element.main_heart = UiSprite(Player.ui_heart_image, Player.ui_heart_image.get_rect(topright = (793, 15)), 
                                      0, f'heart', colorkey=[0, 255, 0], zindex=1)
        element.ui_aim_arrow = None
        element.current_aim_arrow_orientation = pygame.Vector2(0,0)
        return element
    
    def update(self, delta: float):
        if self.movement_joystick: self.movement_joystick.update()
        if self.aim_joystick: self.aim_joystick.update()
        if not core_object.game.is_nm_state(): return
        self.current_direction = self.get_movement_vector()
        self.input_action()
        self.do_movement(delta)
        self.do_collisions()
        if self.armor: self.armor.update(delta)
        self.update_healthbars()
        self.update_aim_arrow()

    def update_aim_arrow(self):
        if core_object.settings.info['ControlMethod'] == 'Mobile': return
        arrow_vec : pygame.Vector2 = self.get_arrow_map_direction()
        aim_arrow : UiSprite|None = self.ui_aim_arrow
        if arrow_vec.magnitude() != 0:
            self.current_aim_arrow_orientation = arrow_vec
        elif self.last_arrow_press_timer.isover():
            self.current_aim_arrow_orientation = pygame.Vector2(0,0)

        if aim_arrow: core_object.main_ui.remove(aim_arrow)
        if self.current_aim_arrow_orientation.magnitude() <= 0: return


        arrow_dir = self.current_aim_arrow_orientation
        surf : pygame.Surface = make_right_arrow(20, 20)
        offset : pygame.Vector2 = pygame.Vector2(50, 0)
        angle : float = arrow_dir.angle_to(pygame.Vector2(1, 0))

        surf = pygame.transform.rotate(surf, angle)
        offset.rotate_ip(-angle)
        rect : pygame.Rect = surf.get_rect(center = round(self.position + offset))

        new_aim_arrow : UiSprite = UiSprite(surf, rect, 0, 'aim_arrow', zindex=20)
        core_object.main_ui.add(new_aim_arrow)
        self.ui_aim_arrow = new_aim_arrow

    
    def get_movement_vector(self) -> pygame.Vector2:
        control_scheme : str = core_object.settings.info['ControlMethod']
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        if control_scheme != 'Mobile':
            keyboard_map = pygame.key.get_pressed()
            if keyboard_map[pygame.K_a]:
                move_vector += pygame.Vector2(-1, 0)
            if keyboard_map[pygame.K_d]:
                move_vector += pygame.Vector2(1, 0)
            if keyboard_map[pygame.K_s]:
                move_vector += pygame.Vector2(0, 1)
            if keyboard_map[pygame.K_w]:
                move_vector += pygame.Vector2(0, -1)
            if move_vector.magnitude() != 0: move_vector.normalize_ip()
        else:
            move_vector = self.movement_joystick.get_vector()
        return move_vector
    
    def get_mouse_vector(self) -> pygame.Vector2:
        return (pygame.Vector2(pygame.mouse.get_pos()) - self.position).normalize()
    
    def get_arrow_key_vector(self) -> pygame.Vector2:
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        if keyboard_map[pygame.K_LEFT]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_RIGHT]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_DOWN]:
            move_vector += pygame.Vector2(0, 1)
        if keyboard_map[pygame.K_UP]:
            move_vector += pygame.Vector2(0, -1)
        if move_vector.magnitude() != 0: move_vector.normalize_ip()
        return move_vector
    
    def update_arrow_map(self):
        if not self.arrow_map: return
        keyboard_map = pygame.key.get_pressed()
        KEYS : tuple[int] = (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_UP)
        any_press : bool = False
        for key in KEYS:
            is_pressed : bool = keyboard_map[key]
            val : bool|Timer = self.arrow_map[key]
            if is_pressed:
                self.arrow_map[key] = True
                any_press = True
            else:
                if val is True:
                    self.arrow_map[key] = Timer(0.06, core_object.game.game_timer.get_time)
                elif val is False:
                    pass
                else:
                    if val.isover():
                        self.arrow_map[key] = False
        if not any_press:
            for key in KEYS:
                self.arrow_map[key] = False
        else:
            self.last_arrow_press_timer.set_duration(0.15)
    
    def get_arrow_map_direction(self) -> pygame.Vector2:
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        if self.arrow_map[pygame.K_LEFT]:
            move_vector += pygame.Vector2(-1, 0)
        if self.arrow_map[pygame.K_RIGHT]:
            move_vector += pygame.Vector2(1, 0)
        if self.arrow_map[pygame.K_DOWN]:
            move_vector += pygame.Vector2(0, 1)
        if self.arrow_map[pygame.K_UP]:
            move_vector += pygame.Vector2(0, -1)
        if move_vector.magnitude() != 0: move_vector.normalize_ip()
        return move_vector
    
    def input_action(self):
        self.update_arrow_map()
        if not self.weapon.stats.fire_mode == FiringModes.auto: return
        control_scheme : str = core_object.settings.info['ControlMethod']
        if control_scheme == 'Mobile':
            if self.finger_id_stack and core_object.active_fingers:
                active_fingers : list[int] = list(core_object.active_fingers.keys())
                if (len(active_fingers) >= 2) or (active_fingers[0] != self.movement_joystick.grab_id):
                    self.shoot('Touch', pygame.Vector2(core_object.active_fingers[self.finger_id_stack[-1]]))
            elif self.aim_joystick.get_vector():
                self.shoot('Touch', list(core_object.active_fingers.values())[-1])
            return
        elif control_scheme != 'Expert':
            arrow_dir = self.get_arrow_map_direction()
            if arrow_dir.magnitude() > 0: self.last_shot_direction = arrow_dir
        
        if (pygame.mouse.get_pressed()[0] and core_object.game.game_timer.get_time() > 0.3): 
            self.shoot('Mouse')
        elif (pygame.key.get_pressed())[pygame.K_SPACE]:
            self.shoot('Space')

    def do_movement(self, delta : float):
        speed : float = 7.0
        if self.armor: speed *= self.armor.speed_pen
        self.position += self.current_direction * speed * delta
        self.clamp_rect(pygame.Rect(0,0, *core_object.main_display.get_size()))
    
    def do_collisions(self):
        enemies : list[BaseZombie] = self.get_all_colliding(BaseZombie)
        for enemy in enemies:
            if not isinstance(enemy, BaseZombie): continue
            if enemy.is_dying: continue
            enemy.kill_instance_safe()
            self.take_damage(enemy.damage)
        
        bullets : list[BaseProjectile] = self.get_all_colliding(BaseProjectile)
        for bullet in bullets:
            if not isinstance(bullet, BaseProjectile): continue
            if not bullet.is_hostile('Friendly'): continue
            self.take_damage(bullet.damage)
            bullet.when_hit()

    
    def is_alive(self) -> bool:
        return (self.hp > 0)
    
    def can_take_damage(self):
        return True

    def take_damage(self, damage : int):
        if not self.can_take_damage(): return
        if self.armor:
            self.hp -= self.armor.take_damage(damage)
        else:
            self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        core_object.bg_manager.play_sfx(self.hit_sound, 1)
        self.update_healthbars()
    
    def shoot(self, input_method : str, press_pos : None|pygame.Vector2 = None):
        if not self.weapon.shot_cooldown.isover(): return
        control_scheme : str = core_object.settings.info['ControlMethod']
        mouse_direction : pygame.Vector2 = (pygame.Vector2(pygame.mouse.get_pos()) - self.position).normalize()
        key_direction : pygame.Vector2 = self.last_shot_direction.copy()
        arrow_direction : pygame.Vector2 = self.get_arrow_map_direction()
        shot_direction : pygame.Vector2
        if control_scheme == 'Expert':
            shot_direction = mouse_direction

        elif control_scheme == 'Mixed':
            if input_method == 'Mouse':
                shot_direction = mouse_direction
            elif arrow_direction.magnitude() != 0:
                shot_direction = self.correct_aim(arrow_direction)
            else:
                shot_direction = self.correct_aim(key_direction)

        elif control_scheme == 'Simple':
            if input_method == 'Mouse': shot_direction = mouse_direction
            else:
                if arrow_direction.magnitude() != 0:
                    shot_direction = self.correct_aim(arrow_direction)
                else:
                    shot_direction = self.correct_aim(key_direction) 


        elif control_scheme == 'Mobile':
            shot_direction = self.correct_aim(self.aim_joystick.get_vector() or (press_pos - self.position).normalize(), 14)
        
        shot_origin = self.position
        self.use_weapon(shot_origin, shot_direction)
        self.last_shot_direction = shot_direction.copy()
    
    def use_weapon(self, shot_origin : pygame.Vector2, shot_direction : pygame.Vector2):
        result : BaseProjectile|list[BaseProjectile]|None
        match core_object.storage.weapon_equipped:
            case 'Pistol':
                result = self.weapon.shoot(shot_origin, shot_direction)
            case 'Shotgun':
                weapon : ShotgunWeapon = self.weapon
                result = weapon.shoot(shot_origin, shot_direction, 1 if not self.equipped_weapon_perks.get('Tight Spread', 0) else 0.85)
            case 'Rifle':
                result = self.weapon.shoot(shot_origin, shot_direction)
            case 'Piercer':
                weapon : PeirceWeapon = self.weapon
                result = weapon.shoot(shot_origin, shot_direction)
            
        if result:
            core_object.bg_manager.play_sfx(self.shot_sfx if self.weapon.stats.firerate <= 7 else self.fast_shot_sfx, 1)

    def correct_aim(self, shot_direction : pygame.Vector2, max_aim_correction : float = 17.5) -> pygame.Vector2:
        if not BaseZombie.active_elements: return shot_direction
        closest_angle : float = 9999
        closest_enemy : BaseZombie|None = None
        closest_enemy_direction : pygame.Vector2|None = None
        V = pygame.Vector2
        player_to_zomb_vec : pygame.Vector2
        angle_diff : float
        for enemy in BaseZombie.active_elements:
            player_to_zomb_vec = (enemy.position - self.position).normalize()
            angle_diff = abs((player_to_zomb_vec).angle_to(shot_direction))
            if angle_diff > 180: angle_diff = 360 - angle_diff
            if angle_diff < closest_angle:
                closest_angle = angle_diff
                closest_enemy = enemy
                closest_enemy_direction = player_to_zomb_vec
        
        if not enemy: return shot_direction
        if closest_angle <= 0.8 or closest_angle >= max_aim_correction: return shot_direction
        return closest_enemy_direction


    def update_healthbar(self):
        hp_percent : float = self.hp / self.max_hp
        colors = {'Dark Green' : 0.8, 'Green' : 0.6, 'Yellow' : 0.4, 'Orange' : 0.2, 'Red' : -1}
        for color, value in colors.items():
            if hp_percent > value:
                break
        reset_upgrade_bar(self.ui_healthbar.surf, 1, 150, 25)
        pygame.draw.rect(self.ui_healthbar.surf, color, (3, 3, pygame.math.lerp(0, 150, hp_percent), 25))
    
    def update_healthbars(self):
        self.update_healthbar()
        if self.armor: self.update_armor_healthbar()
    
    def update_armor_healthbar(self): 
        if not self.armor: return
        reset_upgrade_bar(self.armor_healthbar.surf, 1, 150, 25)
        armor_percent : float = self.armor.stats.health / self.armor.stats.max_health
        pygame.draw.rect(self.armor_healthbar.surf, (26, 156, 217), (3, 3, pygame.math.lerp(0, 150, armor_percent), 25))

    
    def handle_key_event(self, event : pygame.Event):
        if event.type != pygame.KEYDOWN: return
        if not core_object.game.is_nm_state(): return
        if core_object.settings.info['ControlMethod'] == 'Mobile': return
        if event.key == pygame.K_SPACE:
            self.shoot('Space')
    
    def handle_mouse_event(self, event : pygame.Event):
        if event.type != pygame.MOUSEBUTTONDOWN: return
        if event.touch: return
        if core_object.settings.info['ControlMethod'] == 'Mobile': return
        if not core_object.game.is_nm_state(): return
        if event.button == 1:
            self.shoot('Mouse')
    
    def handle_touch_event(self, event : pygame.Event):
        if core_object.settings.info['ControlMethod'] != 'Mobile': return
        window_size : tuple[int, int] = core_object.main_display.get_size()
        if event.type == pygame.FINGERDOWN:
            press_pos : pygame.Vector2 = pygame.Vector2(event.x * window_size[0], event.y * window_size[1])
            #print(press_pos)
            finger_id : int = event.finger_id
            if finger_id not in self.finger_id_stack: self.finger_id_stack.append(finger_id)

            did_grab : bool = False
            if self.movement_joystick:
                self.movement_joystick.update()
                if not self.movement_joystick.is_grabbed and self.movement_joystick.can_grab(press_pos):
                    self.movement_joystick.grab(finger_id, press_pos, True)
                    did_grab = True
                    self.finger_id_stack.remove(finger_id)
            
            if self.aim_joystick:
                self.aim_joystick.update()
                if not self.aim_joystick.is_grabbed and self.aim_joystick.can_grab(press_pos):
                    self.aim_joystick.grab(finger_id, press_pos, True)
                    did_grab = True
                    self.finger_id_stack.remove(finger_id)

            if not did_grab:
                if core_object.game.is_nm_state():
                    pass
                    #self.shoot("Touch", press_pos)
            


        elif event.type == pygame.FINGERUP:
            finger_id : int = event.finger_id
            if finger_id in self.finger_id_stack: self.finger_id_stack.remove(finger_id)
            #print(self.finger_id_stack, core_object.active_fingers, self.movement_joystick.pos)
            if self.movement_joystick:
                if finger_id == self.movement_joystick.grab_id:
                    self.movement_joystick.stop_grab()
            if self.aim_joystick:
                if finger_id == self.aim_joystick.grab_id:
                    self.aim_joystick.stop_grab()
            

    @classmethod
    def receive_key_event(cls, event : pygame.Event):
        for element in cls.active_elements:
            element.handle_key_event(event)
    
    @classmethod
    def receive_mouse_event(cls, event : pygame.Event):
        for element in cls.active_elements:
            element.handle_mouse_event(event)
    
    @classmethod
    def receive_touch_event(cls, event : pygame.Event):
        for element in cls.active_elements:
            element.handle_touch_event(event)
    
    def clean_instance(self):
        super().clean_instance()

        self.current_direction = None
        self.current_aim_arrow_orientation = None
        self.last_shot_direction = None
        self.movement_joystick = None
        self.aim_joystick = None
        self.finger_id_stack = None
        self.arrow_map = None
        
        self.hp = None
        self.max_hp = None
        self.shot_cooldown = None
        self.weapon = None

        self.equipped_weapon_perks = None
        self.equipped_armor_perks = None

        self.main_heart = None
        self.ui_healthbar = None
        self.last_arrow_press_timer = None
        self.ui_aim_arrow = None
    

Sprite.register_class(Player)


def make_connections():
    core_object.event_manager.bind(pygame.KEYDOWN, Player.receive_key_event)
    core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, Player.receive_mouse_event)
    core_object.event_manager.bind(pygame.FINGERDOWN, Player.receive_touch_event)
    core_object.event_manager.bind(pygame.FINGERUP, Player.receive_touch_event)

def remove_connections():
    core_object.event_manager.unbind(pygame.KEYDOWN, Player.receive_key_event)
    core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, Player.receive_mouse_event)
    core_object.event_manager.bind(pygame.FINGERDOWN, Player.receive_touch_event)
    core_object.event_manager.bind(pygame.FINGERUP, Player.receive_touch_event)
    
Player()