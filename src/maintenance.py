import os
import sys

# Optional: GPIO import for Raspberry Pi usage
try:
    # from gpiozero import LED
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

_drill_led = None
_mill_led = None

def get_storage_path(filename):
    """
    Returns a persistent path for data files.
    - If running as EXE: Saves to C:/Users/Name/.pico_cnc_data/
    - If running as Script: Saves to a folder named 'data' in your project.
    """
    if getattr(sys, 'frozen', False):
        # Path for Compiled EXE
        base = os.path.join(os.path.expanduser("~"), ".pico_cnc_data")
    else:
        # Path for Python Script (creates a 'data' folder in your project root)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base = os.path.join(project_root, "data")
    
    if not os.path.exists(base):
        os.makedirs(base)
    return os.path.join(base, filename)

# --- SHARED FILE PATHS ---
DRILL_FILE = get_storage_path("drillcount.txt")
MILL_FILE = get_storage_path("millcount.txt")

def reset_runtime(tool_type):
    """Call this when the user replaces a bit."""
    file_path = DRILL_FILE if tool_type == "drill" else MILL_FILE
    with open(file_path, "w", encoding='utf-8') as f:
        f.write("0")
    return True

def check_machine_runtime(drill_limit=3600, mill_limit=5000, drill_pin=17, mill_pin=27, logger=None):
    global _drill_led, _mill_led

    def log(msg):
        if logger: logger(msg)
        else: print(msg)
    
    # Initialize LEDs only if GPIO is available (Raspberry Pi context)
    if GPIO_AVAILABLE:
        try:
            if _drill_led is None:
                # _drill_led = LED(drill_pin) 
                pass
            if _mill_led is None:
                # _mill_led = LED(mill_pin)
                pass
        except Exception as e:
            log(f"GPIO Error: {e}")

    configs = {
        "drill": {"file": DRILL_FILE, "limit": drill_limit, "led": _drill_led},
        "mill": {"file": MILL_FILE, "limit": mill_limit, "led": _mill_led}
    }

    for tool, data in configs.items():
        file_path = data["file"]
        threshold = data["limit"]
        led = data["led"]

        # Ensure file exists
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding='utf-8') as f:
                f.write("0")
            log(f"Initialized storage: {os.path.basename(file_path)}")

        try:
            with open(file_path, "r", encoding='utf-8') as f:
                content = f.read().strip()
                current_count = float(content) if content else 0.0

            if current_count > threshold:
                log(f"MAINTENANCE ALERT: {tool.upper()} bit has exceeded {threshold}s of use!")
                if led: led.on()
            else:
                if led: led.off()
        except Exception as e:
            log(f"Maintenance check failed for {tool}: {e}")