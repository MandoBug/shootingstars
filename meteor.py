"""
Meteor class representing a meteoroid entering Earth's atmosphere.
Tracks position, velocity, physical properties, and trail history.
"""

import numpy as np
from constants import DEFAULT_METEOR_MASS, DEFAULT_METEOR_RADIUS, MAX_TRAIL_LENGTH


class Meteor:
    """
    Represents a meteor with physical properties and dynamic state.
    
    The meteor has:
        - Position (x, y, z coordinates in meters)
        - Velocity (vx, vy, vz in m/s)
        - Physical properties (mass, radius, cross-sectional area)
        - Trail history for visualization
    """
    
    def __init__(self, position, velocity, mass=None, radius=None):
        """
        Initialize a meteor.
        
        Args:
            position: Initial position [x, y, z] in meters
                     For 2D: [x, y, 0] where y is altitude
            velocity: Initial velocity [vx, vy, vz] in m/s
                     Positive y = upward, negative y = downward
            mass: Meteor mass in kg (optional, uses default if None)
            radius: Meteor radius in meters (optional, uses default if None)
        """
        # Position and velocity as numpy arrays (easier for vector math)
        self.pos = np.array(position, dtype=float)
        self.vel = np.array(velocity, dtype=float)
        
        # Physical properties
        self.mass = mass if mass is not None else DEFAULT_METEOR_MASS
        self.radius = radius if radius is not None else DEFAULT_METEOR_RADIUS
        self.area = np.pi * self.radius**2  # Cross-sectional area (m²)
        
        # State flags
        self.alive = True   # False when meteor burns up or hits ground
        
        # Trail for visualization (list of position arrays)
        self.trail = []
        
    def get_altitude(self):
        """
        Get current altitude above Earth's surface.
        
        Returns:
            float: Altitude in meters
            
        Note:
            In 2D mode, altitude is just the y-coordinate.
            In 3D mode (later), it's distance from Earth's center minus radius.
        """
        # For now, simple 2D: altitude is y-coordinate
        return self.pos[1]
    
    def get_speed(self):
        """
        Get current speed (magnitude of velocity vector).
        
        Returns:
            float: Speed in m/s
        """
        return np.linalg.norm(self.vel)
    
    def get_temperature(self):
        """
        Estimate meteor temperature based on velocity.
        
        Returns:
            float: Approximate temperature in Kelvin
            
        Note:
            This is a rough approximation: T ≈ (v/100)² × 1000 K
            Real calculation would involve heat transfer equations.
            Used primarily for color visualization.
        """
        v = self.get_speed()
        # Rough approximation: faster = hotter
        # At 20 km/s, this gives ~40,000 K (very hot!)
        return (v / 100) ** 2 * 1000
    
    def get_color(self):
        """
        Get RGB color based on temperature (for visualization).
        
        Returns:
            tuple: (R, G, B) values from 0-255
            
        Temperature to color mapping:
            < 1000 K: Red/Orange (cool)
            1000-3000 K: Yellow/White (medium)
            > 3000 K: Blue/White (very hot)
        """
        temp = self.get_temperature()
        
        if temp < 1000:
            # Cool: reddish-orange
            return (255, 100, 0)
        elif temp < 3000:
            # Medium: yellow-white
            brightness = min(255, int(temp / 3000 * 255))
            return (255, 255, brightness)
        else:
            # Hot: blue-white
            blue = min(255, int(200 + (temp - 3000) / 10000 * 55))
            return (200, 200, blue)
    
    def update_trail(self, max_length=MAX_TRAIL_LENGTH):
        """
        Add current position to trail history.
        
        Args:
            max_length: Maximum trail length (oldest points removed)
            
        Note:
            Trail is used for visual rendering - creates the "streak"
            effect as meteor moves through atmosphere.
        """
        # Add copy of current position (not reference!)
        self.trail.append(self.pos.copy())
        
        # Remove oldest point if trail too long
        if len(self.trail) > max_length:
            self.trail.pop(0)  # Remove first (oldest) element
    
    def __str__(self):
        """String representation for debugging."""
        return (f"Meteor(altitude={self.get_altitude()/1000:.1f} km, "
                f"speed={self.get_speed()/1000:.1f} km/s, "
                f"temp={self.get_temperature():.0f} K)")


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the Meteor class."""
    
    print("Testing Meteor Class\n" + "="*50)
    
    # Create a meteor at 100 km altitude, moving at 20 km/s
    pos = [0, 100000, 0]  # 100 km altitude
    vel = [15000, -10000, 0]  # 15 km/s horizontal, 10 km/s downward
    
    meteor = Meteor(pos, vel, mass=0.01, radius=0.02)
    
    print(f"\nInitial state:")
    print(f"  Position: {meteor.pos}")
    print(f"  Velocity: {meteor.vel}")
    print(f"  Altitude: {meteor.get_altitude()/1000:.1f} km")
    print(f"  Speed: {meteor.get_speed()/1000:.1f} km/s")
    print(f"  Temperature: {meteor.get_temperature():.0f} K")
    print(f"  Color: {meteor.get_color()}")
    print(f"  Cross-sectional area: {meteor.area:.6f} m²")
    
    # Test trail
    for i in range(5):
        meteor.update_trail()
        meteor.pos += np.array([100, -50, 0])  # Move it a bit
    
    print(f"\nTrail length: {len(meteor.trail)} points")
    
    print("\n" + "="*50)
    print("✓ Meteor class working correctly!")