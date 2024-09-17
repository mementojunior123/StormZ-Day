import pygame
from game.sprite import Sprite
from core.core import core_object

from utils.animation import Animation
from utils.pivot_2d import Pivot2D


class TestPlayer(Sprite):
    IMAGE_SIZE : tuple[int, int]|list[int] = (20, 60)
    test_anim : Animation = Animation.get_animation("test")
    active_elements : list['TestPlayer'] = []
    inactive_elements : list['TestPlayer'] = []
    #load assets
    test_image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
    pygame.draw.rect(test_image, "Red", (0,0, *IMAGE_SIZE))

    colors : list[str] = ["Red", "Green", "Blue", "Yellow", "Orange", "Purple", "Black", "White"]
    surface_list : list[pygame.Surface] = []
    surfaces : dict[str, pygame.Surface] = {}
    for color in colors:
        image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
        pygame.draw.rect(image, color, (0,0, *IMAGE_SIZE))
        surfaces[color] = image
        surface_list.append(image)

    def __init__(self) -> None:
        super().__init__()
        self.color_images : dict[str, pygame.Surface]
        self.color_image_list : list[pygame.Surface]
        TestPlayer.inactive_elements.append(self)

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2):
        element = cls.inactive_elements[0]

        element.image = cls.test_image
        element.color_images = cls.surfaces
        element.color_image_list = cls.surface_list
        element.rect = element.image.get_rect()

        element.position = new_pos
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(-0, 30)
        track = cls.test_anim.load(element, core_object.game.game_timer.get_time)
        track.play()
        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 5
        if keyboard_map[pygame.K_a]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_d]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_s]:
            move_vector += pygame.Vector2(0, 1)
        if keyboard_map[pygame.K_w]:
            move_vector += pygame.Vector2(0, -1)
        if keyboard_map[pygame.K_e]:
            self.angle += 5 * delta
        if keyboard_map[pygame.K_q]:
            self.angle -= 5 * delta
        if move_vector.magnitude(): move_vector.normalize()
        self.position += move_vector * speed * delta
        self.clamp_rect(pygame.Rect(0,0, *core_object.main_display.get_size()))
    
    def clean_instance(self):
        super().clean_instance()
        self.color_images = None
        self.color_image_list = None

Sprite.register_class(TestPlayer)