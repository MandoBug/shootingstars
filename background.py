# background.py
import random
import pygame

def make_starfield(width, height, n_stars=520, seed=9):
    rng = random.Random(seed)
    surf = pygame.Surface((width, height))
    surf.fill((0, 0, 0))

    for _ in range(n_stars):
        x = rng.randrange(0, width)
        y = rng.randrange(0, height)
        b = rng.choice([120, 140, 160, 180, 210, 240])

        tint = rng.random()
        if tint < 0.06:
            col = (b, b, min(255, b + 20))
        elif tint < 0.12:
            col = (min(255, b + 20), b, b)
        else:
            col = (b, b, b)

        r = 1 if rng.random() < 0.92 else 2
        pygame.draw.circle(surf, col, (x, y), r)

    return surf


def draw_atmosphere_bands(screen, meters_to_px_y, width, font):
    """
    Smooth atmosphere bands with labels.
    """
    # (name, top_km, color_rgb)
    layers = [
        ("Thermosphere", 120, (20, 30, 55)),
        ("Mesosphere",    80, (35, 55, 95)),
        ("Stratosphere",  50, (55, 85, 130)),
        ("Troposphere",   12, (70, 110, 160)),
    ]

    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

    # Draw from ground upward (0->120km)
    # We'll gradient between bands for clean transitions.
    # (bottom_km, top_km, bottom_color, top_color)
    bands = [
        (0, 12,  (85, 125, 175), (70, 110, 160)),
        (12, 50, (70, 110, 160), (55, 85, 130)),
        (50, 80, (55, 85, 130),  (35, 55, 95)),
        (80,120, (35, 55, 95),   (20, 30, 55)),
    ]

    for bkm, tkm, c0, c1 in bands:
        y0 = meters_to_px_y(bkm * 1000)
        y1 = meters_to_px_y(tkm * 1000)
        y_low = min(y0, y1)
        y_high = max(y0, y1)
        h = max(1, y_high - y_low)

        for i in range(h):
            t = i / (h - 1) if h > 1 else 1.0
            c = (
                int(c0[0] + (c1[0] - c0[0]) * t),
                int(c0[1] + (c1[1] - c0[1]) * t),
                int(c0[2] + (c1[2] - c0[2]) * t),
                90
            )
            pygame.draw.line(overlay, c, (0, y_low + i), (width, y_low + i))

    screen.blit(overlay, (0, 0))

    # Labels (right side), placed around midpoints
    for name, top_km, _ in layers:
        bottom_km = 0
        if name == "Troposphere":
            bottom_km = 0
        elif name == "Stratosphere":
            bottom_km = 12
        elif name == "Mesosphere":
            bottom_km = 50
        elif name == "Thermosphere":
            bottom_km = 80

        mid_km = (bottom_km + top_km) / 2
        y = meters_to_px_y(mid_km * 1000)

        label = font.render(f"{name} ({top_km} km)", True, (230, 230, 230))
        screen.blit(label, (width - label.get_width() - 24, y - 10))
