# main.py
import pygame
import math
import sys
import random

from meteor import Meteor
from physics import PhysicsEngine
from atmosphere import Atmosphere
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, DT, TIME_SCALE,
    INITIAL_ALTITUDE,
    BURNING_INTENSITY_THRESHOLD,
)

from vfx import MeteorVFX
from background import make_starfield, draw_atmosphere_bands
from fragmentation import fragment_simple

WIDTH, HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT
GROUND_H = 22
GROUND_COLOR = (139, 69, 19)

METERS_PER_PIXEL = 220.0

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Meteor Atmospheric Entry (2D)")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 18)
small_font = pygame.font.SysFont("Arial", 16)
big_font = pygame.font.SysFont("Arial", 26)

atmosphere = Atmosphere()
physics = PhysicsEngine(use_simple_gravity=True)
vfx = MeteorVFX()

starfield = make_starfield(WIDTH, HEIGHT, n_stars=520, seed=9)
rng = random.Random(7)

def physics_to_screen(pos):
    x_px = int(WIDTH * 0.5 + pos[0] / METERS_PER_PIXEL)
    y_px = int((HEIGHT - GROUND_H) - pos[1] / METERS_PER_PIXEL)
    return x_px, y_px

def meters_to_px_y(alt_m):
    return int((HEIGHT - GROUND_H) - alt_m / METERS_PER_PIXEL)

