"""
Meteor class representing a meteoroid entering Earth's atmosphere.
Tracks position, velocity, physical properties, trail history, and ablation burn-up.
"""

import numpy as np
import math

from constants import (
    DEFAULT_METEOR_MASS, DEFAULT_METEOR_RADIUS, DEFAULT_METEOR_DENSITY,
    MAX_TRAIL_LENGTH, ABLATION_COEFF, BURNUP_MIN_MASS
)


class Meteor:
    COLOR_LEGEND_STOPS = [
        (0,    (255, 100, 0)),
        (1000, (255, 100, 0)),
        (3000, (255, 255, 255)),
        (6000, (200, 200, 255)),
    ]

    def __init__(self, position, velocity, mass=None, radius=None, density=None):
        self.pos = np.array(position, dtype=float)
        self.vel = np.array(velocity, dtype=float)

        self.density = float(density if density is not None else DEFAULT_METEOR_DENSITY)

        self.mass = float(mass if mass is not None else DEFAULT_METEOR_MASS)
        self.initial_mass = float(self.mass)

        self.radius = float(radius if radius is not None else DEFAULT_METEOR_RADIUS)
        self._recompute_area()

        self.alive = True
        self.fragmented = False  # <-- used to avoid repeated fragmentation
        self.trail = []

    def _recompute_area(self):
        self.area = math.pi * self.radius**2

    def get_altitude(self):
        # 2D model: altitude is y
        return float(self.pos[1])

    def get_speed(self):
        return float(np.linalg.norm(self.vel))

    def get_temperature(self):
        v_km_s = self.get_speed() / 1000.0
        return 10.0 * (v_km_s ** 2)

    def get_color(self):
        temp = self.get_temperature()
        if temp < 1000:
            return (255, 100, 0)
        elif temp < 3000:
            brightness = min(255, int(temp / 3000.0 * 255))
            return (255, 255, brightness)
        else:
            blue = min(255, int(200 + (temp - 3000.0) / 10000.0 * 55))
            return (200, 200, blue)

    @classmethod
    def get_color_legend_stops(cls):
        return cls.COLOR_LEGEND_STOPS

    def update_trail(self, max_length=MAX_TRAIL_LENGTH):
        self.trail.append(self.pos.copy())
        if len(self.trail) > max_length:
            self.trail.pop(0)

    def update_ablation(self, rho_air: float, dt: float) -> float:
        """
        dm/dt = -k * A * rho * v^3

        Returns:
            dm (kg) mass lost during this dt (>=0)
        """
        if not self.alive:
            return 0.0

        v = self.get_speed()
        if v < 1.0:
            return 0.0

        dm = ABLATION_COEFF * self.area * rho_air * (v ** 3) * dt
        dm = max(0.0, float(dm))

        self.mass = max(0.0, self.mass - dm)

        if self.mass <= BURNUP_MIN_MASS:
            self.mass = 0.0
            self.alive = False
            return dm

        # Shrink radius with constant density
        r = (3.0 * self.mass / (4.0 * math.pi * self.density)) ** (1.0 / 3.0)
        self.radius = max(1e-4, float(r))
        self._recompute_area()

        return dm
