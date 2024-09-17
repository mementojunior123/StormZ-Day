import pygame
from game.sprite import Sprite
from core.core import core_object
from utils.pivot_2d import Pivot2D
from game.projectiles import BaseProjectile, PeirceProjectile
from utils.helpers import load_alpha_to_colorkey, scale_surf, tuple_vec_average, make_circle
from utils.ui.textsprite import TextSprite
from game.weapons import BaseWeapon, FiringModes, WeaponBuff, WeaponBuffTypes, WeaponStats, WEAPONS
import utils.tween_module as TweenModule
import utils.interpolation as interpolation
from utils.my_timer import Timer

class ZombieTypes:
    normal = 'normal'
    quick = 'quick'
    tank = 'tank'
    ranged = 'ranged'
    zombie_dict : dict[str]

    @staticmethod
    def convert(ztype : str):
        return ZombieTypes.zombie_dict[ztype]
    
    @classmethod
    def get_dict(cls):
        cls.zombie_dict = {cls.normal : NormalZombie, cls.quick : QuickZombie, cls.tank : TankZombie, cls.ranged : RangedZombie}

class ZombieCluster:
    def __init__(self) -> None:
        self.zombies : set[BaseZombie] = set()
    
    def get_count(self) -> int:
        return len(self.zombies)
    
    @staticmethod
    def combine(clusters : list['ZombieCluster']):
        new_cluster = ZombieCluster()
        for cluster in clusters:
            new_cluster.zombies = new_cluster.zombies.union([*cluster.zombies])
        return new_cluster

