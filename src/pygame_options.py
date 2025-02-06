import pygame

pygame.init()

# Recovering screen dimensions
user_screen_info = pygame.display.Info()
USER_SCREEN_WIDTH = user_screen_info.current_w
USER_SCREEN_HEIGHT = user_screen_info.current_h

# Setting Pygame window dimensions
scale = 1.5
WIDTH, HEIGHT = USER_SCREEN_WIDTH // scale, USER_SCREEN_HEIGHT // scale
screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Survivors sim")
FPS = 30