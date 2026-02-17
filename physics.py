"""
Physics engine for meteor simulation.
Implements force calculations and RK4 numerical integration.
"""

import numpy as np
from constants import G, M_EARTH, R_EARTH, g


class PhysicsEngine:
    """
    Handles all physics calculations including forces and integration.
    
    Uses Runge-Kutta 4th order (RK4) method for accurate trajectory calculation.
    RK4 is more accurate than simple Euler integration by sampling the
    derivative at multiple points within each timestep.
    """
    
    def __init__(self, use_simple_gravity=True):
        """
        Initialize physics engine.
        
        Args:
            use_simple_gravity: If True, use constant g = 9.81 m/s²
                              If False, use inverse-square law F = GMm/r²
                              (Simple is fine for altitudes << Earth radius)
        """
        self.use_simple_gravity = use_simple_gravity
    
    def gravity_force(self, meteor):
        """
        Calculate gravitational force on meteor.
        
        Args:
            meteor: Meteor object
            
        Returns:
            np.ndarray: Force vector [Fx, Fy, Fz] in Newtons
        """
        if self.use_simple_gravity:
            # Simplified: constant downward force
            # Good approximation when altitude << Earth radius
            return np.array([0, -meteor.mass * g, 0])
        else:
            # Full Newton's law: F = GMm/r² pointing toward Earth center
            r_vec = meteor.pos  # Position vector from Earth center
            r = np.linalg.norm(r_vec)  # Distance from center
            
            # Force magnitude
            F_mag = G * M_EARTH * meteor.mass / r**2
            
            # Direction: toward Earth center (opposite to position vector)
            F_dir = -r_vec / r
            
            return F_mag * F_dir
    
    def net_force(self, meteor, atmosphere):
        """
        Calculate total force on meteor.
        
        Args:
            meteor: Meteor object
            atmosphere: Atmosphere object
            
        Returns:
            np.ndarray: Net force vector [Fx, Fy, Fz] in Newtons
        """
        altitude = meteor.get_altitude()
        
        # Calculate individual forces
        F_grav = self.gravity_force(meteor)
        F_drag = atmosphere.drag_force(meteor, altitude)
        
        # Vector sum (gravity pulls down, drag opposes motion)
        return F_grav + F_drag
    
    def derivative(self, state, meteor, atmosphere):
        """
        Calculate derivative of state vector for RK4.
        
        This is the key function that defines our physics!
        
        Args:
            state: Current state [x, y, z, vx, vy, vz]
            meteor: Meteor object (for mass, area, etc.)
            atmosphere: Atmosphere object
            
        Returns:
            np.ndarray: Derivative [vx, vy, vz, ax, ay, az]
                       
        Physics:
            dx/dt = vx (position changes at rate of velocity)
            dv/dt = F/m (velocity changes at rate of acceleration)
        """
        # Unpack state
        pos = state[0:3]  # [x, y, z]
        vel = state[3:6]  # [vx, vy, vz]
        
        # Create temporary meteor with this state (for force calculation)
        temp_meteor = type(meteor).__new__(type(meteor))  # Create instance
        temp_meteor.pos = pos
        temp_meteor.vel = vel
        temp_meteor.mass = meteor.mass
        temp_meteor.radius = meteor.radius
        temp_meteor.area = meteor.area
        temp_meteor.get_altitude = meteor.get_altitude
        
        # Calculate forces at this state
        F = self.net_force(temp_meteor, atmosphere)
        
        # Calculate acceleration: F = ma → a = F/m
        accel = F / meteor.mass
        
        # Derivative of state:
        # - position changes at rate velocity
        # - velocity changes at rate acceleration
        return np.concatenate([vel, accel])
    
    def rk4_step(self, meteor, atmosphere, dt):
        """
        Update meteor state using Runge-Kutta 4th order integration.
        
        This is the magic! RK4 samples the derivative at 4 points:
            k1: at the start of timestep
            k2: at midpoint using k1
            k3: at midpoint using k2
            k4: at end using k3
        Then combines them with weights (1, 2, 2, 1) / 6
        
        Args:
            meteor: Meteor object to update
            atmosphere: Atmosphere object
            dt: Timestep in seconds
            
        Note:
            This modifies meteor.pos and meteor.vel in place
        """
        # Pack current state into array
        state = np.concatenate([meteor.pos, meteor.vel])
        
        # RK4 magic: Calculate 4 slope estimates
        
        # k1: slope at current state
        k1 = self.derivative(state, meteor, atmosphere)
        
        # k2: slope at midpoint using k1 to step halfway
        k2 = self.derivative(state + k1 * dt/2, meteor, atmosphere)
        
        # k3: slope at midpoint using k2 to step halfway
        k3 = self.derivative(state + k2 * dt/2, meteor, atmosphere)
        
        # k4: slope at endpoint using k3 to step full way
        k4 = self.derivative(state + k3 * dt, meteor, atmosphere)
        
        # Weighted average: (k1 + 2*k2 + 2*k3 + k4) / 6
        # This is the key insight of RK4!
        new_state = state + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
        
        # Unpack new state back into meteor
        meteor.pos = new_state[0:3]
        meteor.vel = new_state[3:6]


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the physics engine with a simple free-fall scenario."""
    
    print("Testing Physics Engine\n" + "="*50)
    
    # Import here to avoid circular dependency
    import sys
    sys.path.append('..')
    from meteor import Meteor
    from atmosphere import Atmosphere
    
    # Create meteor at 10 km, dropped straight down
    meteor = Meteor([0, 10000, 0], [0, 0, 0], mass=1.0, radius=0.1)
    atm = Atmosphere()
    atm.rho_0 = 0  # Turn off drag for this test
    physics = PhysicsEngine()
    
    print("\nFree fall test (no drag):")
    print(f"Initial altitude: {meteor.get_altitude():.1f} m")
    
    # Simulate for 10 seconds
    dt = 0.01
    t = 0
    
    while t < 10 and meteor.get_altitude() > 0:
        physics.rk4_step(meteor, atm, dt)
        t += dt
    
    print(f"Final altitude after {t:.2f}s: {meteor.get_altitude():.1f} m")
    print(f"Final velocity: {meteor.get_speed():.1f} m/s")
    
    # Theoretical values (h = h₀ - ½gt², v = gt)
    h_theory = 10000 - 0.5 * 9.81 * t**2
    v_theory = 9.81 * t
    
    print(f"\nTheoretical altitude: {h_theory:.1f} m")
    print(f"Theoretical velocity: {v_theory:.1f} m/s")
    
    error_h = abs(meteor.get_altitude() - h_theory)
    error_v = abs(meteor.get_speed() - v_theory)
    
    print(f"\nAltitude error: {error_h:.3f} m")
    print(f"Velocity error: {error_v:.3f} m/s")
    
    if error_h < 1.0 and error_v < 1.0:
        print("\n" + "="*50)
        print("✓ RK4 integration working correctly!")
        print("  Errors are tiny - RK4 is very accurate!")
    else:
        print("\n⚠ Warning: Errors seem high")