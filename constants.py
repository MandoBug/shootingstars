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
TIME_SCALE = 1.0            # 1.0 = real-time, 0.1 = slow-mo, 10.0 = fast

# RENDERING PARAMETERS
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

# Coordinate scaling (meters per pixel)
SCALE = 200                 # (not currently used by main.py; main uses its own METERS_PER_PIXEL)

# Trail settings
MAX_TRAIL_LENGTH = 100
TRAIL_FADE = True

# Colors (RGB)
COLOR_BACKGROUND = (0, 0, 0)
COLOR_EARTH = (50, 100, 200)
COLOR_ATMOSPHERE = (100, 150, 255)
COLOR_METEOR_DEFAULT = (255, 100, 0)

# INITIAL CONDITIONS (Default meteor scenario)
INITIAL_ALTITUDE = 120000   # 120 km
INITIAL_VELOCITY = 20000    # 20 km/s
INITIAL_ANGLE = 45          # degrees from horizontal

INITIAL_VX = INITIAL_VELOCITY * np.cos(np.radians(INITIAL_ANGLE))
INITIAL_VY = -INITIAL_VELOCITY * np.sin(np.radians(INITIAL_ANGLE))

# ============================================================================
# ABLATION / "BURN UP" MODEL (simple but effective)
# ============================================================================
# A common proxy: dm/dt ∝ ρ * A * v^3
# We use a tuned coefficient to look good at typical meteor speeds.
ABLATION_COEFF = 3.5e-9     # tune up/down to burn faster/slower

# When mass drops below this, meteor is considered burned up (kg)
BURNUP_MIN_MASS = 5e-6

# When intensity exceeds this, status shows "BURNING"
BURNING_INTENSITY_THRESHOLD = 0.65
# ============================================================================
# VISUAL / VFX TUNING
# ============================================================================
GLOW_ADD_BLEND = True           # Use additive blend for bloom (looks better)
MAX_METEORS_TOTAL = 25          # parent + fragments cap

# ============================================================================
# FRAGMENTATION (simple but very effective)
# ============================================================================
# Trigger fragmentation when burning hard and losing mass quickly.
FRAG_INTENSITY_THRESHOLD = 0.88      # must be visually "hot"
FRAG_DM_FRACTION_THRESHOLD = 0.035   # mass lost this step / current mass
FRAG_MIN_MASS = 2e-4                # don't fragment tiny dust
FRAG_COUNT_MIN = 3
FRAG_COUNT_MAX = 8
FRAG_SPREAD_DEG = 12                # angular spread of fragments (degrees)
FRAG_SPEED_JITTER = 0.08            # +- 8% speed variation