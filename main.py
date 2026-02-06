import pygame
import sys
import numpy as np
from meteor import Meteor

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Meteor Simulation - 2D")
clock = pygame.time.Clock()
FPS = 60
DT = 1 / FPS
g = 9.81  # Gravity

# Create a meteor
meteor = Meteor([WIDTH//2, 100], [50, 0])  # initial x velocity 50 px/sec

def physics_to_screen(pos):
    x, y = pos
    return int(x), int(HEIGHT - y)

running = True
while running and meteor.alive:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Physics: update velocity and position
    meteor.vel[1] -= g * DT # Gravity acts downward
    meteor.pos += meteor.vel * DT
    
    # Check if meteor hits the ground
    if meteor.pos[1] <= 0:
        meteor.alive = False
    
    # Drawing
    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (255, 100, 0), physics_to_screen(meteor.pos), 5)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
