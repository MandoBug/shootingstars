import numpy as np
from numba import njit, prange


# Constants 

# Universal constants
G = 6.67430e-11 # Gravitational constant (m³/kg/s²)

# Earth
M_EARTH = 5.972e24 # Earth mass (kg)
R_EARTH = 6.371e6 # Earth radius (m)
EARTH_POS = np.array([0.0, 0.0, 0.0]) # Earth at origin

# Moon
M_MOON = 7.342e22   # Moon mass (kg)
R_MOON = 1.737e6    # Moon radius (m)
MOON_ORBIT = 384400e3  # Moon orbital radius (m)

# Sun
M_SUN = 1.989e30 # Sun mass (kg)
R_SUN = 6.96e8 # Sun radius (m)
SUN_DISTANCE = 1.496e11  # 1 AU (m)

# Other planets (for future expansion)
M_MARS = 6.4171e23
M_JUPITER = 1.898e27

# Atmosphere model
g = 9.81 # Surface gravity (m/s²)
RHO_0 = 1.225 # Sea level air density (kg/m³)
H_SCALE = 8500.0 # Scale height (m)
DRAG_COEFFICIENT = 0.47

# Material properties
METEOR_DENSITY = 3500.0 # Stone meteor (kg/m³)
IRON_DENSITY = 7870.0 # Iron meteor (kg/m³)
ICE_DENSITY = 920.0 # Ice/comet (kg/m³)
ABLATION_COEFF = 3.5e-9


# N-Body Gravity (for planets, moons, asteroids)

@njit
def gravity_n_body(pos_i, body_positions, body_masses, i_is_massive=False, self_idx=-1):
    #N-body gravitational force on particle i from all massive bodies.
    
    """
    Args:
        pos_i: Position of particle i (3D vector)
        body_positions: (N_bodies, 3) array of massive body positions
        body_masses: (N_bodies,) array of body masses
        i_is_massive: If True, particle i is also a massive body (avoid self-force)
        self_idx: If i_is_massive, this is the index of particle i in body arrays
    
    Returns 3D force vector (N)
    """
    
    F_total = np.zeros(3)
    
    for j in range(len(body_masses)):
        # Skip self-interaction if this particle is a massive body
        if i_is_massive and j == self_idx:
            continue
        
        r_vec = body_positions[j] - pos_i
        r = np.sqrt(r_vec[0]**2 + r_vec[1]**2 + r_vec[2]**2)
        
        # Avoid singularity at body center - use surface if inside
        body_radius = estimate_body_radius(body_masses[j])
        if r < body_radius:
            r = body_radius
        
        # F = G * m1 * m2 / r ^ 2 in direction of r_vec
        # For force ON particle i, we need mass of i, but we'll return force per unit mass
        # Actually, return acceleration (F/m) so caller can multiply by their mass
        F_mag = G * body_masses[j] / (r * r)
        F_total += F_mag * r_vec / r
    
    return F_total


@njit
def estimate_body_radius(mass):
    # Estimate body radius assuming Earth-like density
    density = 5000.0  # kg/m³
    volume = mass / density
    radius = (3 * volume / (4 * np.pi)) ** (1.0/3.0)
    return radius


# atmosphere
@njit
def air_density(altitude):
    # Exponential atmosphere model.
    if altitude < 0:
        return RHO_0
    return RHO_0 * np.exp(-altitude / H_SCALE)


@njit
def drag_force_per_mass(velocity, altitude, area, mass):
    """
    Drag force divided by mass (i.e., drag acceleration).
    
    Args:
        velocity: 3D velocity vector (m/s)
        altitude: Height above Earth surface (m)
        area: Cross-sectional area (m²)
        mass: Particle mass (kg)
    
    Returns 3D acceleration from drag (m/s^2)
    """
    # Protect against zero/tiny mass
    if mass < 1e-10:
        return np.zeros(3)
    
    rho = air_density(altitude)
    speed = np.sqrt(velocity[0]**2 + velocity[1]**2 + velocity[2]**2)
    
    if speed < 1e-6:
        return np.zeros(3)
    
    # F_drag = 0.5 * rho * v^2 * Cd * A
    # a_drag = F_drag / m
    drag_mag = 0.5 * rho * speed * speed * DRAG_COEFFICIENT * area / mass
    
    return -drag_mag * velocity / speed


