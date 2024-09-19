import json
from sys import platform as PLATFORM
from typing import Any
if PLATFORM == 'emscripten':
    from platform import window
class SettingException(BaseException):
    pass


class Settings:
    def __init__(self) -> None:
        self.info = {}
        self.default = {'Brightness' : 0, "ControlMethod" : None}
    
    def set_defualt(self, new_default : dict):
        self.default = new_default

    def load(self, path : str = 'assets/data/settings.json'):
        '''Loads the settings from the specified path and fills in any missing settings with default.'''
        if self.default is None:
            raise SettingException('Default was not set')
        with open(path, 'r') as file:
            data : dict = json.load(file)
        for key in self.default:
            if key not in data:
                self.info[key] = self.default[key]
            else:
                self.info[key] = data[key]
        for key in data:
            if key not in self.info:
                self.info[key] = data[key]
    
    def load_default(self):
        '''Resets the settings by loading the default settings.'''
        if self.default is None:
            raise SettingException('Default was not set')
        self.info = self.default.copy()
    
    def reset(self):
        self.load_default()
    
    def verify(self) -> bool:
        '''Returns True if no settings are missing, else False.'''
        for key in self.default:
            if key not in self.info:
                return False
        return True
    

    def save(self, path : str = 'assets/data/settings.json'):
        with open(path, 'w') as file:
            json.dump(self.info, file, indent=4, separators=(', ', ' : '))
    
    def save_web(self):
        str_result = json.dumps(self.info)
        window.localStorage.setItem('Settings', str_result)
    
    def load_web(self):
        if self.default is None:
            raise SettingException('Default was not set')
        json_string : str = window.localStorage.getItem('Settings')
        if not json_string: return self.load()
        data : dict = json.loads(json_string)
        for key in self.default:
            if key not in data:
                self.info[key] = self.default[key]
            else:
                self.info[key] = data[key]
        for key in data:
            if key not in self.info:
                self.info[key] = data[key]