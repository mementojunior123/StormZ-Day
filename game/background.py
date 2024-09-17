import pygame
from core.core import core_object
from game.sprite import Sprite

class Background(Sprite):
    screen_size = core_object.main_display.get_size()
    screen_center = (screen_size[0] // 2, screen_size[1] // 2)
    active_elements : list['Background'] = []
    inactive_elements : list['Background']  = []
    areas : dict[int, pygame.Surface] = {}
    areas[0] = pygame.Surface(screen_size)
    areas[0].fill((94,129,162))
    areas[1] = pygame.Surface(screen_size)
    areas[1].fill((94,160,129))
    areas[2] = pygame.Surface(screen_size)
    areas[2].fill((255, 80, 80)) #(255, 0, 160)
    areas[3] = pygame.Surface(screen_size)
    areas[3].fill((255, 80, 80))

    def __init__(self) -> None:
        super().__init__()
        Background.inactive_elements.append(self)
    
    @classmethod
    def spawn(cls, area_num : int):
        element = cls.inactive_elements[0]

        element.image = cls.areas[area_num]
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0,0)
        element.move_rect('center', pygame.Vector2(cls.screen_center))
        element.zindex = -9999999999999

        cls.unpool(element)
        return element

    def switch_area(self, new_area):
        self.image = self.areas[new_area]
