from sys import platform as PLATFORM
from typing import Any
import json
if PLATFORM == 'emscripten':
    from platform import window
class GameStorage:
    def __init__(self) -> None:
        self.high_score : int = 0
        self.high_wave : int = 1

        self.upgrade_tokens : int = 20
        self.general_upgrades : dict[str, int] = {'Firerate' : 0, 'Damage' : 0, 'Vitality' : 0}

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
        'Armors' : {'Light' : 30, 'Balanced' : 50, 'Heavy' : 80, 'Adaptative' : 100},
        'General Upgrades' : {'Firerate' : [0, 5, 10, 20, 40, 50], 'Damage' : [0, 5, 10, 20, 40, 50], 'Vitality' : [0, 5, 10, 20, 40, 50],}
        }
    def reset(self):
        self.high_score = 0
        self.high_wave = 1

        self.upgrade_tokens = 20
        self.general_upgrades = {'Firerate' : 0, 'Damage' : 0, 'Vitality' : 0}

        self.owned_weapons = ['Pistol']
        self.weapon_equipped = 'Pistol'

        self.owned_armors = []
        self.armor_equipped = None
    
    def _load_data(self, data : dict) -> bool:
        if data is None: return False
        if not data.get('isvalid', False): return False
        self.armor_equipped = data['armor_equipped']
        self.owned_armors = data['owned_armors']
        self.weapon_equipped = data['weapon_equipped']
        self.owned_weapons = data['owned_weapons']

        self.high_score = data['highscore']
        self.high_wave = data['highest_wave']
        self.upgrade_tokens = data['tokens']
        self.general_upgrades = data['general_upgrades']
        return True

    def _get_save_data(self) -> dict:
        data : dict = {}
        data['armor_equipped'] = self.armor_equipped
        data['owned_armors'] = self.owned_armors
        data['weapon_equipped'] = self.weapon_equipped
        data['owned_weapons'] = self.owned_weapons

        data['highscore'] = self.high_score
        data['highest_wave'] = self.high_wave
        data['tokens'] = self.upgrade_tokens
        data['general_upgrades'] = self.general_upgrades
        data['isvalid'] = True
        
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
            value = self.get_web(key)
            print(f'{key} : {value}')
        json_string : str = self.get_web('GameData')
        print(json_string)
        if not json_string:
            self.set_web('GameData', r'{}')
            return self.load_from_file()
        data : dict = json.loads(json_string)
        result = self._load_data(data)
        return result

    def save_to_web(self):
        str_result = json.dumps(self._get_save_data()) 
        self.set_web('GameData', str_result)
        print(str_result)

    def get_web(self, key : str) -> str:
        window.localStorage.getItem(key)

    def set_web(self, key : str, value : str):
        str_value : str = str(value)
        window.localStorage.setItem(key, value)
        test = window.localStorage.getItem(key)
        if test != str_value:
            print(f'{test} != {str_value}')