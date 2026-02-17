# fragmentation.py
import math
import random
import numpy as np
from meteor import Meteor

def fragment_simple(parent: Meteor, rng=None, n=5):
    """
    Simple fragmentation: parent keeps 55% mass, rest becomes n fragments.
    Small angular spread around parent direction + slight speed jitter.
    """
    rng = rng or random.Random()

    if parent.mass <= 0:
        return []

    keep_frac = 0.55
    child_total = parent.mass * (1.0 - keep_frac)
    parent.mass *= keep_frac

    # recompute parent size
    parent.radius = max(1e-4, (3.0 * parent.mass / (4.0 * math.pi * parent.density)) ** (1.0/3.0))
    parent._recompute_area()

    weights = np.array([rng.random() for _ in range(n)], dtype=float)
    weights /= weights.sum()
    masses = (weights * child_total).tolist()

    vx0, vy0 = float(parent.vel[0]), float(parent.vel[1])
    sp0 = math.hypot(vx0, vy0) + 1e-9
    base_ang = math.atan2(vy0, vx0)

    spread = math.radians(10.0)

    frags = []
    for m in masses:
        ang = base_ang + rng.uniform(-spread, spread)
        sp = sp0 * (1.0 + rng.uniform(-0.06, 0.06))

        vx = math.cos(ang) * sp
        vy = math.sin(ang) * sp

        r = max(1e-4, (3.0 * m / (4.0 * math.pi * parent.density)) ** (1.0/3.0))

        frags.append(
            Meteor(
                position=parent.pos.copy(),
                velocity=np.array([vx, vy, 0.0], dtype=float),
                mass=float(m),
                radius=float(r),
                density=float(parent.density)
            )
        )

    return frags
