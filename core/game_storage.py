from sys import platform as PLATFORM
from typing import Any
import json
from utils.helpers import to_roman
if PLATFORM == 'emscripten':
    from platform import window

ALL_WEAPONS : list[str] = ['Pistol', 'Rifle', 'Shotgun', 'Piercer']

BASE_WEAPON_STATS : dict[str, dict[str, float|str]] = {
    'Pistol' : {'Damage' : 2, 'Firerate' : 2,},
    'Rifle' : {'Damage' : 2, 'Firerate' : 2,},
    'Shotgun' : {'Damage' : 2, 'Firerate' : 2,},
    'Piercer' : {'Damage' : 2, 'Firerate' : 2,}
}

WEAPON_AVAILABLE_PERKS : dict[str, dict[str, int]] = {
    'Pistol' : {'Firerate' : 5, 'Damage' : 5},
    'Rifle' : {'Firerate' : 5, 'Damage' : 5},
    'Shotgun' : {'Firerate' : 5, 'Damage' : 5},
    'Piercer' : {'Firerate' : 5, 'Damage' : 5}
}

WEAPON_PERK_COST_TABLE : dict[str, dict[str, list[int]]] = {
    'Pistol' : {'Firerate' : [0, 5, 10, 20, 40, 50], 'Damage' : [0, 5, 10, 20, 40, 50]},
    'Rifle' : {'Firerate' : [0, 5, 10, 20, 40, 50], 'Damage' : [0, 5, 10, 20, 40, 50]},
    'Shotgun' : {'Firerate' : [0, 5, 10, 20, 40, 50], 'Damage' : [0, 5, 10, 20, 40, 50]},
    'Piercer' : {'Firerate' : [0, 5, 10, 20, 40, 50], 'Damage' : [0, 5, 10, 20, 40, 50]}
}

ALL_ARMORS : list[str] = ['Light', 'Balanced', 'Heavy', 'Adaptative']

BASE_ARMOR_STATS : dict[str, dict[str, float|str]] = {
    'Light' : {'Health' : 2, 'Resistance' : '100%', 'Regeneration Cooldown' : 2, 'Regeneration Speed' : 1},
    'Balanced' : {'Health' : 2, 'Resistance' : '100%', 'Regeneration Cooldown' : 2, 'Regeneration Speed' : 1},
    'Heavy' : {'Health' : 2, 'Resistance' : '100%', 'Regeneration Cooldown' : 2, 'Regeneration Speed' : 1},
    'Adaptative' : {'Health' : 2, 'Resistance' : '100%', 'Regeneration Cooldown' : 2, 'Regeneration Speed' : 1},
}

ARMOR_AVAILABLE_PERKS : dict[str, dict[str, int]] = {
    'Light' : {'Vitality' : 5},
    'Balanced' : {'Vitality' : 5},
    'Heavy' : {'Vitality' : 5},
    'Adaptative' : {'Vitality' : 5},
}
ARMOR_PERK_COST_TABLE : dict[str, dict[str, list[int]]] = {
    'Light' : {'Vitality' : [0, 5, 10, 20, 40, 50]},
    'Balanced' : {'Vitality' : [0, 5, 10, 20, 40, 50]},
    'Heavy' : {'Vitality' : [0, 5, 10, 20, 40, 50]},
    'Adaptative' : {'Vitality' : [0, 5, 10, 20, 40, 50]}
}




COST_TABLE : dict[str, int|dict[str,dict[str, list[int]]]] = {
    'Weapons' : {'Pistol' : 0, 'Rifle' : 50, 'Shotgun' : 50, 'Piercer' : 100},
    'Armors' : {'Light' : 30, 'Balanced' : 50, 'Heavy' : 80, 'Adaptative' : 100},
}
COST_TABLE['Weapon Perks'] = WEAPON_PERK_COST_TABLE
COST_TABLE['Armor Perks'] = ARMOR_PERK_COST_TABLE

PERK_FORMATTING_TABLE : dict[str, str] = {
    'Firerate' : 'Roman',
    'Damage' : 'Roman',
    'Sharpshooter' : 'Plus',
    'Vitality' : 'Roman',
}

PERK_TOOLTIP_TABLE : dict[str, str] = {
    'Firerate' : 'Increases firerate by 20% per stack.',
    'Damage' : 'Increases damage by 20% per stack.',
    'Vitality' : 'Increases player health by 20% per stack.',
    'Sharpshooter' : '???'
}

