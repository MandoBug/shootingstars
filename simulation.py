"""
- Shooting stars entering atmosphere
- Satellites orbiting Earth
- Moon and Sun gravitational effects  
- Asteroids and comets
"""

import numpy as np
from physics2 import *
from ovito import UltimateOVITOWriter
import time


# different scenarios
def create_meteor_storm(n_meteors=200, altitude_km=120, spread_km=100):
    '''
    meteor shower with variety of sizes and materials.
    
    Returns positions, velocities, masses, radii, areas, densities, material_types
    '''
    print(f"  {n_meteors} meteors at {altitude_km}km (mixed materials)")
    
    positions = np.zeros((n_meteors, 3))
    positions[:, 1] = altitude_km * 1000
    positions[:, 0] = np.random.uniform(-spread_km*1000, spread_km*1000, n_meteors)
    positions[:, 2] = np.random.uniform(-spread_km*1000, spread_km*1000, n_meteors)
    
    # Varied entry velocities (11-72 km/s for meteors)
    v_entry = np.random.uniform(15000, 50000, n_meteors)
    angles = np.random.uniform(np.deg2rad(20), np.deg2rad(70), n_meteors)
    
    velocities = np.zeros((n_meteors, 3))
    velocities[:, 1] = -v_entry * np.sin(angles)
    velocities[:, 0] = v_entry * np.cos(angles) * np.random.choice([-1, 1], n_meteors)
    velocities[:, 2] = v_entry * np.cos(angles) * np.random.uniform(-0.3, 0.3, n_meteors)
    
    # Mixed materials: 70% stone, 20% iron, 10% ice
    material_types = np.random.choice([0, 1, 2], n_meteors, p=[0.7, 0.2, 0.1])
    
    densities = np.zeros(n_meteors)
    densities[material_types == 0] = METEOR_DENSITY  # Stone
    densities[material_types == 1] = IRON_DENSITY    # Iron
    densities[material_types == 2] = ICE_DENSITY     # Ice
    
    # Size distribution (power law - more small ones)
    radii = np.random.power(3, n_meteors) * 0.1  # 0-10cm, skewed to small
    masses = (4/3) * np.pi * radii**3 * densities
    areas = np.pi * radii**2
    
    return positions, velocities, masses, radii, areas, densities, material_types


def create_satellite_constellation(n_satellites=100, altitude_km=550):
    """
    Satellite constellation in various orbital inclinations.
    Returns positions, velocities, masses, radii, areas, densities, material_types
    """
    print(f"  {n_satellites} satellites at {altitude_km}km (constellation)")
    
    r_orbit = R_EARTH + altitude_km * 1000
    v_orbital = orbital_velocity(altitude_km * 1000)
    
    positions = np.zeros((n_satellites, 3))
    velocities = np.zeros((n_satellites, 3))
    
    # Multiple orbital planes
    n_planes = 5
    sats_per_plane = n_satellites // n_planes
    
    for plane_idx in range(n_planes):
        inclination = np.deg2rad(53.0 + plane_idx * 10)  # Varied inclinations
        
        for sat_idx in range(sats_per_plane):
            i = plane_idx * sats_per_plane + sat_idx
            if i >= n_satellites:
                break
            
            # Position in orbital plane
            theta = 2 * np.pi * sat_idx / sats_per_plane
            
            # Transform to inclined orbit
            x = r_orbit * np.cos(theta)
            y = r_orbit * np.sin(theta) * np.cos(inclination)
            z = r_orbit * np.sin(theta) * np.sin(inclination)
            
            positions[i] = [x, y, z]
            
            # Velocity perpendicular to position
            r_hat = positions[i] / r_orbit
            z_axis = np.array([0, 0, 1])
            tangent = np.cross(z_axis, r_hat)
            if np.linalg.norm(tangent) < 1e-6:
                tangent = np.array([1, 0, 0])
            tangent = tangent / np.linalg.norm(tangent)
            
            # Rotate tangent to match inclination
            tangent_rotated = np.array([
                -np.sin(theta),
                np.cos(theta) * np.cos(inclination),
                np.cos(theta) * np.sin(inclination)
            ])
            
            velocities[i] = v_orbital * tangent_rotated
    
    # Satellite properties
    radii = np.random.uniform(1.0, 3.0, n_satellites)  # 1-3m satellites
    densities = np.ones(n_satellites) * 500.0  # Low density (hollow)
    masses = (4/3) * np.pi * radii**3 * densities
    areas = np.pi * radii**2
    material_types = np.zeros(n_satellites, dtype=np.int32)  # Stone (doesn't matter much)
    
    return positions, velocities, masses, radii, areas, densities, material_types


