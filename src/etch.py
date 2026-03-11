import serial
import serial.tools.list_ports
import time
import os
from tkinter import messagebox

# --- CONFIGURATION ---
SAFE_Z = 2.0  

def get_pico_port():
    """Scans for the Pico W or CH340 serial port."""
    available_ports = serial.tools.list_ports.comports()
    for port in available_ports:
        desc = port.description or ""
        dev = port.device or ""
        # Targets Raspberry Pi Pico, CH340, and Linux ttyACM devices
        if any(x in desc or x in dev for x in ["USB Serial", "Pico", "CH340", "ttyACM"]):
            try:
                # Test accessibility
                with serial.Serial(port.device, 115200, timeout=0.5) as test_s:
                    return port.device
            except (serial.SerialException, PermissionError):
                continue
    return None

def etch_gcode(file_path, logger=None, app_reference=None):
    def log(msg):
        print(msg)
        if logger: logger(msg)

    # --- 1. IDENTIFY TOOLING FOR DIALOGUE & LOGGING ---
    if file_path.lower().endswith("_drill.nc"):
        bit_string = "is a drill bit"
        target_file = "drillcount.txt"
        tool_label = "Drill"
    elif file_path.lower().endswith("_etch.nc"):
        bit_string = "is a milling bit"
        target_file = "millcount.txt"
        tool_label = "Mill"
    else:
        bit_string = "is appropriate for the job"
        target_file = None # We won't log maintenance for unknown files
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
            # --- INITIALIZE ---
            s.write(b"\r\n\r\n")
            time.sleep(1)
            s.reset_input_buffer() 

            log("Unlocking machine...")
            s.write(b"$X\n") # $X is the universal GRBL command to unlock
            time.sleep(0.2)

            log(f"Lifting to Safe Height ({SAFE_Z}mm)...")
            s.write(f"G90\nG0 Z{SAFE_Z}\n".encode()) 
            while 'ok' not in s.readline().decode('utf-8').strip(): pass

            # --- DYNAMIC USER START ---
            messagebox.showinfo("Before we start..", 
                                f"1. Make sure that the mounted bit {bit_string}.\n"
                                "2. Turn ON spindle.\n"
                                "3. Click OK to start timer and etching.")

            # START TIMER
            start_time = time.time()
            log("Timer started.")

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
                            # 'replace' handles the .docx/binary garbage safely
                            res = raw_res.decode('utf-8', errors='replace').strip()
                            
                            if 'ok' in res: 
                                break # Move to the next line in the file
                                
                            elif 'error' in res.lower() or 'ALARM' in res:
                                log(f"MACHINE ERROR: {res}")
                                return # Kill the etch process for safety
                                
                        except Exception as e:
                            log(f"Serial Read Error: {e}")
                            return # Exit if the USB is unplugged

            # --- WAIT FOR IDLE ---
            log("Job streamed. Waiting for physical completion...")
            while True:
                try:
                    s.write(b"?") 
                    # Added 'replace' and 'strip' here for consistency
                    status = s.readline().decode('utf-8', errors='replace').strip()
                    if 'Idle' in status:
                        break
                    time.sleep(0.5)
                except Exception as e:
                    log(f"Status Check Error: {e}")
                    break

            # STOP TIMER
            end_time = time.time()
            duration = end_time - start_time
            log(f"Job finished in {duration:.2f} seconds.")

            # --- PERSISTENCE LOGIC ---
            if target_file:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                count_file_path = os.path.join(script_dir, target_file)
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

                # Trigger Maintenance LED                             #USE THIS ONLY ON RPI 4B
                try:
                    from maintenance import check_machine_runtime
                    check_machine_runtime(logger=log) 
                except Exception as e:
                    log(f"Maintenance LED Check Error: {e}")
            else:
                log("Unknown file type. Duration not added to maintenance.")
    except Exception as e:
        log(f"General Error: {e}")

    finally:
        # Clear the reference when done
        if app_reference:
            app_reference.active_serial = None
    log("--- Process Complete ---")