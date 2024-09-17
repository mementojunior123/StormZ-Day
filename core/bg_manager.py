import pygame

class SoundTypes:
    music = 'Music'
    sfx = 'SFX'


class BgManager:
    def __init__(self) -> None:
        self.current : dict[pygame.mixer.Channel, TrackInfo] = {}
        self.global_volume = 1
        self.sound_types = SoundTypes

    def set_global_volume(self, new_volume):
        self.global_volume = new_volume
        for channel in self.current:
            info : TrackInfo = self.current[channel]
            channel.set_volume(self.global_volume * info.volume)

       

    def play(self, track : pygame.mixer.Sound, volume, loops = -1, maxtime = 0, fade_ms = 0, sound_type : str|None = 'Music'):
        '''Used for playing music.'''
        channel = track.play(loops, maxtime, fade_ms)
        channel.set_volume(volume * self.global_volume)
        self.current[channel] = TrackInfo(volume, sound_type)
        return channel
    
    def play_sfx(self, sfx : pygame.mixer.Sound, volume, loops = 0, maxtime = 0, fade_ms = 0, sound_type : str|None = 'SFX'):
        '''Used for playing short sound effects.'''
        channel = sfx.play(loops, maxtime, fade_ms)
        channel.set_volume(volume * self.global_volume)
        self.current[channel] = TrackInfo(volume, sound_type)
        return channel
        


    def stop_channel(self, channel : pygame.mixer.Channel):
        '''Stop a currently playing channel.'''
        channel.stop()
        if channel in self.current:
            self.current.pop(channel)
    
    def stop_track(self, track : pygame.mixer.Sound):
        '''Stop a currently playing track.'''
        to_remove : list[pygame.mixer.Channel] = []
        for channel in self.current:
            if channel.get_sound() == track:
                to_remove.append(channel)
        
        for channel in to_remove:
            self.current.pop(channel)
        
        track.stop()
    
    def stop_all_type(self, type : str):
        'Stop all sounds of a specific type.'
        to_remove : list[pygame.mixer.Channel] = []
        for channel in self.current:
            info = self.current[channel]
            if info.type == type:
                to_remove.append(channel)
        
        for channel in to_remove:
            self.stop_channel(channel)
    
    def stop_all_music(self):
        '''Stop all sounds of type "Music".
        Equivalent to stop_all_type("Music").'''
        self.stop_all_type(self.sound_types.music)

    def stop_all(self):
        """Stops all currently playing sounds."""
        for channel in self.current:
            channel.stop()
        self.current.clear()
            

    def update(self):
        to_remove : list[pygame.mixer.Channel] = []
        for channel in self.current:
            if channel.get_busy() == False:
                to_remove.append(channel)
        for channel in to_remove:
            self.current.pop(channel)   


class TrackInfo:
    def __init__(self, volume : float, sound_type : str|None = None) -> None:
        self.volume : float = volume
        self.type : str|None = sound_type