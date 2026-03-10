import os
from gpiozero import LED

# Globals to prevent "Pin busy" errors on RPi
_drill_led = None
_mill_led = None

def check_machine_runtime(drill_limit=3600, mill_limit=5000, drill_pin=17, mill_pin=27, logger=None):
    global _drill_led, _mill_led
    
    # Helper to handle logging
    def log(msg):
        if logger:
            logger(msg)
        else:
            print(msg)
    
    # Configuration Mapping
    configs = {
        "drill": {"file": "drillcount.txt", "pin": drill_pin, "limit": drill_limit, "led": _drill_led},
        "mill": {"file": "millcount.txt", "pin": mill_pin, "limit": mill_limit, "led": _mill_led}
    }

    # 1. Initialize LEDs only once
    try:
        if _drill_led is None:
            _drill_led = LED(configs["drill"]["pin"])
            configs["drill"]["led"] = _drill_led
        if _mill_led is None:
            _mill_led = LED(configs["mill"]["pin"])
            configs["mill"]["led"] = _mill_led
    except Exception as e:
        log(f"GPIO Initialization Error: {e}")
        return

    # 2. Process both Drill and Mill
    for tool, data in configs.items():
        file_path = data["file"]
        threshold = data["limit"]
        led = data["led"]

        # Check if file exists; if not, create it with 0
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("0")
            log(f"Created missing file: {file_path}")

        try:
            with open(file_path, "r+") as f:
                content = f.read().strip()
                
                if not content:
                    f.write("0")
                    current_count = 0.0
                else:
                    current_count = float(content)

            # Check threshold and trigger LED
            if current_count > threshold:
                log(f"MAINTENANCE REQUIRED ({tool.upper()}): {current_count:.1f}s used.")
                led.on()
            else:
                led.off()

        except Exception as e:
            log(f"Error checking {tool} maintenance: {e}")