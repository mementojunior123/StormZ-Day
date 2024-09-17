import pygame
from sys import exit

class EventManger:
    def __init__(self) -> None:
        self.bound_actions : dict[int, list['function']] = {pygame.QUIT : [self.close_game]}
    
    def close_game(self, event):
        pygame.quit()
        exit()
    
    def bind(self, event_type : int, actions : list['function'], duplicate = False):
        '''The action parameter must be a function or list of functions that accepts exactly one pygame.Event argument. 
        Returns False if the action fails to bind.'''
        try:
            actions[0]
        except TypeError:
            actions = [actions]

        if event_type == pygame.QUIT:
            return False
        
        if (event_type in self.bound_actions):
            for action in actions:
                if action not in self.bound_actions[event_type] or duplicate is True:
                    self.bound_actions[event_type].append(action)
        else:
            self.bound_actions[event_type] = actions
        
        return True

    def unbind(self, event_type : int, target_actions : list['function']):
        '''Returns False if event_type or target_actions is not found.'''
        try:
            target_actions[0]
        except TypeError:
            target_actions = [target_actions]

        if event_type == pygame.QUIT:
            return False

        if event_type not in self.bound_actions:
            return False
        
        for action in target_actions:
            if action in self.bound_actions[event_type]:
                self.bound_actions[event_type].remove(action)
                
        return True
    
    def unbind_all(self, event_type : int):
        if event_type == pygame.QUIT:
            return False

        if event_type not in self.bound_actions:
            return False
        
        self.bound_actions.pop(event_type)
        return True
    
    def process_event(self, event : pygame.Event):
        if event.type in self.bound_actions:
            for callback in self.bound_actions[event.type]:
                callback(event)
