# use to debug ovito not working stuff 

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys
from matplotlib.animation import FFMpegWriter


def load_dump(filename):
    # frames: list of dicts with particle data
    print(f"Opening {filename}")
    
    frames = []
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        if "ITEM: TIMESTEP" in lines[i]:
            timestep = int(lines[i+1])
            
            n_atoms = int(lines[i+3])
            
            # Box bounds (skip for now)
            i += 5
            
            # Skip bounds lines (3 lines)
            i += 3
            
            # Header line
            header = lines[i].strip().split()[2:]
            i += 1
            
            # Read particle data
            data = []
            for _ in range(n_atoms):
                data.append(list(map(float, lines[i].split())))
                i += 1
            
            data = np.array(data)
            
            frame = {
                'timestep': timestep,
                'data': data,
                'columns': header
            }
            
            frames.append(frame)
        else:
            i += 1
    
    print(f"Loaded {len(frames)} frames")
    return frames


def get_column(data, columns, name):
    idx = columns.index(name)
    return data[:, idx]



def plot_frame(frames, frame_idx=-1):
    #single frame 
    
    frame = frames[frame_idx]
    data = frame['data']
    cols = frame['columns']
    
    x = get_column(data, cols, 'x')
    y = get_column(data, cols, 'y')
    z = get_column(data, cols, 'z')
    speed = get_column(data, cols, 'speed')
    ptype = get_column(data, cols, 'type')
    radius = get_column(data, cols, 'radius')
    
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    
    # Scale positions
    scale = 1e-3  # meters → km
    
    # Size scaling
    sizes = np.clip(radius * 5000, 5, 200)
    
    scatter = ax.scatter(
        x * scale, y * scale, z * scale,
        c=speed,
        cmap='hot',
        s=sizes,
        alpha=0.8
    )
    
    ax.set_xlabel("X (km)")
    ax.set_ylabel("Y (km)")
    ax.set_zlabel("Z (km)")
    ax.set_title(f"Frame {frame_idx} | Particles: {len(x)}")
    
    
    plt.colorbar(scatter, label="Speed (m/s)")
    
    ax.view_init(elev=20, azim=45)
    plt.tight_layout()
    plt.show()


def animate(frames, interval=50, max_frames=None):
    max_frames = max_frames or len(frames)
    max_frames = min(max_frames, len(frames))
    
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    
    scale = 1e-3 # km
    
    ax.set_xlim(-500, 500)
    ax.set_ylim(0, 200)
    ax.set_zlim(-500, 500)
    
    ax.set_xlabel("X (km)", color='white')
    ax.set_ylabel("Y (km)", color='white')
    ax.set_zlabel("Z (km)", color='white')
    
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.tick_params(axis='z', colors='white')
    
    # transparent bg
    ax.xaxis.set_pane_color((0, 0, 0, 1)) 
    ax.yaxis.set_pane_color((0, 0, 0, 1))
    ax.zaxis.set_pane_color((0, 0, 0, 1))
    
    #ax.grid(color='gray', linestyle='--', alpha=0.5)
    
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    
    scatter = ax.scatter([], [], [], s=[])
    
    
    def update(i):
        # ax.clear()
        
        frame = frames[i]
        data = frame['data']
        cols = frame['columns']
        
        x = np.asarray(get_column(data, cols, 'x')) * scale
        y = np.asarray(get_column(data, cols, 'y')) * scale
        z = np.asarray(get_column(data, cols, 'z')) * scale
        
        speed = np.asarray(get_column(data, cols, 'speed'))
        radius = np.asarray(get_column(data, cols, 'radius'))
        
        sizes = np.clip(radius * 300, 5,50)          # not sure why this type of upscale isnt working in ovito
        
        '''
        scatter = ax.scatter(
            x * scale, y * scale, z * scale,
            c=speed,
            cmap='plasma',
            s=sizes,
            alpha=0.9
        )
        '''
        
        scatter._offsets3d = (x, y, z)
        scatter.set_sizes(sizes)
        
        if np.max(speed) > 0:
            colors = plt.cm.plasma(speed / np.max(speed))
        else:
            colors = plt.cm.plasma(speed)
        
        scatter.set_color(colors)
        ax.set_title(f"Frame {i}/{max_frames}", color='white')
        
        return scatter,
        
    anim = FuncAnimation(fig, update, frames=max_frames, interval=interval)
    
    save_gif = input("Save as gif? (y/n): ").strip().lower()
    if save_gif == 'y':
        print("Saving GIF...")
        anim.save("simulation.gif", writer="pillow", fps=10)
        print("Saved as simulation.gif")
        
    save_anim = input("Save as mp4? (y/n): ").strip().lower()
    if save_anim == 'y':
        print("Saving MP4...")
        
        writer = FFMpegWriter(fps=30, bitrate=1800)
        anim.save("simulation.mp4", writer=writer)
        
        print("Saved as simulation.mp4")
        
    plt.show()


# trajectory view

def track_particle(frames, particle_id=1):
    # tracks a single particle 
    
    xs, ys, zs = [], [], []
    
    for frame in frames:
        data = frame['data']
        cols = frame['columns']
        
        pid = get_column(data, cols, 'particle_id')
        
        mask = pid == particle_id
        if np.any(mask):
            x = get_column(data, cols, 'x')[mask][0]
            y = get_column(data, cols, 'y')[mask][0]
            z = get_column(data, cols, 'z')[mask][0]
            
            xs.append(x)
            ys.append(y)
            zs.append(z)
    
    xs = np.array(xs) * 1e-3
    ys = np.array(ys) * 1e-3
    zs = np.array(zs) * 1e-3
    
    plt.figure(figsize=(10, 6))
    plt.plot(xs, ys, label="Trajectory")
    
    plt.xlabel("Horizontal Distance (km)")
    plt.ylabel("Altitude (km)")
    plt.title(f"Particle {particle_id} trajectory")
    plt.grid(True)
    plt.legend()
    plt.show()



def main():
    
    if len(sys.argv) < 2:
        print("Usage: python view.py space.dump")
        return
    
    filename = sys.argv[1]
    frames = load_dump(filename)
    
    print("\nOptions:")
    print("1 - Show last frame")
    print("2 - Animate")
    print("3 - Track particle")
    
    choice = input("Choice: ").strip() or "1"
    
    if choice == "1":
        plot_frame(frames, -1)
    
    elif choice == "2":
        animate(frames)
    
    elif choice == "3":
        pid = int(input("Particle ID: ") or "1")
        track_particle(frames, pid)


if __name__ == "__main__":
    main()