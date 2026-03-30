"""
Binary Star System Simulation

Two massive objects orbiting their common center of mass.
Perfect for OVITO - similar scales, easy to see!
"""

import numpy as np
import matplotlib.pyplot as plt


def create_binary_system():
    """
    Create a binary star/planet system.
    
    Returns:
        positions, velocities, masses, radii for both objects
    """
    # Physical constants
    G = 6.67430e-11  # Gravitational constant
    
    # System parameters - let's make "stars" that are planet-sized for easier visualization
    m1 = 5.972e24  # Mass of object 1 (Earth-like)
    m2 = 7.342e22   # Mass of object 2 (Moon-like)
    
    r1_physical = 6.371e6   # Radius of object 1 (m)
    r2_physical = 1.737e6   # Radius of object 2 (m)
    
    # For visualization, we'll scale these up significantly
    r1_visual = 50000  # 50km for visualization
    r2_visual = 20000  # 20km for visualization
    
    # Orbital parameters
    separation = 384400e3 / 100  # 1/100th of Moon-Earth distance for faster orbit
    
    # Calculate center of mass position
    total_mass = m1 + m2
    r1 = separation * m2 / total_mass  # Distance of m1 from COM
    r2 = separation * m1 / total_mass  # Distance of m2 from COM
    
    # Initial positions (both on x-axis, COM at origin)
    pos1 = np.array([-r1, 0.0, 0.0])
    pos2 = np.array([r2, 0.0, 0.0])
    
    # Orbital velocity for circular orbit
    v_orbit = np.sqrt(G * total_mass / separation)
    
    # Initial velocities (perpendicular to position, in y direction)
    vel1 = np.array([0.0, -v_orbit * m2 / total_mass, 0.0])
    vel2 = np.array([0.0, v_orbit * m1 / total_mass, 0.0])
    
    print("Binary System Parameters:")
    print(f"  Object 1: mass={m1:.2e} kg, radius={r1_visual/1000:.1f} km (viz)")
    print(f"  Object 2: mass={m2:.2e} kg, radius={r2_visual/1000:.1f} km (viz)")
    print(f"  Separation: {separation/1000:.0f} km")
    print(f"  Orbital velocity: {v_orbit:.1f} m/s")
    print(f"  Period: {2*np.pi*separation/v_orbit/3600:.1f} hours")
    
    return pos1, pos2, vel1, vel2, m1, m2, r1_visual, r2_visual


def simulate_binary_system(duration=86400, dt=60.0, output_every=10):
    """
    Simulate binary system and output to OVITO format.
    
    Args:
        duration: Simulation time (seconds) - default 1 day
        dt: Timestep (seconds)
        output_every: Output every N steps
    """
    print("="*70)
    print("BINARY STAR SYSTEM SIMULATION")
    print("="*70)
    
    G = 6.67430e-11
    
    # Initialize system
    pos1, pos2, vel1, vel2, m1, m2, r1, r2 = create_binary_system()
    
    # Simulation parameters
    n_steps = int(duration / dt)
    
    print(f"\nSimulation parameters:")
    print(f"  Duration: {duration/3600:.1f} hours")
    print(f"  Timestep: {dt:.1f} seconds")
    print(f"  Total steps: {n_steps}")
    print(f"  Output frames: {n_steps//output_every}")
    
    # Open output file
    with open('binary_stars.dump', 'w') as f:
        frame = 0
        
        for step in range(n_steps):
            # Calculate gravitational force
            r_vec = pos2 - pos1  # Vector from 1 to 2
            r = np.linalg.norm(r_vec)
            
            # F = G * m1 * m2 / r^2, direction along r_vec
            F_mag = G * m1 * m2 / (r * r)
            F_vec = F_mag * r_vec / r
            
            # Update velocities (F = ma)
            vel1 += (F_vec / m1) * dt
            vel2 += (-F_vec / m2) * dt
            
            # Update positions
            pos1 += vel1 * dt
            pos2 += vel2 * dt
            
            # Output frame
            if step % output_every == 0:
                # Calculate derived properties
                speed1 = np.linalg.norm(vel1)
                speed2 = np.linalg.norm(vel2)
                
                # Box bounds (auto from positions with margin)
                all_pos = np.vstack([pos1, pos2])
                margin = max(r1, r2) * 5
                
                box_min = all_pos.min(axis=0) - margin
                box_max = all_pos.max(axis=0) + margin
                
                # Write LAMMPS format
                f.write("ITEM: TIMESTEP\n")
                f.write(f"{step}\n")
                f.write("ITEM: NUMBER OF ATOMS\n")
                f.write("2\n")
                f.write("ITEM: BOX BOUNDS pp pp pp\n")
                f.write(f"{box_min[0]} {box_max[0]}\n")
                f.write(f"{box_min[1]} {box_max[1]}\n")
                f.write(f"{box_min[2]} {box_max[2]}\n")
                f.write("ITEM: ATOMS id type x y z vx vy vz radius mass speed\n")
                
                # Object 1
                f.write(f"1 1 {pos1[0]:.3f} {pos1[1]:.3f} {pos1[2]:.3f} "
                       f"{vel1[0]:.3f} {vel1[1]:.3f} {vel1[2]:.3f} "
                       f"{r1:.3f} {m1:.6e} {speed1:.3f}\n")
                
                # Object 2
                f.write(f"2 2 {pos2[0]:.3f} {pos2[1]:.3f} {pos2[2]:.3f} "
                       f"{vel2[0]:.3f} {vel2[1]:.3f} {vel2[2]:.3f} "
                       f"{r2:.3f} {m2:.6e} {speed2:.3f}\n")
                
                frame += 1
                
                if step % (output_every * 100) == 0:
                    progress = 100 * step / n_steps
                    current_sep = np.linalg.norm(pos2 - pos1)
                    print(f"  Step {step}/{n_steps} ({progress:.1f}%) | "
                          f"sep={current_sep/1000:.0f}km")
    
    print(f"\n✓ Simulation complete!")
    print(f"✓ Output: binary_stars.dump ({frame} frames)")
    print(f"\n{'='*70}")
    print("OVITO VISUALIZATION:")
    print("="*70)
    print("\n1. Import: binary_stars.dump")
    print("\n2. Particle settings:")
    print("   • Shape: Sphere")
    print("   • Radius: 'radius'")
    print("   • Scaling: 1.0 (objects are already visible size!)")
    print("\n3. Color by type:")
    print("   • Add modifier → Color Coding")
    print("   • Property: type")
    print("   • Type 1 (larger object): Blue")
    print("   • Type 2 (smaller object): Orange")
    print("\n4. Press SPACE - watch them orbit!")
    print("\nNOTE: No extreme scaling needed - objects are similar size!")
    print("="*70 + "\n")


if __name__ == "__main__":
    simulate_binary_system(
        duration=86400,  # 1 day
        dt=60.0,         # 1 minute timesteps
        output_every=10  # Frame every 10 minutes
    )