# ablation
@njit
def ablation_rate(velocity, altitude, area, mass, material_type=0):
    """
    Mass loss rate from ablation.
    
    Args:
        velocity: 3D velocity vector (m/s)
        altitude: Height above surface (m)
        area: Cross-sectional area (m²)
        mass: Current mass (kg)
        material_type: 0=stone, 1=iron, 2=ice
    
    Returns dm/dt (kg/s) - always positive
    """
    rho = air_density(altitude)
    speed = np.sqrt(velocity[0]**2 + velocity[1]**2 + velocity[2]**2)
    
    if speed < 1.0:
        return 0.0
    
    # Different materials ablate at different rates
    if material_type == 1:  # Iron
        k = ABLATION_COEFF * 0.3  # Iron more resistant
    elif material_type == 2:  # Ice
        k = ABLATION_COEFF * 3.0  # Ice ablates faster
    else:  # Stone (default)
        k = ABLATION_COEFF
    
    # dm/dt = k * A * ρ * v³
    dm_dt = k * area * rho * (speed ** 3)
    
    return dm_dt


# force calc
@njit
def total_acceleration(position, velocity, mass, area, 
                      body_positions, body_masses,
                      material_type=0, scale='auto'):
    """
    Calculate total acceleration from all forces.
    
    Automatically chooses appropriate physics based on scale:
    - Near Earth surface: atmosphere + Earth gravity
    - Low orbit: atmosphere + Earth gravity (inverse square)
    - High orbit: Earth + Moon + Sun gravity
    - Solar system: All major bodies
    
    Args:
        position: 3D position from Earth center (m)
        velocity: 3D velocity (m/s)
        mass: Particle mass (kg)
        area: Cross-sectional area (m²)
        body_positions: (N_bodies, 3) positions of massive bodies
        body_masses: (N_bodies,) masses of massive bodies
        material_type: Material for ablation
        scale: 'auto', 'atmospheric', 'orbital', 'solar'
    
    Returns 3D acceleration vector (m/s²)
    """
    # If mass is negligible, return zero acceleration (particle is dead)
    if mass < 1e-10:
        return np.zeros(3)
    
    # Determine altitude and scale
    r = np.sqrt(position[0]**2 + position[1]**2 + position[2]**2)
    altitude = r - R_EARTH
    
    # Auto-detect scale if needed
    if scale == 'auto':
        if altitude < 200e3:  # Below 200km
            scale = 'atmospheric'
        elif r < MOON_ORBIT * 0.5:  # Inside half Moon orbit
            scale = 'orbital'
        else:
            scale = 'solar'
    
    # Gravity acceleration (from all bodies)
    a_grav = gravity_n_body(position, body_positions, body_masses)
    
    # Drag acceleration (only if in atmosphere)
    if scale == 'atmospheric' or (scale == 'orbital' and altitude < 150e3):
        a_drag = drag_force_per_mass(velocity, altitude, area, mass)
    else:
        a_drag = np.zeros(3)
    
    return a_grav + a_drag


# rk4
@njit
def rk4_derivative_multiscale(positions, velocities, masses, areas,
                              body_positions, body_masses,
                              material_types, scale='auto'):
    """
    Calculate derivatives for multi-scale RK4 integration.
    
    Args:
        positions: (N, 3) positions from Earth center
        velocities: (N, 3) velocities
        masses: (N,) masses
        areas: (N,) cross-sectional areas
        body_positions: (N_bodies, 3) massive body positions
        body_masses: (N_bodies,) massive body masses
        material_types: (N,) material type per particle
        scale: 'auto', 'atmospheric', 'orbital', or 'solar'
    
    Returns d_pos, d_vel: (N, 3) derivatives
    """
    N = positions.shape[0]
    d_pos = np.empty((N, 3))
    d_vel = np.empty((N, 3))
    
    for i in range(N):
        # Position derivative = velocity
        d_pos[i] = velocities[i]
        
        # Velocity derivative = acceleration
        d_vel[i] = total_acceleration(
            positions[i], velocities[i], masses[i], areas[i],
            body_positions, body_masses,
            material_types[i], scale
        )
    
    return d_pos, d_vel