class BaseZombie(Sprite):
    inactive_elements : list["BaseZombie"] = []
    active_elements : list['BaseZombie'] = []

    test_image : pygame.Surface = pygame.surface.Surface((50, 50))
    test_image.set_colorkey([0, 0, 255])
    test_image.fill([0, 0, 255])
    pygame.draw.circle(test_image, "Red", (25, 25), 25)
    ui_clusters : list[TextSprite] = []
    str_type = None
    flash_image = load_alpha_to_colorkey('assets/graphics/enemy/flash_dark.png', [0, 255, 0])
    def __init__(self) -> None:
        super().__init__()
        self.dynamic_mask = True
        self.speed : float
        self.max_hp : int
        self.hp : int
        self.damage : int
        self.flash_timer : Timer
        self.flashing : bool = False
        self.og_image : pygame.Surface|None = None
        self.is_dying : bool = False
        BaseZombie.inactive_elements.append(self)
    
    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, health : int, speed : int = 3, damage : int = 1):
        element = cls.inactive_elements[0]

        element.image = cls.test_image
        #element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = new_pos
        element.align_rect()
        element.zindex = 10

        element.pivot = Pivot2D(element._position, element.image, (0, 0, 255))


        element.max_hp = health
        element.hp = health
        element.speed = speed
        element.damage = damage

        element.flashing = False
        element.flash_timer = Timer(-1, core_object.game.game_timer.get_time)
        element.og_image = None
        element.is_dying = False

        cls.unpool(element)
        return element
    
    def start_flashing(self):
        if self.flashing: self.flash_timer.restart(); return
        self.flashing = True
        self.flash_timer.set_duration(0.15)
        self.og_image = self.image
        self.image = self.flash_image
    
    def stop_flashing(self):
        if not self.flashing: return
        self.flashing = False
        self.flash_timer.set_duration(-1)
        self.image = self.og_image
        self.og_image = None
    
    def update_flash(self):
        if not self.flashing: return
        if self.flash_timer.isover():
            self.stop_flashing()
    
    def update_death_state(self):
        self.update_flash()
        if not self.flashing: self.kill_instance_safe()
    
    @classmethod
    def pool(cls, element):
        '''Transfers an element from active to inactive state. Nothing changes if the element is already inactive.'''
        if element in BaseZombie.active_elements:
            BaseZombie.active_elements.remove(element)
        
        if element in Sprite.active_elements:
            Sprite.active_elements.remove(element)
        
        if element not in BaseZombie.inactive_elements:
            BaseZombie.inactive_elements.append(element)

        if element not in Sprite.inactive_elements:
            Sprite.inactive_elements.append(element)
    
    @classmethod
    def unpool(cls, element):
        '''Transfers an element from inactive to active state. Nothing changes if the element is already active.'''
        if element not in BaseZombie.active_elements:
            BaseZombie.active_elements.append(element)
        
        if element not in Sprite.active_elements:
            Sprite.active_elements.append(element)


        if element in BaseZombie.inactive_elements:
            BaseZombie.inactive_elements.remove(element)

        if element in Sprite.inactive_elements:
            Sprite.inactive_elements.remove(element)   
    
    def update(self, delta: float):
        if not core_object.game.is_nm_state(): return
        if self.is_dying:
            self.update_death_state()
            return
        player_direction : pygame.Vector2 = (core_object.game.player.position - self.position).normalize()
        self.position += player_direction * self.speed * delta
        self.do_collisions()
        self.update_flash()
    
    def do_collisions(self):
        bullets : list[BaseProjectile] = self.get_all_colliding([BaseProjectile.active_elements])
        for bullet in bullets:
            if not isinstance(bullet, BaseProjectile):continue
            if not bullet.is_hostile(bullet.TEAMS.enemy):continue          
            if isinstance(bullet, PeirceProjectile): 
                if self in bullet.hit_memory:
                    continue
                else:
                    bullet.hit_memory.add(self)
            alive : bool = self.take_damage(bullet.damage)
            self.start_flashing()
            bullet.when_hit()
            if not alive: break
    
    @classmethod
    def update_class(cls, delta: float):
        clusters : dict[tuple[float, float], ZombieCluster] = {}
        grouped_clusters : dict[tuple[float, float], int] = {}
        for i, zombie in enumerate(BaseZombie.active_elements):
            zombie_pos = zombie.position
            result = ZombieCluster()
            result.zombies.add(zombie)
            for j, other_zombie in enumerate(BaseZombie.active_elements):
                if i >= j: continue
                if other_zombie == zombie: continue
                other_zombie_pos = other_zombie.position
                distance_squared = (zombie_pos - other_zombie_pos).magnitude_squared()
                if distance_squared <= 18 * 18:
                    result.zombies.add(other_zombie)
            if result.get_count() >= 3: clusters[(zombie_pos.x, zombie_pos.y)] = result
        
        banned_clusters : list[tuple[float, float]] = []
        for i, cluster in enumerate(clusters):
            if cluster in banned_clusters: continue
            group : list[tuple[float, float]] = [cluster]
            for j, other_cluster in enumerate(clusters):
                if i >= j: continue
                if cluster == other_cluster: continue
                if other_cluster in banned_clusters: continue
                distance_squared = (cluster[0] - other_cluster[0]) ** 2 + (cluster[1] - other_cluster[1]) ** 2
                if distance_squared < 18 * 18:
                    group.append(other_cluster)
                    banned_clusters.append(other_cluster)

            banned_clusters.append(cluster)
            grouped_clusters[tuple_vec_average(group)] = ZombieCluster.combine([clusters[pos] for pos in group]).get_count()
        cls.clear_clusters()
        for cluster in grouped_clusters:
            count : int = grouped_clusters[cluster]
            cls.create_cluster(cluster, count)
            


    @classmethod
    def clear_clusters(cls):
        for cluster in cls.ui_clusters:
            core_object.main_ui.remove(cluster)
        cls.ui_clusters.clear()
    
    @classmethod
    def create_cluster(cls, pos : tuple[float, float], count : int):
        new_sprite = TextSprite(pos, 'midbottom', 0, f'X{count}', None, None, None, 0, (core_object.game.font_50, 'White', False), 
                                ('Black', 2), colorkey=[0, 255, 0])
        core_object.main_ui.add(new_sprite)
        cls.ui_clusters.append(new_sprite)
                
    
    def take_damage(self, damage : int) -> bool:
        self.hp -= damage
        if self.hp <= 0:
            self.die()
            return False
        return True
    
    def die(self):
        self.is_dying = True
        self.start_flashing()
        core_object.game.on_enemy_death(self)
        

    def clean_instance(self):
        self.image = None
        #self.mask = None
        self.rect = None
        self.pivot = None
        self._position = pygame.Vector2(0,0)
        self.zindex = None

        self.speed = None
        self.max_hp = None
        self.hp = None
    
    @classmethod
    def class_cleanup(self):
        self.clear_clusters()

