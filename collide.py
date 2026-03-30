import numpy as np


def simulate_meteor_collision(duration=10.0, dt=0.01, output_every=5):
    """
    Simulate two meteors colliding.
    
    Args:
        duration: Simulation time (seconds)
        dt: Timestep (seconds)
        output_every: Output every N steps
    """
    
    # Meteor properties
    # Meteor 1: Larger, slower
    m1 = 1000.0 # 1 ton
    r1 = 1.0 # radius = 1m
    pos1 = np.array([-2500.0, 0.0, 0.0]) # Start 2.5km away on left
    vel1 = np.array([400.0, 0.0, 0.0]) # Moving right at 400 m/s
    
    # Meteor 2: Smaller, faster
    m2 = 100.0 # 100 kg
    r2 = 0.5 # 0.5 meter radius
    pos2 = np.array([2500.0, 0.0, 0.0]) # Start 2.5km away on right
    vel2 = np.array([-600.0, 0.0, 0.0]) # Moving left at 600 m/s
    
    print("\nMeteor 1:")
    print(f"  Mass: {m1:.0f} kg")
    print(f"  Radius: {r1:.1f} m")
    print(f"  Initial velocity: {vel1[0]:.1f} m/s")
    
    print("\nMeteor 2:")
    print(f"  Mass: {m2:.0f} kg")
    print(f"  Radius: {r2:.1f} m")
    print(f"  Initial velocity: {vel2[0]:.1f} m/s")
    
    # Collision parameters
    collision_distance = r1 + r2
    collision_occurred = False
    collision_time = None
    
    # After collision - create fragments
    fragments_created = False
    fragment_positions = []
    fragment_velocities = []
    fragment_radii = []
    fragment_masses = []
    
    n_steps = int(duration / dt)
    
    print(f"\nSimulation:")
    print(f"  Duration: {duration:.1f} seconds")
    print(f"  Timestep: {dt:.3f} seconds")
    print(f"  Expected collision time: ~{2500/(400+600):.2f} seconds")
    
    with open('meteor_collision.dump', 'w') as f:
        frame = 0
        
        for step in range(n_steps):
            time = step * dt
            
            # Check for collision
            if not collision_occurred:
                distance = np.linalg.norm(pos2 - pos1)
                
                if distance <= collision_distance:
                    print(f"\nCollision at t={time:.3f}s!")
                    collision_occurred = True
                    collision_time = time
                    
                    # Calculate collision physics
                    # Relative velocity
                    v_rel = vel2 - vel1
                    
                    # Center of mass velocity
                    v_com = (m1 * vel1 + m2 * vel2) / (m1 + m2)
                    
                    # Create fragments (simple model - 4 large + 8 small pieces)
                    n_large = 4
                    n_small = 8
                    
                    # Collision center
                    col_center = (m1 * pos1 + m2 * pos2) / (m1 + m2)
                    
                    # Large fragments (from main masses)
                    for i in range(n_large):
                        angle = 2 * np.pi * i / n_large
                        offset = 3.0 * np.array([np.cos(angle), np.sin(angle), 0])
                        
                        fragment_positions.append(col_center + offset)
                        
                        # Velocity: COM + random + tangential
                        v_fragment = v_com + np.random.randn(3) * 100 + \
                                   np.array([-np.sin(angle), np.cos(angle), 0]) * 200
                        fragment_velocities.append(v_fragment)
                        
                        fragment_radii.append(0.4)
                        fragment_masses.append((m1 + m2) / (n_large + n_small) * 1.5)
                    
                    # Small fragments (debris)
                    for i in range(n_small):
                        angle = 2 * np.pi * i / n_small + np.pi/n_small
                        offset = 5.0 * np.array([np.cos(angle), np.sin(angle), 
                                                np.random.uniform(-0.2, 0.2)])
                        
                        fragment_positions.append(col_center + offset)
                        
                        # Velocity: faster, more random
                        v_fragment = v_com + np.random.randn(3) * 200
                        fragment_velocities.append(v_fragment)
                        
                        fragment_radii.append(0.2)
                        fragment_masses.append((m1 + m2) / (n_large + n_small) * 0.5)
                    
                    fragments_created = True
            
            # Update positions
            if not collision_occurred:
                pos1 += vel1 * dt
                pos2 += vel2 * dt
            elif fragments_created:
                # Update fragment positions
                for i in range(len(fragment_positions)):
                    fragment_positions[i] += fragment_velocities[i] * dt
            
            # Write output frame
            if step % output_every == 0:
                # Calculate box bounds
                if not collision_occurred:
                    all_pos = np.vstack([pos1, pos2])
                else:
                    all_pos = np.array(fragment_positions)
                
                margin = 500.0
                box_min = all_pos.min(axis=0) - margin
                box_max = all_pos.max(axis=0) + margin
                
                # Write header
                f.write("ITEM: TIMESTEP\n")
                f.write(f"{step}\n")
                f.write("ITEM: NUMBER OF ATOMS\n")
                
                if not collision_occurred:
                    f.write("2\n")
                else:
                    f.write(f"{len(fragment_positions)}\n")
                
                f.write("ITEM: BOX BOUNDS pp pp pp\n")
                f.write(f"{box_min[0]} {box_max[0]}\n")
                f.write(f"{box_min[1]} {box_max[1]}\n")
                f.write(f"{box_min[2]} {box_max[2]}\n")
                f.write("ITEM: ATOMS id type x y z vx vy vz radius mass speed\n")
                
                # Write particles
                if not collision_occurred:
                    # Before collision - two meteors
                    speed1 = np.linalg.norm(vel1)
                    speed2 = np.linalg.norm(vel2)
                    
                    f.write(f"1 1 {pos1[0]:.3f} {pos1[1]:.3f} {pos1[2]:.3f} "
                           f"{vel1[0]:.3f} {vel1[1]:.3f} {vel1[2]:.3f} "
                           f"{r1:.3f} {m1:.3f} {speed1:.3f}\n")
                    
                    f.write(f"2 2 {pos2[0]:.3f} {pos2[1]:.3f} {pos2[2]:.3f} "
                           f"{vel2[0]:.3f} {vel2[1]:.3f} {vel2[2]:.3f} "
                           f"{r2:.3f} {m2:.3f} {speed2:.3f}\n")
                else:
                    # After collision - fragments
                    for i, (pos, vel, rad, mass) in enumerate(zip(
                        fragment_positions, fragment_velocities, 
                        fragment_radii, fragment_masses
                    )):
                        speed = np.linalg.norm(vel)
                        frag_type = 3 if i < 4 else 4  # Type 3 for large, 4 for small
                        
                        f.write(f"{i+1} {frag_type} {pos[0]:.3f} {pos[1]:.3f} {pos[2]:.3f} "
                               f"{vel[0]:.3f} {vel[1]:.3f} {vel[2]:.3f} "
                               f"{rad:.3f} {mass:.3f} {speed:.3f}\n")
                
                frame += 1
                
                if step % (output_every * 20) == 0:
                    progress = 100 * step / n_steps
                    if not collision_occurred:
                        dist = np.linalg.norm(pos2 - pos1)
                        print(f"  t={time:.2f}s ({progress:.0f}%) | distance={dist:.0f}m")
                    else:
                        print(f"  t={time:.2f}s ({progress:.0f}%) | {len(fragment_positions)} fragments")
    
    print(f"\nSimulation complete! ({frame} frames)")
    print(f"Output: meteor_collision.dump")
    
    if collision_occurred:
        print(f"\nCollision occurred at t={collision_time:.3f}s")
        print(f"   Created {len(fragment_positions)} fragments")


if __name__ == "__main__":
    simulate_meteor_collision(
        duration=10.0,    # 10 seconds total
        dt=0.01,         # 10ms timesteps
        output_every=5   # Frame every 50ms
    )