def create_space_debris(n_debris=50, altitude_min_km=200, altitude_max_km=1000):
    """
    Random space debris in various orbits (some decaying).
    Returns positions, velocities, masses, radii, areas, densities, material_types
    """
    print(f"  {n_debris} debris pieces ({altitude_min_km}-{altitude_max_km}km)")
    
    positions = np.zeros((n_debris, 3))
    velocities = np.zeros((n_debris, 3))
    
    for i in range(n_debris):
        # Random altitude
        altitude = np.random.uniform(altitude_min_km, altitude_max_km) * 1000
        r_orbit = R_EARTH + altitude
        v_orbital = orbital_velocity(altitude)
        
        # Random position on sphere
        theta = np.random.uniform(0, 2*np.pi)
        phi = np.random.uniform(0, np.pi)
        
        positions[i] = [
            r_orbit * np.sin(phi) * np.cos(theta),
            r_orbit * np.sin(phi) * np.sin(theta),
            r_orbit * np.cos(phi)
        ]
        
        # Some debris have decaying orbits (80-95% orbital velocity)
        v_factor = np.random.uniform(0.8, 1.0)
        
        r_hat = positions[i] / r_orbit
        up = np.array([0, 0, 1])
        tangent = np.cross(up, r_hat)
        if np.linalg.norm(tangent) < 1e-6:
            tangent = np.array([1, 0, 0])
        tangent = tangent / np.linalg.norm(tangent)
        
        velocities[i] = (v_orbital * v_factor) * tangent
        
        # Add random perturbations
        velocities[i] += np.random.normal(0, 200, 3)
    
    # Debris properties (fragments, paint chips, etc.)
    radii = np.random.uniform(0.01, 0.5, n_debris)  # 1cm to 50cm
    densities = np.ones(n_debris) * 2000.0
    masses = (4/3) * np.pi * radii**3 * densities
    areas = np.pi * radii**2
    material_types = np.ones(n_debris, dtype=np.int32)  # Iron-like
    
    return positions, velocities, masses, radii, areas, densities, material_types


def create_asteroid_flyby(n_asteroids=5):
    """
    Asteroids on hyperbolic trajectories (flyby or impact).
    Returns positions, velocities, masses, radii, areas, densities, material_types
    """
    print(f"  {n_asteroids} asteroids (Earth flyby/impact)")
    
    positions = np.zeros((n_asteroids, 3))
    velocities = np.zeros((n_asteroids, 3))
    
    for i in range(n_asteroids):
        # Start far out, approaching Earth
        distance = np.random.uniform(1e8, 5e8)  # 100,000 - 500,000 km
        
        # Random approach direction
        theta = np.random.uniform(0, 2*np.pi)
        phi = np.random.uniform(0, np.pi)
        
        positions[i] = distance * np.array([
            np.sin(phi) * np.cos(theta),
            np.sin(phi) * np.sin(theta),
            np.cos(phi)
        ])
        
        # Velocity toward Earth (hyperbolic, > escape velocity)
        v_esc = escape_velocity(distance)
        v_approach = v_esc * np.random.uniform(1.2, 2.0)
        
        # Direction: toward Earth with some offset
        to_earth = -positions[i] / distance
        offset = np.random.normal(0, 0.1, 3)
        direction = to_earth + offset
        direction = direction / np.linalg.norm(direction)
        
        velocities[i] = v_approach * direction
    
    # Asteroid sizes (10m to 1km)
    radii = np.random.uniform(10, 1000, n_asteroids)
    densities = np.ones(n_asteroids) * METEOR_DENSITY
    masses = (4/3) * np.pi * radii**3 * densities
    areas = np.pi * radii**2
    material_types = np.zeros(n_asteroids, dtype=np.int32)
    
    return positions, velocities, masses, radii, areas, densities, material_types



