import serial
import serial.tools.list_ports
import time
from tkinter import messagebox

def get_pico_port():
    available_ports = serial.tools.list_ports.comports()
    if not available_ports:
        return None

    for port in available_ports:
        desc = port.description or ""
        dev = port.device or ""
        # Common identifiers for Pico W and CH340 drivers on Debian Trixie
        if "USB Serial" in desc or "Pico" in desc or "CH340" in desc or "ttyACM" in dev:
            try:
                # Brief check to see if the port is accessible
                test_s = serial.Serial(port.device, 115200, timeout=0.5)
                test_s.close()
                return port.device
            except (serial.SerialException, PermissionError):
                continue
    return None

def run_full_startup(logger_func):
    """
    Step-by-step initialization for ETCH-IT.
    logger_func: The self.log_message function from your App class.
    """
    logger_func("--- INITIALIZING MACHINE ---")
    
    # 1. Search for Port
    port = get_pico_port()
    if not port:
        logger_func("ERROR: Pico W not found. Check USB connection.")
        messagebox.showerror("Connection Error", "Pico W not detected on any USB port.")
        return None

    logger_func(f"Pico detected on {port}. Establishing connection...")
    
    try:
        # 2. Connect
        with serial.Serial(port, 115200, timeout=2) as ser:
            # Buffer: Allow GRBL/Pico to finish booting
            time.sleep(2) 
            ser.reset_input_buffer()
            ser.write(b"\r\n\r\n") # Wake up GRBL
            time.sleep(1)

            # 3. Home Command ($H)
            logger_func("Sending Homing Command ($H)...")
            ser.write(b"$H\n")
            
            # Wait for 'ok' (Homing can take 10-20 seconds)
            while True:
                line = ser.readline().decode().strip()
                if "ok" in line:
                    logger_func("Homing Successful. Machine Zero set.")
                    break
                if "ALARM" in line or "error" in line:
                    logger_func(f"HOMING ERROR: {line}")
                    return False

            logger_func("READY FOR SESSION.")
            return port

    except Exception as e:
        logger_func(f"CRITICAL STARTUP ERROR: {str(e)}")
        return None