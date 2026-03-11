import serial
import serial.tools.list_ports
import time
import os
from tkinter import messagebox
from src.maintenance import check_machine_runtime, DRILL_FILE, MILL_FILE

# --- CONFIGURATION ---
SAFE_Z = 2.0  

def get_pico_port():
    """Scans for the Pico W or CH340 serial port."""
    available_ports = serial.tools.list_ports.comports()
    for port in available_ports:
        desc = (port.description or "").upper()
        dev = (port.device or "").upper()
        # Common identifiers for Pico and Serial-to-USB chips
        if any(x in desc or x in dev for x in ["USB SERIAL", "PICO", "CH340", "TTYACM", "CP210X"]):
            try:
                # Test if the port is actually accessible
                with serial.Serial(port.device, 115200, timeout=0.1) as test_s:
                    return port.device
            except (serial.SerialException, PermissionError):
                continue
    return None

def etch_gcode(file_path, logger=None, app_reference=None):
    def log(msg):
        print(msg)
        if logger: logger(msg)

    # --- 1. IDENTIFY TOOLING ---
    filename = os.path.basename(file_path).lower()
    if "_drill" in filename or filename.endswith(".drd") or filename.endswith(".xln"):
        count_file_path = DRILL_FILE
        tool_label = "Drill"
    else:
        # Default to Mill if not explicitly a drill file
        count_file_path = MILL_FILE
        tool_label = "Mill"

    pico_port = get_pico_port()
    if not pico_port:
        log("Error: No Pico W / CNC Controller detected.")
        messagebox.showerror("Connection Error", "Controller port not found. Check USB connection.")
        return

    try:
        with serial.Serial(pico_port, 115200, timeout=1) as s:
            if app_reference:
                app_reference.active_serial = s
            
            # Wake up GRBL / Controller
            s.write(b"\r\n\r\n")
            time.sleep(1) # Wait for initialization
            s.reset_input_buffer() 
            
            start_time = time.time()
            log(f"Starting {tool_label} job on {pico_port}...")

            with open(file_path, 'r') as f:
                for line in f:
                    # Check if user pressed "Stop" in the GUI
                    if app_reference and getattr(app_reference, 'stop_thread', False):
                        log("!!! JOB ABORTED BY USER !!!")
                        s.write(b"!") # GRBL immediate stop command
                        break

                    command = line.strip()
                    if not command or command.startswith(';'):
                        continue

                    s.write((command + '\n').encode('utf-8'))
                    
                    # Wait for 'ok' response from controller
                    while True:
                        response = s.readline().decode().strip()
                        if 'ok' in response.lower():
                            break
                        if 'error' in response.lower():
                            log(f"CNC {response} at line: {command}")
                            break

            duration = time.time() - start_time
            log(f"Job finished in {duration:.2f} seconds.")

            # --- PERSISTENCE LOGIC ---
            if count_file_path:
                current_total = 0.0
                if os.path.exists(count_file_path):
                    try:
                        with open(count_file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            current_total = float(content) if content else 0.0
                    except (ValueError, IOError):
                        current_total = 0.0

                new_total = current_total + duration
                try:
                    # Save the updated runtime
                    os.makedirs(os.path.dirname(count_file_path), exist_ok=True)
                    with open(count_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"{new_total:.2f}")
                        f.flush()
                        os.fsync(f.fileno()) 
                    
                    log(f"Runtime Updated: {new_total:.2f}s total usage.")
                    
                    # Trigger maintenance check
                    check_machine_runtime(logger=log)
                except Exception as e:
                    log(f"Maintenance Log Error: {e}")

    except serial.SerialException as e:
        log(f"Serial Connection Lost: {e}")
        messagebox.showerror("Hardware Error", "Serial connection lost during etching.")
    except Exception as e:
        log(f"Critical Error: {e}")
    finally:
        if app_reference:
            app_reference.active_serial = None
            # Reset the stop flag for the next job
            if hasattr(app_reference, 'stop_thread'):
                app_reference.stop_thread = False
        log("--- Session Closed ---")