### Simulation 
def run_ultimate_simulation(
    include_meteors=True,
    include_satellites=True,
    include_debris=True,
    include_asteroids=False,  # long
    duration=30.0,
    dt=0.01,
    output_every=5
):
    """
    Args:
        include_meteors: Include meteor shower
        include_satellites: Include satellite constellation
        include_debris: Include space debris
        include_asteroids: Include asteroid flybys (WARNING: needs long duration)
        duration: Simulation time (seconds)
        dt: Integration timestep (seconds)
        output_every: Write OVITO frame every N steps
    """
    
    # Collect all particles
    all_data = []
    
    if include_meteors:
        all_data.append(create_meteor_storm(n_meteors=150))
    
    if include_satellites:
        all_data.append(create_satellite_constellation(n_satellites=80))
    
    if include_debris:
        all_data.append(create_space_debris(n_debris=40))
    
    if include_asteroids:
        all_data.append(create_asteroid_flyby(n_asteroids=3))
    
    # Combine all particles
    positions = np.vstack([d[0] for d in all_data])
    velocities = np.vstack([d[1] for d in all_data])
    masses = np.concatenate([d[2] for d in all_data])
    radii = np.concatenate([d[3] for d in all_data])
    areas = np.concatenate([d[4] for d in all_data])
    densities = np.concatenate([d[5] for d in all_data])
    material_types = np.concatenate([d[6] for d in all_data]).astype(np.int32)
    
    n_total = len(positions)
    
    print(f"\nTotal particles: {n_total}")
    print(f"Duration: {duration}s")
    print(f"Timestep: {dt}s")
    
    # Setup massive bodies (Earth, Moon, Sun)
    body_positions = np.zeros((3, 3))
    body_masses = np.zeros(3)
    
    body_positions[0] = EARTH_POS  # Earth at origin
    body_masses[0] = M_EARTH
    
    body_positions[1] = moon_position(0)  # Moon initial position
    body_masses[1] = M_MOON
    
    body_positions[2] = sun_position(0)  # Sun initial position
    body_masses[2] = M_SUN
    
    writer = UltimateOVITOWriter('space.dump', trail_length=40)
    
    # Simulation loop
    n_steps = int(duration / dt)
    start_time = time.time()
    sim_time = 0.0
    
    print(f"\nRunning simulation")
    
    for step in range(n_steps):
        # Update Moon and Sun positions
        body_positions[1] = moon_position(sim_time)
        body_positions[2] = sun_position(sim_time)
        
        # Physics update
        rk4_step_multiscale(
            positions, velocities, masses, areas,
            body_positions, body_masses,
            material_types, dt, scale='auto'
        )
        
        # Ablation update
        alive = update_ablation_multiscale(
            positions, velocities, masses, radii, areas,
            densities, material_types, dt
        )
        
        n_alive = np.sum(alive)
        
        # Write OVITO output
        if step % output_every == 0:
            # Create body markers for visualization
            body_markers = [
                ('Earth', body_positions[0], R_EARTH, M_EARTH),
                ('Moon', body_positions[1], R_MOON, M_MOON),
                ('Sun', body_positions[2], R_SUN * 0.01, M_SUN)  # Scale down Sun for viz
            ]
            
            writer.write_frame(
                positions, velocities, masses, radii,
                timestep=step,
                body_markers=body_markers,
                material_types=material_types
            )
            
            if step % (output_every * 20) == 0:
                elapsed = time.time() - start_time
                progress = 100 * step / n_steps
                print(f"  Step {step}/{n_steps} ({progress:.1f}%) | "
                      f"{n_alive}/{n_total} active | "
                      f"{elapsed:.1f}s elapsed | "
                      f"sim_time={sim_time:.1f}s")
        
        sim_time += dt
        
        # Early exit if nothing left
        if n_alive == 0:
            print(f"\nAll particles gone at step {step}")
            break
    
    writer.finalize()
    
    total_time = time.time() - start_time
    print(f"finished simulation in {total_time:.2f}s")
    print(f"{sim_time:.1f}s of real physics")
    print(f"Output: space.dump ({writer.frame_number} frames)")

# test scenarios 
def quick_meteor_show():
    run_ultimate_simulation(
        include_meteors=True,
        include_satellites=False,
        include_debris=False,
        include_asteroids=False,
        duration=15.0,
        dt=0.01,
        output_every=3
    )


def quick_orbital_mechanics():
    run_ultimate_simulation(
        include_meteors=False,
        include_satellites=True,
        include_debris=True,
        include_asteroids=False,
        duration=600.0,  # 10 minutes for one orbit
        dt=0.1,
        output_every=50
    )


def quick_everything():
    # everything but asteroids 
    run_ultimate_simulation(
        include_meteors=True,
        include_satellites=True,
        include_debris=True,
        include_asteroids=False,
        duration=30.0,
        dt=0.01,
        output_every=5
    )



if __name__ == "__main__":
    import sys
    
    scenarios = {
        '1': ('Meteor shower only', quick_meteor_show),
        '2': ('Orbital mechanics', quick_orbital_mechanics),
        '3': ('Everything combined', quick_everything),
    }
    
    print("\n" + "="*70)
    print("ULTIMATE SPACE SIMULATOR - Choose Your Adventure")
    print("="*70)
    print("\n1. Meteor shower only (15s, fast & dramatic)")
    print("2. Orbital mechanics (satellites + debris, 600s)")
    print("3. Everything combined (meteors + satellites + debris, 30s)")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nChoose scenario (1/2/3) [3]: ").strip() or '3'
    
    if choice in scenarios:
        name, func = scenarios[choice]
        func()
    else:
        print(f"Unknown choice: {choice}, running default")
        quick_everything()