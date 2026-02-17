# vfx.py
import math
import random
from dataclasses import dataclass
from typing import Dict, Tuple, List
import pygame

def clamp(x, a, b):
    return a if x < a else b if x > b else x

def lerp(a, b, t):
    return a + (b - a) * t

@dataclass
class Spark:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: Tuple[int, int, int]

class MeteorVFX:
    """
    Simple, stable VFX:
    - streak aligned with velocity
    - one soft bloom + core
    - optional sparks (still simple)
    """

    def __init__(self):
        self._glow_cache: Dict[Tuple[int, Tuple[int, int, int], int], pygame.Surface] = {}
        self.sparks: List[Spark] = []
        self.max_sparks = 450
        self.spark_air_drag = 0.92
        self.spark_gravity = 120.0

    # Heating proxy + intensity mapping
    def heating_proxy(self, rho: float, speed_m_s: float) -> float:
        return rho * (speed_m_s ** 3)

    def intensity_from_heating(self, heating: float) -> float:
        # Smooth saturating mapping -> 0..1
        k = 2.2e-7
        x = heating * k
        return clamp(x / (1.0 + x), 0.0, 1.0)

    def _get_glow_surface(self, radius_px: int, color: Tuple[int, int, int], alpha_scale: int) -> pygame.Surface:
        key = (radius_px, color, alpha_scale)
        if key in self._glow_cache:
            return self._glow_cache[key]

        size = radius_px * 2 + 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2

        # very simple soft bloom
        pygame.draw.circle(surf, (*color, int(0.10 * alpha_scale)), (cx, cy), radius_px)
        pygame.draw.circle(surf, (*color, int(0.22 * alpha_scale)), (cx, cy), int(radius_px * 0.60))
        pygame.draw.circle(surf, (*color, int(0.45 * alpha_scale)), (cx, cy), int(radius_px * 0.32))
        pygame.draw.circle(surf, (255, 255, 255, int(0.85 * alpha_scale)), (cx, cy), max(2, int(radius_px * 0.10)))

        self._glow_cache[key] = surf
        return surf

    # --------- sparks (optional, stable) ----------
    def emit_sparks(self, x_px, y_px, dirx, diry, intensity, dt, color):
        # keep it subtle
        if intensity < 0.25:
            return

        rate = lerp(8.0, 120.0, intensity)
        expected = rate * dt
        count = int(expected)
        if random.random() < (expected - count):
            count += 1

        if len(self.sparks) > self.max_sparks:
            self.sparks = self.sparks[-self.max_sparks:]

        tailx = -dirx
        taily = -diry
        base_ang = math.atan2(taily, tailx)

        for _ in range(count):
            ang = base_ang + random.uniform(-0.55, 0.55)
            spd = lerp(50.0, 240.0, intensity) * random.uniform(0.6, 1.0)

            vx = math.cos(ang) * spd + random.uniform(-15, 15)
            vy = math.sin(ang) * spd + random.uniform(-15, 15)

            life = lerp(0.20, 0.65, 1.0 - intensity) * random.uniform(0.8, 1.2)
            size = lerp(1.0, 2.4, intensity) * random.uniform(0.8, 1.2)

            spark_color = (
                clamp(int(color[0] + 20), 0, 255),
                clamp(int(color[1] + 10), 0, 255),
                clamp(int(color[2] - 10), 0, 255),
            )

            self.sparks.append(Spark(x_px, y_px, vx, vy, life, life, size, spark_color))

    def update_sparks(self, dt):
        alive = []
        for s in self.sparks:
            s.life -= dt
            if s.life <= 0:
                continue
            s.vx *= self.spark_air_drag
            s.vy = s.vy * self.spark_air_drag + self.spark_gravity * dt
            s.x += s.vx * dt
            s.y += s.vy * dt
            alive.append(s)
        self.sparks = alive

    def draw_sparks(self, screen):
        if not self.sparks:
            return
        surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for s in self.sparks:
            t = s.life / s.max_life
            a = int(255 * (t ** 1.4))
            pygame.draw.circle(surf, (*s.color, a), (int(s.x), int(s.y)), max(1, int(s.size)))
        screen.blit(surf, (0, 0))

    # --------- trail ----------
    def draw_trail(self, screen, trail_points_px, color, intensity):
        if len(trail_points_px) < 2:
            return
        surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        n = len(trail_points_px)

        base_w = lerp(2.0, 6.0, intensity)

        for i, (px, py) in enumerate(trail_points_px):
            t = i / max(1, n - 1)
            a = int(lerp(8, 140, t) * (0.45 + 0.55 * intensity))
            w = int(max(1, base_w * (0.35 + 0.75 * t)))
            pygame.draw.circle(surf, (*color, a), (px, py), w)

        screen.blit(surf, (0, 0))

    # --------- meteor ----------
    def draw_meteor(self, screen, x, y, vx, vy, color, intensity, radius_m, meters_per_pixel):
        """
        IMPORTANT: screen y is down, physics y is up => flip vy for screen direction.
        """
        sp = math.hypot(vx, vy) + 1e-9
        dirx = vx / sp
        diry = -vy / sp

        # Speed-based streak
        speed_km_s = sp / 1000.0
        streak_len = int(clamp(16 + speed_km_s * 7.0, 20, 220) * (0.55 + 0.45 * intensity))
        streak_w = int(clamp(2 + speed_km_s * 0.25, 2, 10) * (0.65 + 0.35 * intensity))

        # streak behind
        streak = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        tx = x - int(dirx * streak_len)
        ty = y - int(diry * streak_len)

        for i in range(5):
            t = i / 4.0
            a = int(lerp(210, 25, t) * (0.35 + 0.65 * intensity))
            w = max(1, int(streak_w * (1.0 - 0.55 * t)))
            pygame.draw.line(streak, (*color, a), (x, y), (lerp(x, tx, 1.0 - t), lerp(y, ty, 1.0 - t)), w)

        screen.blit(streak, (0, 0))

        # simple bloom
        glow_r = int(lerp(18, 80, intensity))
        alpha_scale = int(lerp(70, 255, intensity))
        glow = self._get_glow_surface(glow_r, color, alpha_scale)
        screen.blit(glow, (x - glow.get_width() // 2, y - glow.get_height() // 2))

        # core bead
        r_px = int(clamp((radius_m / meters_per_pixel) * 900.0, 2, 12))
        core = pygame.Surface((r_px * 6, r_px * 6), pygame.SRCALPHA)
        cx = cy = core.get_width() // 2
        pygame.draw.circle(core, (*color, 220), (cx, cy), r_px + 2)
        pygame.draw.circle(core, (255, 255, 255, 235), (cx, cy), max(2, int(r_px * 0.55)))
        screen.blit(core, (x - cx, y - cy))

        return dirx, diry
