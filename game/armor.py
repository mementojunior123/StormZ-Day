import pygame
from pygame.math import clamp
from core.core import core_object
from utils.my_timer import Timer
from typing import Callable
from dataclasses import dataclass
import dataclasses

class BaseArmor:
    def __init__(self, stats : 'ArmorStats', speed_penalty : float = 1, does_healthgate : bool = False, 
                 time_source : Callable[[], float]|None = None, name : str|None = None) -> None:
        self.stats : ArmorStats = stats
        self.unique_name : str|None = name
        self.regen_cooldown : Timer = Timer(self.stats.regen_cooldown, time_source)
        self.healthgate : bool = does_healthgate
        self.speed_pen : float = speed_penalty
    
    def get_game_source(self):
        self.regen_cooldown.time_source = core_object.game.game_timer.get_time

    def update(self, delta : float):
        if self.regen_cooldown.isover():
            self.stats.health += (self.stats.base_regen_speed / 60) * delta
            if self.stats.health > self.stats.max_health:
                self.stats.health = self.stats.max_health

    def take_damage(self, damge : float):
        if damge <= 0: return 0
        self.regen_cooldown.set_duration(self.stats.regen_cooldown)
        if self.stats.health <= 0: return damge
        resistance : float = clamp(self.stats.resistance, 0, 1)
        absorbed : float = damge * resistance
        leftover : float = damge - absorbed
        if self.stats.health >= absorbed:
            self.stats.health -= absorbed
            return leftover
        elif self.healthgate:
            self.stats.health = 0
            return leftover    
        else:
            leftover += (absorbed - self.stats.health)
            self.stats.health = 0
            return leftover
    
    def refill(self):
        self.stats.health = self.stats.max_health
        

class ArmorStats:
    def __init__(self, resistance : float, max_hp : int, regen_speed : float, regen_cooldown : float) -> None:
        self.base_resistance : float = resistance
        self.base_max_health : int = max_hp
        self.base_regen_speed : float = regen_speed
        self.base_regen_cooldown : float = regen_cooldown

        self.resistance_mult : float = 1
        self.resistance_bonus : float = 0

        self.max_health_mult : float = 1
        self.max_health_bonus : float = 0

        self.regen_speed_mult : float = 1
        self.regen_speed_bonus : float = 0

        self.regen_cooldown_mult : float = 1
        self.regen_cooldown_bonus : float = 0

        self.buffs : list['ArmorBuff'] = []
        self.perma_buffs : list['ArmorBuff'] = []
        self.health : int = self.max_health

    @property
    def resistance(self):
        return (self.base_resistance * self.resistance_mult) + self.resistance_bonus
    
    @property
    def max_health(self):
        return (self.base_max_health * self.max_health_mult) + self.max_health_bonus
    
    @property
    def regen_speed(self):
        return (self.base_regen_speed * self.regen_speed_mult) + self.regen_speed_bonus
    
    @property
    def regen_cooldown(self):
        val = (self.base_regen_cooldown / self.regen_cooldown_mult) - self.regen_cooldown_bonus
        return val if val > 0 else 0
    

    def reset(self):
        self.clear_buffs()
        self.perma_buffs.clear()

        self.resistance_mult = 1
        self.resistance_bonus = 0

        self.max_health_mult = 1
        self.max_health_bonus = 0

        self.regen_speed_mult = 1
        self.regen_speed_bonus = 0

        self.regen_cooldown_mult = 1
        self.regen_cooldown_bonus = 0

        self.health = self.base_max_health
        
    
    def apply_buff(self, new_buff : 'ArmorBuff'):
        new_buff.apply(self)
    
    def apply_perma_buff(self, new_buff : 'ArmorBuff'):
        new_buff.apply(self, do_append=False)
        self.perma_buffs.append(new_buff)
    
    def update_buffs(self):
        to_del : list[ArmorBuff] = []
        for buff in self.buffs:
            if buff.timer.isover():
                to_del.append(buff)
        for buff in to_del:
            buff.remove(self)

    def clear_buffs(self):
        while self.buffs:
            self.buffs[0].remove(self)

class ArmorBuffTypes:
    resistance_mult = 'resistance_mult'
    resistance_bonus = 'resistance_bonus'
    max_health_mult = 'max_health_mult'
    max_health_bonus = 'max_health_bonus'
    regen_speed_mult = 'regen_speed_mult'
    regen_speed_bonus = 'regen_speed_bonus'
    regen_cooldown_mult = 'regen_cooldown_mult'
    regen_cooldown_bonus = 'regen_cooldown_bonus'

