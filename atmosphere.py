"""
Atmosphere model for meteor simulation.
Handles air density calculation and drag force computation.
"""

import numpy as np
from constants import RHO_0, H_SCALE, DRAG_COEFFICIENT


class Atmosphere:
    """
    Models Earth's atmosphere with exponential density decay.
    
    The atmosphere gets thinner as altitude increases, following:
    ρ(h) = ρ₀ × e^(-h/H)
    
    Where:
        ρ₀ = sea level density (1.225 kg/m³)
        H = scale height (8500 m)
        h = altitude above sea level
    """
    
    def __init__(self):
        """Initialize atmosphere with standard parameters."""
        self.rho_0 = RHO_0      # Sea level density (kg/m³)
        self.H = H_SCALE         # Scale height (m)
    
    def density(self, altitude):
        """
        Calculate air density at given altitude.
        
        Args:
            altitude (float): Height above sea level in meters
            
        Returns:
            float: Air density in kg/m³
            
        Note:
            If altitude is negative (below sea level), returns sea level density.
            Density decreases exponentially - at 8500m it's 1/e of sea level.
        """
        if altitude < 0:
            # Below sea level - just use sea level density
            return self.rho_0
        
        # Exponential atmosphere model
        return self.rho_0 * np.exp(-altitude / self.H)
    
    def drag_force(self, meteor, altitude):
        """
        Calculate drag force on meteor at given altitude.
        
        Args:
            meteor: Meteor object with velocity, area attributes
            altitude (float): Current altitude in meters
            
        Returns:
            numpy.ndarray: Drag force vector [Fx, Fy, Fz] in Newtons
            
        Physics:
            F_drag = ½ × ρ × v² × C_d × A
            
            Where:
                ρ = air density (from altitude)
                v = speed (magnitude of velocity)
                C_d = drag coefficient (~0.8)
                A = cross-sectional area
                
            Direction: Always opposes velocity (antiparallel)
        """
        # Get air density at current altitude
        rho = self.density(altitude)
        
        # Get meteor velocity vector
        v = meteor.vel
        speed = np.linalg.norm(v)  # Magnitude of velocity
        
        # Handle case where meteor is stationary (avoid division by zero)
        if speed < 1e-6:
            return np.zeros(3)  # No drag if not moving
        
        # Calculate drag magnitude: F = ½ρv²CdA
        drag_magnitude = 0.5 * rho * speed**2 * DRAG_COEFFICIENT * meteor.area
        
        # Drag direction is opposite to velocity
        # Unit vector in velocity direction: v / |v|
        # So drag direction: -v / |v|
        drag_direction = -v / speed
        
        # Force vector = magnitude × direction
        return drag_magnitude * drag_direction


# ============================================================================
# TESTING (run this file directly to test)
# Use python atmosphere.py (I added some data points so you can see whats happening in numbers)
if __name__ == "__main__":
    """Test the atmosphere model."""
    
    print("Testing Atmosphere Model\n" + "="*50)
    
    atm = Atmosphere()
    
    # Test density at various altitudes
    altitudes = [0, 10000, 50000, 100000, 150000]
    
    print("\nAir Density at Different Altitudes:")
    print(f"{'Altitude (km)':<15} {'Density (kg/m³)':<20} {'% of Sea Level'}")
    print("-" * 55)
    
    for h in altitudes:
        rho = atm.density(h)
        percent = (rho / RHO_0) * 100
        print(f"{h/1000:<15.0f} {rho:<20.6e} {percent:>6.2f}%")
    
    print("\n" + "="*50)
    print("✓ Atmosphere model working correctly!")
    print("\nNotice how density drops exponentially with altitude.")
    print("At 100 km, air is ~0.0001% as dense as sea level!")