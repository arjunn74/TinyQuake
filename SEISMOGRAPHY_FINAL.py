

import serial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import math
import csv
from datetime import datetime

# --- HARDWARE CONFIGURATION ---
SERIAL_PORT = 'COM6' # Change this to the correct port for your Arduino
BAUD_RATE = 115200   # Change this to match the baud rate set in your Arduino sketch   
print("If this crashes, it's a feature.")
# Connect to the Arduino
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0) 
    time.sleep(2)
    ser.reset_input_buffer()   # Flush ALL stale startup bytes
    print("[+] Connected.Negotiating peace treaty with Earth's crust...")
except Exception as e:
    print(f"[!] {e}"); exit()

# --- CSV SETUP ---
csv_file = open('seismic_data_log.csv', mode='a', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Timestamp", "X_Raw", "Y_Raw", "Z_Raw", "Filtered_Amplitude", "VII_Magnitude"])

# --- GRAPH SETUP ---
MAX_POINTS = 100
data_buffer = np.zeros(MAX_POINTS)

fig, ax = plt.subplots()
fig.canvas.manager.set_window_title("Live Digital Seismograph")
ax.set_title("Arjun's Real-Time Seismic Amplitude & VII")
ax.set_xlabel("Time (frames)")
ax.set_ylabel("Vibration Amplitude")
ax.set_ylim(0, 1500) 

ax.text(0.5, 0.5, 'ARJUN MISHRA',  #Watermark text
        transform=ax.transAxes, 
        fontsize=40,            
        color='gray',           
        alpha=0.25,             
        ha='center',           
        va='center',          
        rotation=30,          
        zorder=0) 


plot_line, = ax.plot(data_buffer, color='red', linewidth=1.5)

# --- CALIBRATION VARIABLES ---
# AVERAGE RESTING VALUES
# STEP 1: Don't touch the table
# STEP 2: I said dont touch the table!!
# STEP 3: STOP TOUCHING THE TABLE!! (I mean it)
# personally, I calibrated using state-of-the-art technology
# (a ruler, a notebook, and optimism)
X_OFFSET = 79.10 
Y_OFFSET = 23.82
Z_OFFSET = 988.31
filtered_amplitude = 0  
_serial_buf = ""

def get_live_data():
    
    global _serial_buf
    if ser.in_waiting:
        _serial_buf += ser.read(ser.in_waiting).decode('utf-8', errors='ignore') 

    lines = _serial_buf.split('\n')
    
    _serial_buf = lines[-1]
    
    for line in reversed(lines[:-1]):
        line = line.strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) == 3:
            try:
                return float(parts[0]), float(parts[1]), float(parts[2])
            except ValueError:
                continue
    
    return None

# --- INTENSITY CALIBRATION ---
# Tune this to slightly above whatever your 'filtered_amplitude' rests at.
# In my case, it rests at about 12.5, so I set it to 15.0 to avoid false positives.
NOISE_FLOOR = 15.0  

# This stretches the final number to fit a 1-10 Richter scale. 
SCALE_FACTOR = 3.5  

def update(frame):
    global data_buffer
    global filtered_amplitude

    raw_data = get_live_data()

    if raw_data:
        x_raw, y_raw, z_raw = raw_data

        # Remove resting offsets
        dx = x_raw - X_OFFSET
        dy = y_raw - Y_OFFSET
        dz = z_raw - Z_OFFSET

        raw_amplitude = np.sqrt(dx**2 + dy**2 + dz**2) 

        # Low-pass filter to filter out electronic noise and miniscule vibrations
        filtered_amplitude = (0.7 * filtered_amplitude) + (0.3 * raw_amplitude)

        # Move each value in the buffer one step to the left and add the new filtered amplitude to the end
        data_buffer[:-1] = data_buffer[1:]
        data_buffer[-1] = filtered_amplitude


        if filtered_amplitude <= NOISE_FLOOR:
            VII = 0.0  # Absolute zero while resting
        else:
            # log10(1) = 0, so that when it exceeds noise floor, it will go up smoothly
            VII = math.log10(filtered_amplitude / NOISE_FLOOR) * SCALE_FACTOR
        
        csv_writer.writerow([
            datetime.now().strftime("%H:%M:%S.%f"),
            x_raw, y_raw, z_raw,
            filtered_amplitude, VII
        ])

        # --------------------------------------------------
        # Alert the Hoomans or they will diee
        # --------------------------------------------------
        if VII >= 7 :
            print(f"☠️ DANGER! VERY DESTRUCTIVE QUAKE! VII: {VII:.1f} - TAKE COVER IMMEDIATELY! (Amp={filtered_amplitude:.0f})")
        elif VII >= 5.0:
            print(f"🚨 DANGER! DESTRUCTIVE QUAKE! VII: {VII:.1f} - TAKE COVER IMMEDIATELY! (Amp={filtered_amplitude:.0f})")
            print(f"🚨 Earth is no longer asking politely.")
        elif VII >= 3.0:
            print(f"⚠️ STRONG SHAKING! VII: {VII:.1f} - BRACE YOURSELF! (Amp={filtered_amplitude:.0f})")
            print(f"⚠️ Earth is now expressing opinions.")
        elif VII >= 1.0:
            print(f"👀 Tremor Detected. VII: {VII:.1f} (Amp={filtered_amplitude:.0f})")
            print(f"👀 Tremor Detected. Earth has sent a friend request.")
        elif VII > 0:
            print(f"😊 Minor Vibration. VII: {VII:.1f} - No need to worry! (Amp={filtered_amplitude:.0f})") 
        elif VII < 0:
            print(f"Achievement: How did we get here?. Negatiev VII!! VII: {VII:.1f} ")
        elif filtered_amplitude > 5000:
            print("🌏 DONT HURT ME GODZILLA...please?🙏")           
        elif filtered_amplitude > 8000:
            print("🚀 D-Did you just launch a r-rocket?")
        elif filtered_amplitude > 12000:
            print("📞 Calling NASA for a second opinion...")
        plot_line.set_ydata(data_buffer) 
    
    return plot_line, 
# ==========================================================

# Start the live animation loop (Running at the speed of 100 FPS) 
# # this graph runs faster than my homework progress 👀
# I should really be completing my homework
ani = animation.FuncAnimation(fig, update, interval=10, blit=True, cache_frame_data=False)


plt.show()

# --- CLEANUP ---

csv_file.close()
ser.close()
print("[---] Data saved to seismic_data_log.csv. Connection closed. Tectonic plates will continue unsupervised. Good luck humanity.")
print("If this worked, it's innovation. If not, it's research.")