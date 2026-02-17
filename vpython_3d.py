"""
METEOR SIMULATOR - Simple & Beautiful
Just works, looks amazing
"""

from vpython import *
import numpy as np
import random as rand
from meteor import Meteor
from atmosphere import Atmosphere
from physics import PhysicsEngine
from constants import R_EARTH


def main():
    """Simple epic meteor simulation."""
    
    print("\n" + "="*60)
    print("🔥 METEOR SIMULATOR 🔥".center(60))
    print("="*60)
    
    # Get user input
    print("\nSpeed options:")
    print("  1 - Slow (15 km/s)")
    print("  2 - Medium (30 km/s)")
    print("  3 - Fast (50 km/s)")
    print("  4 - EXTREME (72 km/s)")
    
    speed_choice = input("\nChoose speed (1-4): ").strip() or "3"
    speeds = {"1": 15000, "2": 30000, "3": 50000, "4": 72000}
    velocity = speeds.get(speed_choice, 50000)
    
    print("\nAngle options:")
    print("  1 - Shallow (20°)")
    print("  2 - Medium (45°)")
    print("  3 - Steep (70°)")
    
    angle_choice = input("\nChoose angle (1-3): ").strip() or "2"
    angles = {"1": 20, "2": 45, "3": 70}
    angle = angles.get(angle_choice, 45)
    
    print("\n" + "="*60)
    print(f"🚀 Launching {velocity/1000:.0f} km/s at {angle}°")
    print("="*60 + "\n")
    
    # ==================== SCENE ====================
    scene.width = 1920
    scene.height = 1080
    scene.background = vector(0, 0, 0.01)
    scene.title = f"🔥 METEOR: {velocity/1000:.0f} km/s at {angle}° 🔥"
    
    # Lock camera
    scene.userzoom = False
    scene.userspin = False
    scene.userpan = False
    
    # Set camera view
    scene.camera.pos = vector(0, 200000, 900000)
    scene.camera.axis = vector(0, -0.12, -1)
    scene.range = 400000
    scene.center = vector(0, 80000, 0)
    
    # ==================== EARTH ====================
    earth = sphere(
        pos=vector(0, -R_EARTH, 0),
        radius=R_EARTH,
        texture=textures.earth,
        shininess=2
    )
    
    # Atmosphere - glowing layers
    for h, op, col in [
        (30000, 0.5, vector(0.05, 0.2, 1)),
        (60000, 0.4, vector(0.1, 0.3, 1)),
        (100000, 0.3, vector(0.2, 0.45, 1)),
        (150000, 0.2, vector(0.3, 0.6, 1)),
        (220000, 0.1, vector(0.4, 0.7, 0.95)),
    ]:
        sphere(
            pos=vector(0, -R_EARTH, 0),
            radius=R_EARTH + h,
            opacity=op,
            color=col
        )
    
    # ==================== STARS ====================
    print("Creating starfield...")
    for i in range(1000):
        x = (rand.random() - 0.5) * R_EARTH * 25
        y = rand.random() * R_EARTH * 8
        z = (rand.random() - 0.5) * R_EARTH * 25
        
        bright = rand.random() ** 1.5
        size = R_EARTH * (0.002 + rand.random() ** 2 * 0.03)
        
        sphere(
            pos=vector(x, y, z),
            radius=size,
            color=vector(bright, bright, bright * 0.98),
            emissive=True
        )
    
    print("✓ Stars created")
    
    # Lighting
    distant_light(direction=vector(1, 0.5, 0.3), color=color.white)
    distant_light(direction=vector(-0.5, -0.3, 0.3), color=vector(0.4, 0.5, 0.7))
    
    # ==================== PHYSICS ====================
    atmosphere = Atmosphere()
    physics = PhysicsEngine(use_simple_gravity=True)
    
    # Setup meteor
    angle_rad = radians(angle)
    start_pos = np.array([-700000, 150000, 0])
    
    v_x = velocity * cos(angle_rad)
    v_y = -velocity * sin(angle_rad)
    start_vel = np.array([v_x, v_y, 0])
    
    meteor_obj = Meteor(
        position=start_pos,
        velocity=start_vel,
        mass=0.05,
        radius=0.03
    )
    
    print(f"✓ Meteor ready at ({start_pos[0]/1000:.0f}, {start_pos[1]/1000:.0f}) km")
    print(f"✓ Velocity: ({v_x/1000:.1f}, {v_y/1000:.1f}) km/s\n")
    
    # ==================== METEOR VISUALS ====================
    print("Creating meteor...")
    
    # WHITE HOT CORE
    core = sphere(
        pos=vector(start_pos[0], start_pos[1], 0),
        radius=2000,
        color=color.white,
        emissive=True
    )
    
    # INNER PLASMA - super bright
    plasma = sphere(
        pos=core.pos,
        radius=6000,
        color=vector(1, 1, 0.9),
        opacity=0.95,
        emissive=True
    )
    
    # MID GLOW - yellow
    glow_mid = sphere(
        pos=core.pos,
        radius=12000,
        color=vector(1, 0.95, 0.6),
        opacity=0.8,
        emissive=True
    )
    
    # OUTER GLOW - orange
    glow_outer = sphere(
        pos=core.pos,
        radius=22000,
        color=vector(1, 0.8, 0.4),
        opacity=0.6,
        emissive=True
    )
    
    # FAR GLOW - red
    glow_far = sphere(
        pos=core.pos,
        radius=38000,
        color=vector(1, 0.6, 0.2),
        opacity=0.35,
        emissive=True
    )
    
    # EXTREME FAR GLOW
    glow_extreme = sphere(
        pos=core.pos,
        radius=60000,
        color=vector(1, 0.4, 0.1),
        opacity=0.18,
        emissive=True
    )
    
    print("✓ Meteor created\n")
    
    # Trail storage
    trails = []
    
    # Info label
    info = label(
        pos=vector(0, 500000, 0),
        text='',
        height=30,
        color=color.white,
        box=False
    )
    
    # ==================== MAIN LOOP ====================
    print("🎬 SIMULATION RUNNING\n")
    
    frame = 0
    dt = 0.015
    
    while meteor_obj.alive:
        rate(70)
        
        # Physics
        physics.rk4_step(meteor_obj, atmosphere, dt)
        frame += 1
        
        # Update position
        pos = vector(meteor_obj.pos[0], meteor_obj.pos[1], 0)
        
        core.pos = pos
        plasma.pos = pos
        glow_mid.pos = pos
        glow_outer.pos = pos
        glow_far.pos = pos
        glow_extreme.pos = pos
        
        # Get data
        speed = meteor_obj.get_speed()
        alt = meteor_obj.get_altitude()
        temp = meteor_obj.get_temperature()
        
        # CRAZY PULSING
        pulse = 1 + 0.5 * sin(frame * 0.7)
        plasma.opacity = 0.95 * pulse
        glow_mid.opacity = 0.8 * pulse
        glow_outer.opacity = 0.6 * pulse
        
        core.radius = 2000 * (1 + 0.3 * sin(frame * 0.7))
        
        # Dynamic colors based on speed
        intensity = min(1, speed / 50000)
        
        if speed > 60000:
            # BLUE-WHITE (extreme speed)
            core.color = vector(0.9, 0.95, 1)
            plasma.color = vector(0.92, 0.97, 1)
            glow_mid.color = vector(0.95, 0.98, 1)
            glow_outer.color = vector(1, 1, 0.9)
        elif speed > 40000:
            # WHITE-YELLOW (very fast)
            core.color = vector(1, 1, 0.98)
            plasma.color = vector(1, 1, 0.95)
            glow_mid.color = vector(1, 0.98, 0.8)
            glow_outer.color = vector(1, 0.9, 0.6)
        elif speed > 20000:
            # YELLOW-ORANGE (fast)
            core.color = vector(1, 0.98, 0.8)
            plasma.color = vector(1, 0.95, 0.7)
            glow_mid.color = vector(1, 0.9, 0.5)
            glow_outer.color = vector(1, 0.8, 0.3)
        else:
            # ORANGE-RED (slower)
            core.color = vector(1, 0.9, 0.6)
            plasma.color = vector(1, 0.85, 0.5)
            glow_mid.color = vector(1, 0.75, 0.3)
            glow_outer.color = vector(1, 0.6, 0.2)
        
        # TRAIL - every frame
        trail = sphere(
            pos=pos,
            radius=3000,
            color=core.color,
            emissive=True,
            opacity=1
        )
        trails.append({'obj': trail, 'age': 0})
        
        # Age trail
        max_age = 200
        for t in trails:
            t['age'] += 1
            fade = 1 - (t['age'] / max_age)
            
            if fade > 0:
                t['obj'].opacity = fade ** 0.4
                t['obj'].radius *= 0.975
                
                # Color fade: white -> yellow -> orange -> red -> dark
                if fade > 0.8:
                    pass
                elif fade > 0.5:
                    t['obj'].color = vector(1, fade * 1.3, fade * 0.6)
                elif fade > 0.25:
                    t['obj'].color = vector(1, fade * 0.8, 0)
                else:
                    t['obj'].color = vector(fade * 3, fade * 0.3, 0)
            else:
                t['obj'].visible = False
        
        trails = [t for t in trails if t['age'] < max_age]
        
        # Update info
        if frame % 25 == 0:
            info.text = f"⚡ {speed/1000:.1f} km/s   📏 {alt/1000:.0f} km   🔥 {temp:.0f}K"
        
        # Print progress
        if frame % 80 == 0:
            print(f"⚡ Alt: {alt/1000:>5.0f} km | Speed: {speed/1000:>5.1f} km/s | Temp: {temp:>6.0f}K")
        
        # Check impact
        if alt <= 0:
            meteor_obj.alive = False
            
            print("\n" + "="*60)
            print("💥 IMPACT! 💥".center(60))
            print("="*60)
            print(f"Impact speed: {speed/1000:.1f} km/s")
            print(f"Peak temp: {temp:.0f} K")
            print("="*60 + "\n")
            
            # HUGE EXPLOSION
            for i in range(8):
                sphere(
                    pos=pos,
                    radius=100000 * (i + 1) * 0.45,
                    opacity=0.9 - i * 0.1,
                    color=vector(1, 0.95 - i * 0.1, 0.7 - i * 0.08),
                    emissive=True
                )
            
            # Debris
            for i in range(100):
                angle = rand.random() * 2 * 3.14159
                sphere(
                    pos=pos,
                    radius=4000 * (0.3 + rand.random()),
                    color=vector(1, 0.2 + rand.random() * 0.8, rand.random() * 0.6),
                    emissive=True,
                    make_trail=True,
                    trail_radius=2000
                )
            
            sleep(3)
            break
        
        # Safety
        if abs(meteor_obj.pos[0]) > 2500000:
            print("\n⚠️  Meteor left area\n")
            break
    
    print("✓ Simulation complete\n")


if __name__ == "__main__":
    main()