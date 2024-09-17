import pygame
from utils.ui.ui_sprite import UiSprite
from utils.ui.base_ui_elements import BaseUiElements
from utils.my_timer import Timer
from typing import Callable

class Ui:
    def __init__(self, elements : list[UiSprite] = None) -> None:
        if elements is None: elements = []
        self.elements : list[UiSprite] = elements
        self.temp_elements : dict[UiSprite, Timer] = {}
        self.complete_list : list[UiSprite] = []
    
    def get_sprite(self, name : str|None = None, tag : int|None = None) -> UiSprite|None:
        for element in self.complete_list:
            if name is not None:
                if element.name == name:
                    return element
            if tag is not None:
                if element.tag == tag:
                    return element
    
    def get_sprites(self, name : str|None = None, tag : int|None = None) -> list[UiSprite]:
        return_list = []
        for element in self.complete_list:
            if name is not None:
                if element.name == name:
                    return_list.append(element)
            if tag is not None:
                if element.tag == tag:
                    if element not in return_list: return_list.append(element)
        
        return return_list

    def render(self, display : pygame.Surface):
        
        self.complete_list.sort(key = lambda ui_sprite : ui_sprite.zindex)
        for element in self.complete_list:
            element.draw(display)
        #print(self.complete_list, self.elements, self.temp_elements)
    
    def add(self, element : UiSprite, duplicate = False):
        if element not in self.elements or duplicate == True:
            self.elements.append(element)
            self.complete_list.append(element)
    
    def add_multiple(self, elements : list[UiSprite], duplicate = False):
        for element in elements:
            self.add(element, duplicate=duplicate)

    def remove(self, element : UiSprite, remove_all_instances = False):
        if remove_all_instances == False:
            if element in self.elements: 
                self.elements.remove(element)
                if element in self.temp_elements: self.temp_elements.pop(element)
                if element in self.complete_list: self.complete_list.remove(element)
        else:
            to_del = []
            for sprite in self.elements:
                if sprite == element: to_del.append(element)
            for item in to_del:
                self.elements.remove(item)
                if item in self.temp_elements: self.temp_elements.pop(item)
                if element in self.complete_list: self.complete_list.remove(item)
    
    def clear_all(self):
        self.elements.clear()
        self.temp_elements.clear()
        self.complete_list.clear()
    
    def add_temp(self, element : UiSprite, time : float|Timer, override = False, time_source : Callable[[], float]|None = None, time_scale : float = 1):
        if element not in self.temp_elements or override == True:
            timer = time if type(time) == Timer else Timer(time, time_source, time_scale)
            self.temp_elements[element] = timer
            self.complete_list.append(element)
    
    def update(self):
        to_del = []
        for item in self.temp_elements:
            if self.temp_elements[item].isover(): to_del.append(item)
        for item in to_del:
            self.temp_elements.pop(item)
            if item in self.complete_list: self.complete_list.remove(item)

    
    