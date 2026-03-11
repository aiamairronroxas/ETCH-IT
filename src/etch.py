import serial
import serial.tools.list_ports
import time
import os
from tkinter import messagebox
# Import the shared paths and the check function
from src.maintenance import check_machine_runtime, DRILL_FILE, MILL_FILE

# --- CONFIGURATION ---
SAFE_Z = 2.0  

def get_pico_port():
    """Scans for the Pico W or CH340 serial port."""
    available_ports = serial.tools.list_ports.comports()
    for port in available_ports:
        desc = port.description or ""
        dev = port.device or ""
        if any(x in desc or x in dev for x in ["USB Serial", "Pico", "CH340", "ttyACM"]):
            try:
                with serial.Serial(port.device, 115200, timeout=0.5) as test_s:
                    return port.device
            except (serial.SerialException, PermissionError):
                continue
    return None

def etch_gcode(file_path, logger=None, app_reference=None):
    def log(msg):
        print(msg)
        if logger: logger(msg)

    # --- 1. IDENTIFY TOOLING ---
    # We use the shared paths (DRILL_FILE/MILL_FILE) directly here
    if file_path.lower().endswith("_drill.nc"):
        count_file_path = DRILL_FILE
        tool_label = "Drill"
    elif file_path.lower().endswith("_etch.nc"):
        count_file_path = MILL_FILE
        tool_label = "Mill"
    else:
        count_file_path = None
        tool_label = "Unknown"

    pico_port = get_pico_port()
    if not pico_port:
        log("Error: No Pico W detected.")
        messagebox.showerror("Connection Error", "Pico W port not found.")
        return

    try:
        with serial.Serial(pico_port, 115200, timeout=1) as s:
            if app_reference:
                app_reference.active_serial = s
            
            s.write(b"\n")
            s.reset_input_buffer() 
            
            start_time = time.time()
            log(f"Streaming {tool_label} G-code...")

            # STREAM G-CODE 
            with open(file_path, 'r') as file:
                for line in file:
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith('('): 
                        continue 
                    
                    s.write((clean_line + '\n').encode('utf-8'))
                    while True:
                        try:
                            raw_res = s.readline()
                            res = raw_res.decode('utf-8', errors='replace').strip()
                            if 'ok' in res: 
                                break 
                            elif 'error' in res.lower() or 'ALARM' in res:
                                log(f"MACHINE ERROR: {res}")
                                return 
                        except Exception as e:
                            log(f"Serial Read Error: {e}")
                            return 

            # --- WAIT FOR IDLE ---
            log("Job streamed. Waiting for physical completion...")
            while True:
                try:
                    s.write(b"?") 
                    status = s.readline().decode('utf-8', errors='replace').strip()
                    if 'Idle' in status:
                        break
                    time.sleep(0.5)
                except Exception as e:
                    log(f"Status Check Error: {e}")
                    break

            duration = time.time() - start_time
            log(f"Job finished in {duration:.2f} seconds.")

            # --- PERSISTENCE LOGIC ---
            if count_file_path:
                current_total = 0.0
                if os.path.exists(count_file_path):
                    try:
                        with open(count_file_path, 'r') as f:
                            content = f.read().strip()
                            current_total = float(content) if content else 0.0
                    except ValueError:
                        current_total = 0.0

                new_total = current_total + duration
                try:
                    with open(count_file_path, 'w') as f:
                        f.write(f"{new_total:.2f}")
                        f.flush()
                        os.fsync(f.fileno()) 
                    log(f"{tool_label} updated. Total: {new_total:.2f}s")
                except Exception as e:
                    log(f"File Save Error: {e}")

                # Trigger Maintenance Check
                try:
                    # We already imported it at the top, so we just call it
                    check_machine_runtime(logger=log) 
                except Exception as e:
                    log(f"Maintenance Check Error: {e}")
            else:
                log("Unknown file type. Duration not added to maintenance.")

    except Exception as e:
        log(f"General Error: {e}")
    finally:
        if app_reference:
            app_reference.active_serial = None
        log("--- Process Complete ---")