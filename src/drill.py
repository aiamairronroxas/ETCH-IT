import gerber
from gerber.primitives import Circle
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_drill_layer(ax, file_path):
    """
    Core logic: Reads an Excellon drill file and adds red circles to an existing axis.
    """
    try:
        # 1. Open the file manually to avoid the 'rU' mode error
        with open(file_path, 'r') as f:
            content = f.read()
        # 2. Pass the string content to gerber.read
        layer = gerber.loads(content)
        
    except Exception as e:
        # Keeping this print as it only triggers if the file fails to open/parse
        print(f"Error in plot_drill_layer: {e}")
        return
    
    for primitive in layer.primitives:
            # Check for Circle type or position attribute
            if isinstance(primitive, Circle) or hasattr(primitive, 'position'):
                pos = primitive.position
                
                d = 0.5  # Default drill size
                    
                
                hole = patches.Circle(pos, d/2, color='red', fill=True, alpha=0.9, zorder=5)
                ax.add_patch(hole)
                
    # REMOVED: print(f"Successfully plotted {len(layer.primitives)} drill hits.")

def plot_excellon(file_path):
    """
    Wrapper: Sets up the Matplotlib environment and triggers the drill plotting.
    """
    # 1. Create the Figure and Axis
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 2. Call the worker function
    plot_drill_layer(ax, file_path)
    
    # Note: You have plot_drill_layer called twice in your original code.
    # I left the second call here to match your logic, but usually once is enough.
    ax.relim()           # Recalculate limits based on added patches
    ax.autoscale_view() # Adjust the view to those limits

    # 3. Finalize Plot Settings
    ax.set_aspect('equal')
    ax.set_title(f"Excellon Drill Verification: {file_path}")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    plt.grid(True, linestyle=':', alpha=0.5)
    
    # 4. Display the window
    plt.show()