import gerber
from gerber.primitives import Circle
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_drill_layer(ax, file_path):
    """
    Core logic: Reads an Excellon drill file and adds red circles to an existing axis.
    """
    try:
        layer = gerber.read(file_path)
        print(f"Reading Drill File: {file_path}")
        
        for primitive in layer.primitives:
            # Check for Circle type or position attribute
            if isinstance(primitive, Circle) or hasattr(primitive, 'position'):
                pos = primitive.position
                
                try:
                    # Access diameter via primitive or aperture
                    d = primitive.diameter if hasattr(primitive, 'diameter') else primitive.aperture.diameter
                except AttributeError:
                    d = 0.8  # Default drill size
                
                hole = patches.Circle(pos, d/2, color='red', fill=True, alpha=0.9, zorder=5)
                ax.add_patch(hole)
                
        print(f"Successfully plotted {len(layer.primitives)} drill hits.")
    except Exception as e:
        print(f"Error in plot_drill_layer: {e}")

def plot_excellon(file_path):
    """
    Wrapper: Sets up the Matplotlib environment and triggers the drill plotting.
    """
    # 1. Create the Figure and Axis
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 2. Call the worker function
    plot_drill_layer(ax, file_path)
    
    plot_drill_layer(ax, file_path)
    ax.relim()        # Recalculate limits based on added patches
    ax.autoscale_view() # Adjust the view to those limits

    # 3. Finalize Plot Settings
    ax.set_aspect('equal')
    ax.set_title(f"Excellon Drill Verification: {file_path}")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    plt.grid(True, linestyle=':', alpha=0.5)
    
    # 4. Display the window
    plt.show()

# --- Simplified Call ---
plot_excellon('drill_1_16.xln')