"""
should implement

- Glowing trails with temperature-based colors
- Size changes during ablation (visible in real-time)
- Full particle tracks
- Multiple particle types with different visual properties
"""

import numpy as np
from pathlib import Path


class UltimateOVITOWriter:
    """
    Particle types:
    1 = Active meteor/object (bright, full size)
    2 = Trail ghost (fading, colored by age)
    3 = Burned up particle (dim, small)
    4 = Massive body marker (Earth, Moon, Sun)
    """
    
    def __init__(self, filename, trail_length=30, track_mode='smart'):
        """
        Initialize enhanced writer.
        
        Args:
            filename: Output file path
            trail_length: Number of historical positions for trails
            track_mode: 'none', 'smart' (only fast-moving), 'all'
        """
        self.filename = Path(filename)
        self.trail_length = trail_length
        self.track_mode = track_mode
        self.frame_number = 0
        
        # History per particle for trails
        self.particle_history = {}  # particle_id -> list of (pos, vel, radius, temp)
        
        # Track particles that burned up (keep as ghosts)
        self.burned_particles = {}  # particle_id -> last known state
        
        # Create/clear output file
        with open(self.filename, 'w') as f:
            pass
    
    def write_frame(self, positions, velocities, masses, radii,
                   timestep=None, box_bounds=None, body_markers=None,
                   material_types=None):
        """
        Write enhanced frame with all visual effects.
        
        Args:
            positions: (N, 3) positions (m)
            velocities: (N, 3) velocities (m/s)
            masses: (N,) masses (kg)
            radii: (N,) radii (m)
            timestep: Current timestep
            box_bounds: Box boundaries or None for auto
            body_markers: List of (name, position, radius, mass) for planets/moons
            material_types: (N,) material type indices
        """
        N = len(positions)
        
        # Calculate derived properties
        speeds = np.sqrt(np.sum(velocities**2, axis=1))
        kinetic_energies = 0.5 * masses * speeds**2
        
        # Enhanced temperature calculation
        # - Based on speed (kinetic heating)
        # - Enhanced at low altitudes (atmospheric heating)
        temperatures = np.zeros(N)
        for i in range(N):
            r = np.sqrt(positions[i, 0]**2 + positions[i, 1]**2 + positions[i, 2]**2)
            altitude = r - 6.371e6  # Earth radius
            
            # Base temperature from speed
            temp_base = speeds[i] / 1000.0
            
            # Amplify in atmosphere
            if altitude < 150e3:
                atm_factor = 1.0 + 5.0 * np.exp(-altitude / 20000.0)
                temperatures[i] = temp_base * atm_factor
            else:
                temperatures[i] = temp_base
        
        # Update particle histories
        for i in range(N):
            particle_id = i + 1
            
            if masses[i] > 0:  # Active particle
                state = (positions[i].copy(), velocities[i].copy(), 
                        radii[i], temperatures[i], speeds[i])
                
                if particle_id not in self.particle_history:
                    self.particle_history[particle_id] = []
                
                self.particle_history[particle_id].append(state)
                
                # Limit history length
                if len(self.particle_history[particle_id]) > self.trail_length:
                    self.particle_history[particle_id].pop(0)
            
            else:  # Burned up
                if particle_id not in self.burned_particles:
                    # Save last known state
                    if particle_id in self.particle_history and self.particle_history[particle_id]:
                        last_state = self.particle_history[particle_id][-1]
                        self.burned_particles[particle_id] = last_state
        
        # Auto-detect box bounds
        if box_bounds is None:
            all_positions = [positions]
            if body_markers:
                all_positions.append(np.array([m[1] for m in body_markers]))
            
            all_pos = np.vstack(all_positions)
            max_extent = np.max(np.abs(all_pos))
            max_extent = min(max_extent, 1e7)  # clamp to 10,000 km scale

            margin = max(100000, max_extent * 0.1)
            
            box_bounds = [
                [all_pos[:, 0].min() - margin, all_pos[:, 0].max() + margin],
                [all_pos[:, 1].min() - margin, all_pos[:, 1].max() + margin],
                [all_pos[:, 2].min() - margin, all_pos[:, 2].max() + margin]
            ]
        
        # Collect all particles for this frame
        all_particles = []
        next_id = 1
        
        # 1. Active particles (type 1)
        for i in range(N):
            if masses[i] > 0:
                all_particles.append({
                    'id': next_id,
                    'type': 1,  # Active
                    'x': positions[i, 0],
                    'y': positions[i, 1],
                    'z': positions[i, 2],
                    'vx': velocities[i, 0],
                    'vy': velocities[i, 1],
                    'vz': velocities[i, 2],
                    'radius': radii[i],
                    'mass': masses[i],
                    'speed': speeds[i],
                    'temperature': temperatures[i],
                    'brightness': 1.0,  # Full brightness
                    'particle_id': i + 1  # Original particle ID
                })
                next_id += 1
        
        # 2. Trail particles (type 2) - with enhanced fading
        for particle_id, history in self.particle_history.items():
            if len(history) > 1:  # Need at least 2 points for trail
                # Skip the most recent point (that's the active particle)
                for hist_idx, (pos, vel, rad, temp, speed) in enumerate(history[:-1]):
                    # Fade factor: 0 (oldest) to 1 (newest)
                    age = len(history) - hist_idx - 1
                    fade = 1.0 - (age / self.trail_length)
                    
                    # Enhanced trail properties
                    trail_radius = rad * fade * 0.5  # Shrinking trail
                    trail_temp = temp * fade  # Cooling trail
                    trail_brightness = fade * 0.7  # Fading glow
                    
                    all_particles.append({
                        'id': next_id,
                        'type': 2,  # Trail
                        'x': pos[0],
                        'y': pos[1],
                        'z': pos[2],
                        'vx': 0.0,
                        'vy': 0.0,
                        'vz': 0.0,
                        'radius': trail_radius,
                        'mass': 0.0,
                        'speed': speed * fade,
                        'temperature': trail_temp,
                        'brightness': trail_brightness,
                        'particle_id': particle_id
                    })
                    next_id += 1
        
        # 3. Burned up particles (type 3) - keep as dim ghosts
        for particle_id, (pos, vel, rad, temp, speed) in self.burned_particles.items():
            all_particles.append({
                'id': next_id,
                'type': 3,  # Burned up
                'x': pos[0],
                'y': pos[1],
                'z': pos[2],
                'vx': 0.0,
                'vy': 0.0,
                'vz': 0.0,
                'radius': rad * 0.1,  # Very small
                'mass': 0.0,
                'speed': 0.0,
                'temperature': 0.0,
                'brightness': 0.1,  # Very dim
                'particle_id': particle_id
            })
            next_id += 1
        
        # 4. Massive body markers (type 4) - Earth, Moon, Sun
        if body_markers:
            for name, position, radius, mass in body_markers:
                all_particles.append({
                    'id': next_id,
                    'type': 4,  # Body marker
                    'x': position[0],
                    'y': position[1],
                    'z': position[2],
                    'vx': 0.0,
                    'vy': 0.0,
                    'vz': 0.0,
                    'radius': radius,
                    'mass': mass,
                    'speed': 0.0,
                    'temperature': 0.0,
                    'brightness': 1.0,
                    'particle_id': 0  # Special ID for bodies
                })
                next_id += 1
        
        # Write LAMMPS dump format with enhanced properties
        with open(self.filename, 'a') as f:
            f.write(f"ITEM: TIMESTEP\n")
            f.write(f"{timestep if timestep is not None else self.frame_number}\n")
            
            f.write(f"ITEM: NUMBER OF ATOMS\n")
            f.write(f"{len(all_particles)}\n")
            
            f.write(f"ITEM: BOX BOUNDS pp pp pp\n")
            f.write(f"{box_bounds[0][0]} {box_bounds[0][1]}\n")
            f.write(f"{box_bounds[1][0]} {box_bounds[1][1]}\n")
            f.write(f"{box_bounds[2][0]} {box_bounds[2][1]}\n")
            
            # Enhanced property list for dramatic visualization
            f.write(f"ITEM: ATOMS id type x y z vx vy vz radius mass speed temperature brightness particle_id\n")
            
            for p in all_particles:
                f.write(f"{p['id']} {p['type']} "
                       f"{p['x']:.6e} {p['y']:.6e} {p['z']:.6e} "
                       f"{p['vx']:.3f} {p['vy']:.3f} {p['vz']:.3f} "
                       f"{p['radius']:.6e} {p['mass']:.6e} "
                       f"{p['speed']:.3f} {p['temperature']:.3f} "
                       f"{p['brightness']:.3f} {p['particle_id']}\n")
        
        self.frame_number += 1
    
    def finalize(self):
        """Finalize and provide visualization tips."""
        print(f"\nWrote {self.frame_number} frames to {self.filename}")


def create_writer_basic(filename):
    # moderate effects 
    return UltimateOVITOWriter(filename, trail_length=15)


def create_writer_dramatic(filename):
    # max effects
    return UltimateOVITOWriter(filename, trail_length=40)


def create_writer_minimal(filename):
    # min fx (performance)
    return UltimateOVITOWriter(filename, trail_length=5)