# ------------------------
# CONFIG SCREEN
# ------------------------
def config_screen():
    speed = 20.0
    angle = 45
    radius = 0.02

    selected = 0
    options = ["Speed (km/s)", "Angle (deg)", "Radius (m)"]

    while True:
        screen.blit(starfield, (0, 0))
        title = big_font.render("Meteor Entry Configuration", True, (255, 255, 255))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))

        values = [f"{speed:.1f}", f"{angle:d}", f"{radius:.3f}"]

        for i, label in enumerate(options):
            color = (255, 255, 0) if i == selected else (255, 255, 255)
            text = font.render(f"{label}: {values[i]}", True, color)
            screen.blit(text, (WIDTH//2 - 170, 180 + i * 50))

        hint1 = font.render("UP/DOWN select | LEFT/RIGHT adjust", True, (200, 200, 200))
        hint2 = font.render("ENTER start | ESC quit", True, (200, 200, 200))
        screen.blit(hint1, (WIDTH//2 - hint1.get_width()//2, HEIGHT - 90))
        screen.blit(hint2, (WIDTH//2 - hint2.get_width()//2, HEIGHT - 60))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % 3
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % 3
                elif event.key == pygame.K_LEFT:
                    if selected == 0:
                        speed = max(11.0, speed - 0.5)
                    elif selected == 1:
                        angle = max(5, angle - 1)
                    elif selected == 2:
                        radius = max(0.003, radius - 0.001)
                elif event.key == pygame.K_RIGHT:
                    if selected == 0:
                        speed = min(72.0, speed + 0.5)
                    elif selected == 1:
                        angle = min(85, angle + 1)
                    elif selected == 2:
                        radius = min(0.25, radius + 0.001)
                elif event.key == pygame.K_RETURN:
                    return speed, angle, radius

# ------------------------
# LEGEND (small bottom-left)
# ------------------------
def draw_color_legend_small(meteor):
    stops = meteor.get_color_legend_stops()
    w, h = 240, 150
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 190))

    title = small_font.render("Legend: Color ~ Temp", True, (255, 255, 255))
    surf.blit(title, (10, 8))

    y = 34
    for T, color in stops:
        pygame.draw.rect(surf, color, (10, y, 22, 16))
        label = small_font.render(f"{int(T)} K", True, (230, 230, 230))
        surf.blit(label, (40, y - 1))
        y += 24

    note = small_font.render("T ≈ 10 · (v[km/s])²", True, (200, 200, 200))
    surf.blit(note, (10, h - 26))

    screen.blit(surf, (16, HEIGHT - h - 16))

# ------------------------
# HUD / status
# ------------------------
def status_for(m: Meteor, intensity: float):
    alt = m.get_altitude()
    if alt <= 0:
        return "IMPACT", (255, 80, 80)
    if not m.alive:
        return "BURNED UP", (255, 120, 120)
    if intensity >= BURNING_INTENSITY_THRESHOLD:
        return "BURNING", (255, 200, 90)
    return "FLYING", (200, 220, 255)

def draw_hud(sim_time, main, fps, paused, intensity, fragment_done, meteor_count):
    alt_km = main.get_altitude() / 1000.0
    spd_km_s = main.get_speed() / 1000.0
    temp = main.get_temperature()
    status, status_col = status_for(main, intensity)

    lines = [
        f"Time: {sim_time:.2f} s",
        f"Altitude: {alt_km:.1f} km",
        f"Speed: {spd_km_s:.2f} km/s",
        f"Temperature: {temp:.0f} K",
        f"Brightness: {intensity:.2f}",
        f"Status: {status}",
        f"Fragments: {'YES' if fragment_done else 'no'}  (count={meteor_count})",
        f"FPS: {fps:.0f}",
    ]

    x0, y0 = WIDTH - 360, 20
    for i, txt in enumerate(lines):
        col = status_col if txt.startswith("Status:") else (255, 255, 255)
        img = font.render(txt, True, col)
        screen.blit(img, (x0, y0 + i * 22))

    if paused:
        p = font.render("PAUSED - SPACE: Resume | R: Restart", True, (255, 255, 255))
        screen.blit(p, (WIDTH - p.get_width() - 20, 20 + len(lines) * 22 + 18))

# ------------------------
# RUN SIMULATION
# ------------------------
def run_simulation(speed_km_s, angle_deg, radius):
    angle_rad = math.radians(angle_deg)
    speed_m_s = speed_km_s * 1000.0
    vx = speed_m_s * math.cos(angle_rad)
    vy = -speed_m_s * math.sin(angle_rad)

    main = Meteor(
        position=[0.0, float(INITIAL_ALTITUDE), 0.0],
        velocity=[vx, vy, 0.0],
        radius=radius
    )

    meteors = [main]
    paused = False
    sim_time = 0.0
    vfx.sparks.clear()

    fragment_done = False

    while True:
        frame_dt = clock.tick(FPS) / 1000.0
        fps_now = clock.get_fps()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    return
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # ---- physics ----
        if not paused:
            dt_phys = DT * TIME_SCALE
            steps = max(1, int(frame_dt / dt_phys))
            steps = min(steps, 10)

            for _ in range(steps):
                sim_time += dt_phys

                for m in meteors:
                    if not m.alive:
                        continue
                    if m.get_altitude() <= 0:
                        m.alive = False
                        continue

                    physics.rk4_step(m, atmosphere, dt_phys)
                    rho = atmosphere.density(max(0.0, m.get_altitude()))
                    m.update_ablation(rho_air=rho, dt=dt_phys)
                    m.update_trail()

                # SIMPLE fragmentation trigger: once, when main is hot + low enough
                if (not fragment_done) and main.alive:
                    rho = atmosphere.density(max(0.0, main.get_altitude()))
                    intensity = vfx.intensity_from_heating(vfx.heating_proxy(rho, main.get_speed()))

                    if main.get_altitude() < 45000 and intensity > 0.70:
                        fragment_done = True
                        meteors.extend(fragment_simple(main, rng=rng, n=5))

        # ---- intensity for HUD (main meteor) ----
        rho_main = atmosphere.density(max(0.0, main.get_altitude()))
        main_intensity = vfx.intensity_from_heating(vfx.heating_proxy(rho_main, main.get_speed()))

        # ---- render ----
        screen.blit(starfield, (0, 0))
        draw_atmosphere_bands(screen, meters_to_px_y, WIDTH, font)
        pygame.draw.rect(screen, GROUND_COLOR, (0, HEIGHT - GROUND_H, WIDTH, GROUND_H))

        # trails first
        for m in meteors:
            rho = atmosphere.density(max(0.0, m.get_altitude()))
            inten = vfx.intensity_from_heating(vfx.heating_proxy(rho, m.get_speed()))
            col = m.get_color()
            trail_px = [physics_to_screen(p) for p in m.trail]
            vfx.draw_trail(screen, trail_px, col, inten)

        # bodies + sparks
        for m in meteors:
            if not m.alive or m.get_altitude() <= 0:
                continue

            rho = atmosphere.density(max(0.0, m.get_altitude()))
            inten = vfx.intensity_from_heating(vfx.heating_proxy(rho, m.get_speed()))
            col = m.get_color()
            x, y = physics_to_screen(m.pos)

            dirx, diry = vfx.draw_meteor(
                screen, x, y,
                float(m.vel[0]), float(m.vel[1]),
                col, inten,
                float(m.radius),
                METERS_PER_PIXEL
            )

            if not paused:
                vfx.emit_sparks(x, y, dirx, diry, inten, frame_dt, col)

        if not paused:
            vfx.update_sparks(frame_dt)
        vfx.draw_sparks(screen)

        draw_hud(sim_time, main, fps_now, paused, main_intensity, fragment_done, len(meteors))
        draw_color_legend_small(main)

        pygame.display.flip()

# ------------------------
# APP LOOP
# ------------------------
while True:
    speed, angle, radius = config_screen()
    run_simulation(speed, angle, radius)
