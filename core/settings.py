import json

class SettingException(BaseException):
    pass


class Settings:
    def __init__(self) -> None:
        self.info = {}
        self.default = None
    
    def set_defualt(self, new_default : dict):
        self.default = new_default

    def load(self, path : str = 'assets/data/settings.json') -> bool:
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
    
    def verify(self):
        '''Returns True if no settings are missing, else False.'''
        for key in self.default:
            if key not in self.info:
                return False
        return True
    

    def save(self, path : str = 'assets/data/settings.json'):
        with open(path, 'w') as file:
            json.dump(self.info, file)