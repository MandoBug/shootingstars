import numpy as np

"""
Physical constants and simulation parameters for meteor simulation.
All values in SI units (meters, kilograms, seconds).
"""

# Gravitational constant (N⋅m²/kg²)
G = 6.674e-11

# Earth properties
M_EARTH = 5.972e24          # Earth mass (kg)
R_EARTH = 6.371e6           # Earth radius (m)
g = 9.81                    # Surface gravity (m/s²)

# Atmospheric properties
RHO_0 = 1.225               # Sea level air density (kg/m³)
H_SCALE = 8500              # Atmospheric scale height (m)
                            # Density drops by factor of e every H_SCALE meters
                            
# METEOR DEFAULT PROPERTIES

DEFAULT_METEOR_MASS = 0.01          # Default mass (kg) - 10 grams
DEFAULT_METEOR_RADIUS = 0.02        # Default radius (m) - 2 cm
DEFAULT_METEOR_DENSITY = 3000       # Default density (kg/m³) - stone
DRAG_COEFFICIENT = 0.8              # Drag coefficient (dimensionless)
                                    # ~0.5 for smooth sphere, ~1.0 for irregular

# SIMULATION PARAMETERS

FPS = 60                    # Frames per second for rendering
DT = 0.01                   # Timestep for physics (seconds)
                            # Smaller = more accurate but slower
                            # 0.01s is good balance for RK4

# Time scaling (for visualization)
TIME_SCALE = 1.0            # 1.0 = real-time, 0.1 = slow-mo, 10.0 = fast


# RENDERING PARAMETERS
SCREEN_WIDTH = 1200         # Window width (pixels)
SCREEN_HEIGHT = 800         # Window height (pixels)

# Coordinate scaling (meters per pixel)
SCALE = 1000                # 1 pixel = 1000 meters (1 km)
                            # Adjust this to zoom in/out

# Trail settings
MAX_TRAIL_LENGTH = 100      # Number of points in trail
TRAIL_FADE = True           # Should trail fade out?

# Colors (RGB)
COLOR_BACKGROUND = (0, 0, 0)        # Black
COLOR_EARTH = (50, 100, 200)        # Blue
COLOR_ATMOSPHERE = (100, 150, 255)  # Light blue
COLOR_METEOR_DEFAULT = (255, 100, 0) # Orange

# INITIAL CONDITIONS (Default meteor scenario)
# Starting altitude (m)
INITIAL_ALTITUDE = 120000   # 120 km - typical meteor entry altitude

# Starting velocity (m/s)
INITIAL_VELOCITY = 20000    # 20 km/s - typical meteor speed

# Entry angle (degrees from horizontal)
INITIAL_ANGLE = 45          # 45 degrees - steep entry

# Convert angle to velocity components
INITIAL_VX = INITIAL_VELOCITY * np.cos(np.radians(INITIAL_ANGLE))
INITIAL_VY = -INITIAL_VELOCITY * np.sin(np.radians(INITIAL_ANGLE))  # Negative = downward