class GameStorage:

    @staticmethod
    def format_perk(perk_name : str, perk_level : int) -> str:
        perk_format = PERK_FORMATTING_TABLE[perk_name]
        if perk_format == 'Roman':
            return f'{perk_name} {to_roman(perk_level)}'
        elif perk_format == 'Plus':
            return f'{perk_name}' + ('+' * (perk_level - 1))
    
    @staticmethod
    def format_perk_improvement(perk_name : str, current_perk_level : int, new_perk_level : int|None = None):
        if new_perk_level is None:
            new_perk_level = current_perk_level + 1
        
        return f'{GameStorage.format_perk(perk_name, current_perk_level)} --> {GameStorage.format_perk(perk_name, new_perk_level)}'
        

    def __init__(self) -> None:
        self.ALL_WEAPONS : list[str] = ALL_WEAPONS
        self.ALL_ARMORS : list[str] = ALL_ARMORS
        self.WEAPON_AVAILABLE_PERKS : dict[str, dict[str, int]] = WEAPON_AVAILABLE_PERKS
        self.ARMOR_AVAILABLE_PERKS = ARMOR_AVAILABLE_PERKS
        self.BASE_ARMOR_STATS = BASE_ARMOR_STATS
        self.PERK_FORMATTING_TABLE : dict[str, str] = PERK_FORMATTING_TABLE
        self.PERK_TOOLTIP_TABLE = PERK_TOOLTIP_TABLE
        self.COST_TABLE : dict[str, int|dict[str, list[int]]] = COST_TABLE
        self.BASE_WEAPON_STATS = BASE_WEAPON_STATS

        self.high_score : int = 0
        self.high_wave : int = 1
        self.upgrade_tokens : int = 20

        self.owned_weapons : list[str] = ['Pistol']
        self.weapon_equipped : str = 'Pistol'
        self.current_weapon_perks : dict[str, dict[str, int]] = {
            weapon : {} for weapon in self.ALL_WEAPONS
        }
        self.current_armor_perks : dict[str, dict[str, int]] = {
            armor : {} for armor in self.ALL_ARMORS
        }

        self.owned_armors : list[str] = []
        self.armor_equipped : str|None = None
        
    def reset(self):
        self.high_score = 0
        self.high_wave = 1
        self.upgrade_tokens = 20

        self.owned_weapons = ['Pistol']
        self.weapon_equipped = 'Pistol'
        self.current_weapon_perks : dict[str, dict[str, int]] = {
            weapon : {} for weapon in self.ALL_WEAPONS
        }
        self.current_armor_perks : dict[str, dict[str, int]] = {
            armor : {} for armor in self.ALL_ARMORS
        }

        self.owned_armors = []
        self.armor_equipped = None
    
    def _load_data(self, data : dict) -> bool:
        if data is None: return False
        if not data.get('isvalid', False): return False
        if int(data.get('isvalid', 0)) < 2: return False
        self.armor_equipped = data['armor_equipped']
        self.owned_armors = data['owned_armors']
        self.weapon_equipped = data['weapon_equipped']
        self.owned_weapons = data['owned_weapons']

        self.current_weapon_perks = data['current_weapon_perks']
        self.current_armor_perks = data['current_armor_perks']

        self.high_score = data['highscore']
        self.high_wave = data['highest_wave']
        self.upgrade_tokens = data['tokens']
        return True

    def _get_save_data(self) -> dict:
        data : dict = {}
        data['armor_equipped'] = self.armor_equipped
        data['owned_armors'] = self.owned_armors
        data['weapon_equipped'] = self.weapon_equipped
        data['owned_weapons'] = self.owned_weapons

        data['current_weapon_perks'] = self.current_weapon_perks
        data['current_armor_perks'] = self.current_armor_perks

        data['highscore'] = self.high_score
        data['highest_wave'] = self.high_wave
        data['tokens'] = self.upgrade_tokens
        data['isvalid'] = 2
        
        return data
    
    def load_from_file(self, file_path : str = 'assets/data/game_info.json') -> bool:
        with open(file_path, 'r') as file:
            data : dict = json.load(file)
        
        return self._load_data(data)


    def save_to_file(self, file_path : str = 'assets/data/game_info.json'):
        data : dict = self._get_save_data()
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4, separators=(', ', ' : '))

    def load_from_web(self):

        for index in range(window.localStorage.length):
            key = window.localStorage.key(index)
            value = window.localStorage.getItem(key)
            f'{key} : {value}'

        json_string : str = window.localStorage.getItem('GameData')
        if not json_string:
            window.localStorage.setItem('GameData', r'{}')
            return self.load_from_file()
        data : dict = json.loads(json_string)
        result = self._load_data(data)
        return result

    def save_to_web(self):
        str_result = json.dumps(self._get_save_data()) 
        window.localStorage.setItem('GameData', str_result)