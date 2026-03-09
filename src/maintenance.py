import os
from gpiozero import LED

# USE THIS ONLY ON RPI4B
# We define the LED globally or use a singleton pattern to avoid "Pin busy" errors
_warning_led = None

def check_machine_runtime(n=3600, led_pin=17):
    global _warning_led
    count_file = "count.txt"
    
    # Initialize LED only once
    if _warning_led is None:
        try:
            _warning_led = LED(led_pin)
        except Exception as e:
            print(f"GPIO Error: {e}")
            return

    if not os.path.exists(count_file):
        _warning_led.off()
        return

    try:
        with open(count_file, "r") as f:
            content = f.read().strip()
            if not content:
                _warning_led.off()
                return
            
            # Using float because our etch_gcode saves as float
            current_count = float(content)
            
            if current_count > n:
                print(f"MAINTENANCE REQUIRED: {current_count:.1f}s used.")
                _warning_led.on()
            else:
                _warning_led.off()

    except Exception as e:
        print(f"Maintenance check failed: {e}")