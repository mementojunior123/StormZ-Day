from sys import platform as PLATFORM
from typing import Any
if PLATFORM == 'emscripten':
    from platform import window

class GameStorage:
    def __init__(self) -> None:
        self.high_score : int = 0
        self.high_wave : int = 1

        self.upgrade_tokens : int = 20
        self.firerate_level : int = 0
        self.damage_level : int = 0
        self.vitality_level : int = 0

        self.owned_weapons : list[str] = ['Pistol']
        self.weapon_equipped : str = 'Pistol'
        self.ALL_WEAPONS : list[str] = ['Pistol', 'Rifle', 'Shotgun', 'Piercer']

        self.owned_armors : list[str] = []
        self.armor_equipped : str|None = None
        self.ALL_ARMORS : list[str] = ['Light', 'Balanced', 'Heavy', 'Adaptative']

        self.COST_TABLE : dict[str, list[int]|dict[str, int]] = {
        'Firerate' : [0, 5, 10, 20, 40, 50], 
        'Damage' : [0, 5, 10, 20, 40, 50], 
        'Vitality' : [0, 5, 10, 20, 40, 50], 
        'Weapons' : {'Pistol' : 0, 'Rifle' : 50, 'Shotgun' : 50, 'Piercer' : 100},
        'Armors' : {'Light' : 30, 'Balanced' : 50, 'Heavy' : 80, 'Adaptative' : 100}
        }                                          
    
    def load_from_file(self, file_path : str = 'assets/data/game_info.json'):
        pass

    def save_to_file(self, file_path : str = 'assets/data/game_info.json'):
        pass

    def load_from_web(self):
        self.high_score = int(self.get_web('high_score') or 0)
        self.upgrade_tokens = int(self.get_web('upgrade_tokens') or 3)
        self.firerate_level = int(self.get_web('firerate_level') or 1)
        self.damage_level = int(self.get_web('damage_level') or 1)

    def save_to_web(self):
        self.set_web('high_score', self.high_score)
        self.set_web('upgrade_tokens', self.upgrade_tokens)
        self.set_web('firerate_level', self.firerate_level)
        self.set_web('damage_level', self.damage_level)

    def get_web(self, key : str) -> str:
        window.localStorage.getItem(key)

    def set_web(self, key : str, value : Any):
        window.localStorage.setItem(key, str(value) )