Sprite.register_class(BaseZombie)

class NormalZombie(BaseZombie):
    test_image : pygame.Surface = load_alpha_to_colorkey('assets/graphics/enemy/normal/main.png', [73, 197, 2])
    inactive_elements : list['NormalZombie'] = []
    active_elements : list['NormalZombie'] = []
    str_type = ZombieTypes.normal
    def __init__(self) -> None:
        super().__init__()
        NormalZombie.inactive_elements.append(self)
    
    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, health : int, speed : int = 3, damage : int = 1):
        element = cls.inactive_elements[0]

        element.image = cls.test_image
        #element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = new_pos
        element.align_rect()
        element.zindex = 10

        element.pivot = Pivot2D(element._position, element.image, (0, 0, 255))


        element.max_hp = health
        element.hp = health
        element.speed = speed
        element.damage = damage
        
        element.flashing = False
        element.flash_timer = Timer(-1, core_object.game.game_timer.get_time)
        element.og_image = None
        element.is_dying = False

        cls.unpool(element)
        return element
        

    @classmethod
    def pool(cls, element):
        '''Transfers an element from active to inactive state. Nothing changes if the element is already inactive.'''
        super().pool(element)
        if element in NormalZombie.active_elements:
            NormalZombie.active_elements.remove(element)
        
        if element not in NormalZombie.inactive_elements:
            NormalZombie.inactive_elements.append(element)
    
    @classmethod
    def unpool(cls, element):
        '''Transfers an element from inactive to active state. Nothing changes if the element is already active.'''
        super().unpool(element)
        if element not in NormalZombie.active_elements:
            NormalZombie.active_elements.append(element)


        if element in NormalZombie.inactive_elements:
            NormalZombie.inactive_elements.remove(element)

class QuickZombie(BaseZombie):
    inactive_elements : list['NormalZombie'] = []
    active_elements : list['NormalZombie'] = []

    test_image : pygame.Surface = load_alpha_to_colorkey('assets/graphics/enemy/quick/main.png', [73, 197, 2])
    str_type = ZombieTypes.quick
    def __init__(self) -> None:
        super().__init__()
        QuickZombie.inactive_elements.append(self)
    
    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, health : int, speed : int = 3, damage : int = 1):
        element = cls.inactive_elements[0]

        element.image = cls.test_image
        #element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = new_pos
        element.align_rect()
        element.zindex = 10

        element.pivot = Pivot2D(element._position, element.image, (0, 0, 255))


        element.max_hp = health
        element.hp = health
        element.speed = speed
        element.damage = damage
        
        element.flashing = False
        element.flash_timer = Timer(-1, core_object.game.game_timer.get_time)
        element.og_image = None
        element.is_dying = False


        cls.unpool(element)
        return element
        

    @classmethod
    def pool(cls, element):
        '''Transfers an element from active to inactive state. Nothing changes if the element is already inactive.'''
        super().pool(element)
        if element in QuickZombie.active_elements:
            QuickZombie.active_elements.remove(element)
        
        if element not in QuickZombie.inactive_elements:
            QuickZombie.inactive_elements.append(element)
    
    @classmethod
    def unpool(cls, element):
        '''Transfers an element from inactive to active state. Nothing changes if the element is already active.'''
        super().unpool(element)
        if element not in QuickZombie.active_elements:
            QuickZombie.active_elements.append(element)


        if element in QuickZombie.inactive_elements:
            QuickZombie.inactive_elements.remove(element)