class ArmorBuff:
    @staticmethod
    def new(buff_type : str, value : float, time : float = -1):
        ABF = ArmorBuffTypes
        conversion_dict : dict[str, ArmorBuff] = {
            ABF.resistance_mult : ResistanceMult,
            ABF.resistance_bonus : ResistanceBonus,
            ABF.max_health_mult : MaxHealthMult,
            ABF.max_health_bonus : MaxHealthBonus,
            ABF.regen_cooldown_bonus : RegenCooldownBonus,
            ABF.regen_cooldown_mult : RegenCooldownMult,
            ABF.regen_speed_bonus : RegenSpeedBonus,
            ABF.regen_speed_mult : RegenSpeedMult
        }
        if buff_type not in conversion_dict:
            return ArmorBuff(buff_type, value, time)
        else:
            return conversion_dict[buff_type](buff_type, value, time)
        
    def __init__(self, buff_type : str, value : float, time : float = -1) -> None:
        self.type : str = buff_type
        self.value : float = value
        self.timer : Timer = Timer(time, time_source=core_object.game.game_timer.get_time)

    def apply(self, armor : ArmorStats, do_append : bool = True):
        if do_append: armor.buffs.append(self)
        pass

    def remove(self, armor : ArmorStats, do_remove : bool = True):
        if self not in armor.buffs: return
        if do_remove: armor.buffs.remove(self)
        pass


class ResistanceBonus(ArmorBuff):
    def apply(self, armor: ArmorStats, do_append: bool = True):
        if do_append: armor.buffs.append(self)
        armor.resistance_bonus += self.value
    
    def remove(self, armor: ArmorStats, do_remove: bool = True):
        if self not in armor.buffs: return
        if do_remove: armor.buffs.remove(self)
        armor.resistance_bonus -= self.value

class ResistanceMult(ArmorBuff):
    def apply(self, armor: ArmorStats, do_append: bool = True):
        if do_append: armor.buffs.append(self)
        armor.resistance_mult += self.value
    
    def remove(self, armor: ArmorStats, do_remove: bool = True):
        if self not in armor.buffs: return
        if do_remove: armor.buffs.remove(self)
        armor.resistance_mult -= self.value


class MaxHealthBonus(ArmorBuff):
    def apply(self, armor: ArmorStats, do_append: bool = True):
        if do_append: armor.buffs.append(self)
        armor.max_health_bonus += self.value
    
    def remove(self, armor: ArmorStats, do_remove: bool = True):
        if self not in armor.buffs: return
        if do_remove: armor.buffs.remove(self)
        armor.max_health_bonus -= self.value

class MaxHealthMult(ArmorBuff):
    def apply(self, armor: ArmorStats, do_append: bool = True):
        if do_append: armor.buffs.append(self)
        armor.max_health_mult += self.value
    
    def remove(self, armor: ArmorStats, do_remove: bool = True):
        if self not in armor.buffs: return
        if do_remove: armor.buffs.remove(self)
        armor.max_health_mult -= self.value


class RegenSpeedBonus(ArmorBuff):
    def apply(self, armor: ArmorStats, do_append: bool = True):
        if do_append: armor.buffs.append(self)
        armor.regen_speed_bonus += self.value
    
    def remove(self, armor: ArmorStats, do_remove: bool = True):
        if self not in armor.buffs: return
        if do_remove: armor.buffs.remove(self)
        armor.regen_speed_bonus -= self.value

class RegenSpeedMult(ArmorBuff):
    def apply(self, armor: ArmorStats, do_append: bool = True):
        if do_append: armor.buffs.append(self)
        armor.regen_speed_mult += self.value
    
    def remove(self, armor: ArmorStats, do_remove: bool = True):
        if self not in armor.buffs: return
        if do_remove: armor.buffs.remove(self)
        armor.regen_speed_mult -= self.value


class RegenCooldownBonus(ArmorBuff):
    def apply(self, armor: ArmorStats, do_append: bool = True):
        if do_append: armor.buffs.append(self)
        armor.regen_cooldown_bonus += self.value
    
    def remove(self, armor: ArmorStats, do_remove: bool = True):
        if self not in armor.buffs: return
        if do_remove: armor.buffs.remove(self)
        armor.regen_cooldown_bonus -= self.value

class RegenCooldownMult(ArmorBuff):
    def apply(self, armor: ArmorStats, do_append: bool = True):
        if do_append: armor.buffs.append(self)
        armor.regen_cooldown_mult += self.value
    
    def remove(self, armor: ArmorStats, do_remove: bool = True):
        if self not in armor.buffs: return
        if do_remove: armor.buffs.remove(self)
        armor.regen_cooldown_mult -= self.value

ARMORS : dict[str, BaseArmor] = {
    None : None,
    'Light' : BaseArmor(ArmorStats(0.6, 2, (2 / 2), 2), (7/7)),
    'Balanced' : BaseArmor(ArmorStats(0.75, 5, (5/4), 3), (6/7)),
    'Heavy' : BaseArmor(ArmorStats(0.9, 8, (6/8), 5), (5/7), True),
    'Adaptative' : BaseArmor(ArmorStats(1, 2, (2 / 4), 2), (7/7), True)

}