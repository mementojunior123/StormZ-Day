import pygame

green_button_surf = pygame.image.load("assets/graphics/button_templates/green_button.png").convert_alpha()
blue_button_surf = pygame.image.load("assets/graphics/button_templates/blue_button.png").convert_alpha()
red_button_surf = pygame.image.load("assets/graphics/button_templates/red_button.png").convert_alpha()

left_button_surf = pygame.image.load("assets/graphics/button_templates/left_button.png").convert_alpha()
right_button_surf = pygame.image.load("assets/graphics/button_templates/right_button.png").convert_alpha()

hover_icon_surf = pygame.image.load("assets/graphics/button_templates/hover_icon.png").convert_alpha()
hover_icon_clean_surf = pygame.image.load("assets/graphics/button_templates/hover_icon_clean.png").convert_alpha()
hover_icon_blue_surf = pygame.image.load("assets/graphics/button_templates/hover_icon_blue.png").convert_alpha()
home_icon_surf = pygame.image.load("assets/graphics/button_templates/home_icon.png").convert_alpha()

back_icon_surf = pygame.image.load("assets/graphics/button_templates/back_icon_green_colorkey.png").convert()
back_icon_surf.set_colorkey((0, 255, 0))
left_arrow_surf = pygame.image.load("assets/graphics/button_templates/left_arrow.png").convert_alpha()
right_arrow_surf = pygame.image.load("assets/graphics/button_templates/right_arrow.png").convert_alpha()

image_dict : dict[str, pygame.Surface] = {
"GreenButton": green_button_surf,
"BlueButton": blue_button_surf,
"RedButton": red_button_surf,
"Left" : left_button_surf,
"Right" : right_button_surf,
"Pointer": hover_icon_surf,
"CleanPointer": hover_icon_clean_surf,
"BluePointer": hover_icon_blue_surf,
"Home" : home_icon_surf,
"LeftArrow" : left_arrow_surf,
"RightArrow" : right_arrow_surf,
"BackIcon" : back_icon_surf,
}