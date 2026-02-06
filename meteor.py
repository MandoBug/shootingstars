#import pygame
import numpy as np
#import matplotlib.pyplot as plt
#import sys

'''
rho0 = 1.225  # kg/m³, sea-level density
H = 8500      # m, scale height
Cd = 0.8      # drag coefficient

# Scale factor: meters to pixels
SCALE = 500  # 1 pixel = 500 m

'''

class Meteor:
    def __init__(self, position, velocity, mass=0.01, radius=0.02):
        self.pos = np.array(position, dtype=float) # [x, y], in meters
        self.vel = np.array(velocity, dtype=float) # [v_x, v_y], in meters/sec
        self.mass = mass
        self.radius = radius
        # self.area = np.pi * (radius/SCALE)**2 # cross-section in m²
        # self.trail = []
        self.alive = True

'''

    def get_speed(self):
        return np.linalg.norm(self.vel)
        
    def update_trail(self, max_length=50):
        self.trail.append(self.pos.copy())
        if len(self.trail) > max_length:
            self.trail.pop(0)
            
            
# Atmosphere functions
def air_density(y):
    """Exponential decay with altitude"""
    if y < 0:
        return rho0
    return rho0 * np.exp(-y / H)

def drag_force(meteor):
    v = meteor.vel
    speed = np.linalg.norm(v)
    if speed < 1e-6:
        return np.array([0.0, 0.0])
    f_mag = 0.5 * air_density(meteor.pos[1]) * speed**2 * Cd * meteor.area
    return -f_mag * (v / speed)


# Pygame setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Meteor Simulation with Drag")
clock = pygame.time.Clock()

def physics_to_screen(pos):
    """Convert physics coords (meters) to screen coords (pixels)"""
    x = WIDTH / 2 + pos[0] / SCALE
    y = HEIGHT - pos[1] / SCALE
    return int(x), int(y)

# Create meteor
initial_pos = np.array([0.0, 100_000]) # 100 km altitude
initial_vel = np.array([20_000, -5_000]) # 20 km/s horizontal, -5 km/s downward
meteor = Meteor(initial_pos, initial_vel)


# Main loop
running = True
while running and meteor.alive:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Physics update
    F_drag = drag_force(meteor)
    F_grav = np.array([0, -meteor.mass * g])
    a = (F_grav + F_drag) / meteor.mass
    meteor.vel += a * DT
    meteor.pos += meteor.vel * DT
    meteor.update_trail()

    # Stop if meteor hits ground
    if meteor.pos[1] <= 0:
        meteor.alive = False
        
    # Drawing
    screen.fill((0, 0, 0))

    # Draw trail
    for i, pos in enumerate(meteor.trail):
        alpha = int(255 * (i / len(meteor.trail)))
        color = (alpha, alpha//2, 0)  # orange fading
        pygame.draw.circle(screen, color, physics_to_screen(pos), 2)

    # Draw meteor
    pygame.draw.circle(screen, (255, 150, 0), physics_to_screen(meteor.pos), meteor.radius)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
'''