class TankZombie(BaseZombie):
    inactive_elements : list['NormalZombie'] = []
    active_elements : list['NormalZombie'] = []

    test_image : pygame.Surface = load_alpha_to_colorkey('assets/graphics/enemy/tank/main.png', [73, 197, 2])
    str_type = ZombieTypes.tank
    def __init__(self) -> None:
        super().__init__()
        TankZombie.inactive_elements.append(self)
    
    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, health : int, speed : int = 3, damage : int = 1):
        element = cls.inactive_elements[0]

        element.image = cls.test_image
        #element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = new_pos
        element.align_rect()
        element.zindex = 10

        element.pivot = Pivot2D(element._position, element.image, (0, 0, 255))


        element.max_hp = health
        element.hp = health
        element.speed = speed
        element.damage = damage
        
        element.flashing = False
        element.flash_timer = Timer(-1, core_object.game.game_timer.get_time)
        element.og_image = None
        element.is_dying = False


        cls.unpool(element)
        return element
        

    @classmethod
    def pool(cls, element):
        '''Transfers an element from active to inactive state. Nothing changes if the element is already inactive.'''
        super().pool(element)
        if element in TankZombie.active_elements:
            TankZombie.active_elements.remove(element)
        
        if element not in TankZombie.inactive_elements:
            TankZombie.inactive_elements.append(element)
    
    @classmethod
    def unpool(cls, element):
        '''Transfers an element from inactive to active state. Nothing changes if the element is already active.'''
        super().unpool(element)
        if element not in TankZombie.active_elements:
            TankZombie.active_elements.append(element)


        if element in TankZombie.inactive_elements:
            TankZombie.inactive_elements.remove(element)

class RangedZombie(BaseZombie):
    test_image : pygame.Surface = load_alpha_to_colorkey('assets/graphics/enemy/ranged/main.png', [0, 255, 0])
    inactive_elements : list['RangedZombie'] = []
    active_elements : list['RangedZombie'] = []
    str_type = ZombieTypes.ranged
    def __init__(self) -> None:
        super().__init__()
        self.weapon : BaseWeapon
        self.entry_tween : TweenModule.TweenChain|None
        RangedZombie.inactive_elements.append(self)
    
    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, health : int, speed : int = 3, damage : int = 1):
        element = cls.inactive_elements[0]

        element.image = cls.test_image
        #element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = new_pos
        element.align_rect()
        element.zindex = 10

        element.pivot = Pivot2D(element._position, element.image, (0, 0, 255))


        element.max_hp = health
        element.hp = health
        element.speed = speed
        
        element.flashing = False
        element.flash_timer = Timer(-1, core_object.game.game_timer.get_time)
        element.og_image = None
        element.is_dying = False


        element.damage = damage
        element.weapon = BaseWeapon(WeaponStats(1, 1, FiringModes.auto, 5), core_object.game.game_timer.get_time)
        element.weapon.team = BaseProjectile.TEAMS.enemy
        element.weapon.ready_shot_cooldown()
        target_x : int|float = pygame.math.clamp(new_pos.x, 50, 960 - 50)
        target_y : int|float = pygame.math.clamp(new_pos.y, 50, 540 - 50)
        target_pos : pygame.Vector2 = pygame.Vector2(target_x, target_y)
        goal1 = {'position' : target_pos}
        info1 = TweenModule.TweenInfo(interpolation.quad_ease_out, 1 / speed)
        goalwait = {}
        infowait = TweenModule.TweenInfo(lambda t : t, 0.35 / speed)
        element.entry_tween = TweenModule.TweenChain(element, [(info1, goal1), (infowait, goalwait)], time_source=core_object.game.game_timer.get_time)
        element.entry_tween.play()
        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        if not core_object.game.is_nm_state(): return
        if self.is_dying:
            self.update_death_state()
            return
        self.do_collisions()
        if self._zombie: return
        if self.entry_tween:
            self.entry_tween.update()
            if self.entry_tween.has_finished:
                self.entry_tween = None
            return
        bullet = self.weapon.shoot(self.position, (core_object.game.player.position - self.position).normalize())
        if bullet: bullet.image = make_circle(4, (162, 42, 232))
        self.update_flash()
        

    @classmethod
    def pool(cls, element):
        '''Transfers an element from active to inactive state. Nothing changes if the element is already inactive.'''
        super().pool(element)
        if element in RangedZombie.active_elements:
            RangedZombie.active_elements.remove(element)
        
        if element not in RangedZombie.inactive_elements:
            RangedZombie.inactive_elements.append(element)
    
    @classmethod
    def unpool(cls, element):
        '''Transfers an element from inactive to active state. Nothing changes if the element is already active.'''
        super().unpool(element)
        if element not in RangedZombie.active_elements:
            RangedZombie.active_elements.append(element)


        if element in RangedZombie.inactive_elements:
            RangedZombie.inactive_elements.remove(element)
    
    def clean_instance(self):
        super().clean_instance()
        self.entry_tween = None
        self.weapon = None

ZombieTypes.get_dict()