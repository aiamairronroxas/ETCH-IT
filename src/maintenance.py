import os
#from gpiozero import LED # Uncomment on Pi

_drill_led = None
_mill_led = None

# Get the directory where THIS script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRILL_FILE = os.path.join(BASE_DIR, "drillcount.txt")
MILL_FILE = os.path.join(BASE_DIR, "millcount.txt")

def check_machine_runtime(drill_limit=3600, mill_limit=5000, drill_pin=17, mill_pin=27, logger=None):
    global _drill_led, _mill_led

    def log(msg):
        if logger: logger(msg)
        else: print(msg)
    
    # 1. Initialize LEDs globally first
    try:
        if _drill_led is None:
            #_drill_led = LED(drill_pin) # Uncomment on Pi
            pass
        if _mill_led is None:
            #_mill_led = LED(mill_pin)   # Uncomment on Pi
            pass
    except Exception as e:
        log(f"GPIO Initialization Error: {e}")
        return

    # 2. Define configs AFTER initialization so they pick up the new LED objects
    configs = {
        "drill": {
            "file": DRILL_FILE, 
            "limit": drill_limit, 
            "led": _drill_led
        },
        "mill": {
            "file": MILL_FILE, 
            "limit": mill_limit, 
            "led": _mill_led
        }
    }

    # 3. Process
    for tool, data in configs.items():
        file_path = data["file"]
        threshold = data["limit"]
        led = data["led"]

        # Ensure file exists
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("0")
            log(f"Created missing file: {file_path}")

        try:
            with open(file_path, "r") as f:
                content = f.read().strip()
                current_count = float(content) if content else 0.0

            if current_count > threshold:
                log(f"MAINTENANCE REQUIRED ({tool.upper()}): {current_count:.1f}s used.")
                if led: led.on() # Only calls .on() if LED was successfully initialized
                print(f"{tool}: you're cooked")
            else:
                if led: led.off()
                print(f"{tool}: you're cool")

        except Exception as e:
            log(f"Error checking {tool} maintenance: {e}")