@njit(parallel=True)
def rk4_step_multiscale(positions, velocities, masses, areas, body_positions, body_masses, material_types, dt, scale='auto'):
    
    N = positions.shape[0]
    
    # Allocate temp arrays
    k1_pos = np.empty((N, 3))
    k1_vel = np.empty((N, 3))
    k2_pos = np.empty((N, 3))
    k2_vel = np.empty((N, 3))
    k3_pos = np.empty((N, 3))
    k3_vel = np.empty((N, 3))
    k4_pos = np.empty((N, 3))
    k4_vel = np.empty((N, 3))
    
    temp_pos = np.empty((N, 3))
    temp_vel = np.empty((N, 3))
    
    # k1
    k1_pos, k1_vel = rk4_derivative_multiscale(
        positions, velocities, masses, areas,
        body_positions, body_masses, material_types, scale
    )
    
    # k2
    for i in prange(N):
        temp_pos[i] = positions[i] + k1_pos[i] * (dt / 2)
        temp_vel[i] = velocities[i] + k1_vel[i] * (dt / 2)
    
    k2_pos, k2_vel = rk4_derivative_multiscale(
        temp_pos, temp_vel, masses, areas,
        body_positions, body_masses, material_types, scale
    )
    
    # k3
    for i in prange(N):
        temp_pos[i] = positions[i] + k2_pos[i] * (dt / 2)
        temp_vel[i] = velocities[i] + k2_vel[i] * (dt / 2)
    
    k3_pos, k3_vel = rk4_derivative_multiscale(
        temp_pos, temp_vel, masses, areas,
        body_positions, body_masses, material_types, scale
    )
    
    # k4
    for i in prange(N):
        temp_pos[i] = positions[i] + k3_pos[i] * dt
        temp_vel[i] = velocities[i] + k3_vel[i] * dt
    
    k4_pos, k4_vel = rk4_derivative_multiscale(
        temp_pos, temp_vel, masses, areas,
        body_positions, body_masses, material_types, scale
    )
    
    # Update
    for i in prange(N):
        positions[i] += (dt / 6) * (k1_pos[i] + 2*k2_pos[i] + 2*k3_pos[i] + k4_pos[i])
        velocities[i] += (dt / 6) * (k1_vel[i] + 2*k2_vel[i] + 2*k3_vel[i] + k4_vel[i])


@njit(parallel=True)
def update_ablation_multiscale(positions, velocities, masses, radii, areas,
                               densities, material_types, dt):
    """
    Update mass loss from ablation for all particles.
    
    Args:
        positions: (N, 3) positions from Earth center
        velocities: (N, 3) velocities
        masses: (N,) masses (modified in-place)
        radii: (N,) radii (modified in-place)
        areas: (N,) areas (modified in-place)
        densities: (N,) material densities
        material_types: (N,) material types
        dt: Timestep (s)
    
    Returns alive: (N,) boolean array
    """
    N = masses.shape[0]
    alive = np.ones(N, dtype=np.bool_)
    
    for i in prange(N):
        # Calculate altitude
        r = np.sqrt(positions[i, 0]**2 + positions[i, 1]**2 + positions[i, 2]**2)
        altitude = r - R_EARTH
        
        # Only ablate if in atmosphere and moving fast
        if altitude < 150e3:
            dm_dt = ablation_rate(velocities[i], altitude, areas[i], 
                                masses[i], material_types[i])
            dm = dm_dt * dt
            
            masses[i] -= dm
            
            # Check if burned up
            if masses[i] < 1e-8:
                masses[i] = 0.0
                radii[i] = 0.0
                areas[i] = 0.0
                alive[i] = False
            else:
                # Update geometry with constant density
                radii[i] = (3.0 * masses[i] / (4.0 * np.pi * densities[i])) ** (1.0/3.0)
                areas[i] = np.pi * radii[i] * radii[i]
    
    return alive





def orbital_velocity(altitude, central_mass=M_EARTH):
    # Circular orbital velocity 
    r = R_EARTH + altitude
    return np.sqrt(G * central_mass / r)


def escape_velocity(altitude, central_mass=M_EARTH):
    # Escape velocity from altitude 
    r = R_EARTH + altitude
    return np.sqrt(2 * G * central_mass / r)


def moon_position(time_seconds):
    # Calculate Moon position at given time.
    # Simplified circular orbit in XY plane.
    
    """
    Args:
        time_seconds: Time since epoch (s)
    
    Returns 3D position vector (m)
    """
    
    # Moon orbital period: ~27.3 days
    period = 27.3 * 24 * 3600
    omega = 2 * np.pi / period
    
    theta = omega * time_seconds
    
    return np.array([
        MOON_ORBIT * np.cos(theta),
        MOON_ORBIT * np.sin(theta),
        0.0
    ])


def sun_position(time_seconds):
    """
    Sun position (Earth orbits Sun, but we're in Earth frame).
    So Sun appears to orbit Earth.
    
    Args:
        time_seconds: Time since epoch (s)
    
    Returns 3D position vector (m)
    """
    # Earth orbital period: 365.25 days
    period = 365.25 * 24 * 3600
    omega = 2 * np.pi / period
    
    theta = omega * time_seconds
    
    # Sun appears to move in Earth's frame
    return np.array([
        -SUN_DISTANCE * np.cos(theta),
        -SUN_DISTANCE * np.sin(theta),
        0.0
    ])