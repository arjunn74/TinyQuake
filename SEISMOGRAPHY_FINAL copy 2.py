import serial
import serial.tools.list_ports
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import math
import csv
from datetime import datetime


BAUD_RATE = 115200   
CALIBRATION_SECONDS = 10  

print("If this crashes, it's a feature.")

# port finder ->
def find_arduino_port():
   #scans for arduino port,if not found falls back to first port
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("[!] No serial ports found. Is the Arduino plugged in?")
        exit()

    keywords = ["arduino", "ch340", "usb-serial", "usb serial", "wch.cn", "cp210", "ftdi"]

    for port in ports:
        desc = f"{port.description} {port.manufacturer or ''}".lower()
        if any(k in desc for k in keywords):
            print(f"[+] Found likely Arduino on {port.device} ({port.description})")
            return port.device

    print("[!] Couldn't confidently identify an Arduino. Available ports:")
    for port in ports:
        print(f"    {port.device} - {port.description}")
    fallback = ports[0].device
    print(f"[!] Falling back to first available port: {fallback}")
    return fallback


SERIAL_PORT = find_arduino_port()

# Connect to the Arduino
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
    time.sleep(2)
    ser.reset_input_buffer()   
    print(f"[+] Connected on {SERIAL_PORT}. Negotiating peace treaty with Earth's crust...")
except Exception as e:
    print(f"[!] {e}"); exit()

#record data for later analysis
#def record_data_to_csv():
    #with open('seismic_data_log.csv', mode='w', newline='') as csv_file:
        #csv_writer = csv.writer(csv_file)
        #csv_writer.writerow(["Timestamp", "X_Raw", "Y_Raw", "Z_Raw", "Filtered_Amplitude", "VII_Magnitude"])
        #print("[+] CSV file created: seismic_data_log.csv")
#record_data_to_csv()        
csv_file = open('seismic_data_log.csv', mode='a', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Timestamp", "X_Raw", "Y_Raw", "Z_Raw", "Filtered_Amplitude", "VII_Magnitude"])


MAX_POINTS = 100
data_buffer = np.zeros(MAX_POINTS)

fig, ax = plt.subplots()
fig.canvas.manager.set_window_title("Live Digital Seismograph")
ax.set_title("Arjun's Real-Time Seismic Amplitude & VII")
ax.set_xlabel("Time (frames)")
ax.set_ylabel("Vibration Amplitude")
ax.set_ylim(-100, 1500)

ax.text(0.5, 0.5, 'ARJUN MISHRA',  # Watermark text
        transform=ax.transAxes,
        fontsize=40,
        color='gray',
        alpha=0.25,
        ha='center',
        va='center',
        rotation=30,
        zorder=0)

plot_line, = ax.plot(data_buffer, color='red', linewidth=1.5)

# --- SERIAL READ HELPER ---
_serial_buf = ""

def read_serial_lines():
    """
    Reads whatever is available on the serial port and returns a list of
    complete (X, Y, Z) float tuples parsed since the last call, oldest first.
    """
    global _serial_buf
    if ser.in_waiting:
        _serial_buf += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')

    lines = _serial_buf.split('\n')
    _serial_buf = lines[-1]

    results = []
    for line in lines[:-1]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) == 3:
            try:
                results.append((float(parts[0]), float(parts[1]), float(parts[2])))
            except ValueError:
                continue
    return results


def get_live_data():
    """Returns the most recent (x, y, z) reading, or None if nothing new arrived."""
    lines = read_serial_lines()
    return lines[-1] if lines else None


# --- AUTO-CALIBRATION ---
# STEP 1: Don't touch the table
# STEP 2: I said dont touch the table!!
# STEP 3: STOP TOUCHING THE TABLE!! (I mean it)
# No more ruler-and-optimism calibration — the script now averages
# CALIBRATION_SECONDS worth of readings itself.
def auto_calibrate(duration=CALIBRATION_SECONDS):
    print(f"[*] Calibrating for {duration} seconds. DO NOT TOUCH THE TABLE.")
    xs, ys, zs = [], [], []
    start = time.time()
    last_print = -1

    while time.time() - start < duration:
        for x, y, z in read_serial_lines():
            xs.append(x)
            ys.append(y)
            zs.append(z)

        remaining = int(duration - (time.time() - start))
        if remaining != last_print:
            print(f"    ...{remaining}s remaining ({len(xs)} samples so far)")
            last_print = remaining

        time.sleep(0.02)

    if not xs:
        print("[!] No data received during calibration — check wiring/port. "
              "Falling back to zero offsets.")
        return 0.0, 0.0, 0.0

    x_offset = float(np.mean(xs))
    y_offset = float(np.mean(ys))
    z_offset = float(np.mean(zs))
    print(f"[+] Calibration complete. Offsets: X={x_offset:.2f}, "
          f"Y={y_offset:.2f}, Z={z_offset:.2f} (n={len(xs)} samples)")
    return x_offset, y_offset, z_offset


X_OFFSET, Y_OFFSET, Z_OFFSET = auto_calibrate()

filtered_amplitude = 0
last_category = None  # Tracks the last printed VII category so we don't spam the console

def classify_vii(VII):
    """Buckets a VII value into a category label used to decide whether to print."""
    if VII >= 7:
        return "extreme"
    elif VII >= 5.0:
        return "severe"
    elif VII >= 3.0:
        return "strong"
    elif VII >= 1.0:
        return "tremor"
    elif VII > 0:
        return "minor"
    elif VII < 0:
        return "negative"
    else:
        return "resting"

# --- INTENSITY CALIBRATION ---
# Tune this to slightly above whatever your 'filtered_amplitude' rests at.
# In my case, it rests at about 12.5, so I set it to 15.0 to avoid false positives.
NOISE_FLOOR = 15.0

# This stretches the final number to fit a 1-10 Richter scale.
SCALE_FACTOR = 3.5

def update(frame):
    global data_buffer
    global filtered_amplitude
    global last_category

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
        # (Every reading is still logged to CSV above regardless of this.
        #  Console prints only fire when the VII category actually changes.)
        # --------------------------------------------------
        category = classify_vii(VII)
        if category != last_category:
            if category == "extreme":
                print(f"☠️ DANGER! VERY DESTRUCTIVE QUAKE! VII: {VII:.1f} - TAKE COVER IMMEDIATELY! (Amp={filtered_amplitude:.0f})")
            elif category == "severe":
                print(f"🚨 DANGER! DESTRUCTIVE QUAKE! VII: {VII:.1f} - TAKE COVER IMMEDIATELY! (Amp={filtered_amplitude:.0f})")
            elif category == "strong":
                print(f"⚠️ STRONG SHAKING! VII: {VII:.1f} - BRACE YOURSELF! (Amp={filtered_amplitude:.0f})")
            elif category == "tremor":
                print(f"👀 Tremor Detected. VII: {VII:.1f} (Amp={filtered_amplitude:.0f})")
            elif category == "minor":
                print(f"😊 Minor Vibration. VII: {VII:.1f} - No need to worry! (Amp={filtered_amplitude:.0f})")
            elif category == "negative":
                print(f"Achievement: How did we get here?. Negatiev VII!! VII: {VII:.1f} ")
            elif category == "resting":
                if filtered_amplitude > 12000:
                    print("📞 Calling NASA for a second opinion...")
                elif filtered_amplitude > 8000:
                    print("🚀 D-Did you just launch a r-rocket?")
                elif filtered_amplitude > 5000:
                    print("🌏 DONT HURT ME GODZILLA...please?🙏")

            last_category = category

        plot_line.set_ydata(data_buffer)

    return plot_line,
# ==========================================================

# Start the live animation loop (Running at the speed of 100 FPS)
# this graph runs faster than my homework progress 👀
# I should really be completing my homework
ani = animation.FuncAnimation(fig, update, interval=10, blit=True, cache_frame_data=False)

plt.show()

# --- CLEANUP ---

csv_file.close()
ser.close()
print("[---] Data saved to seismic_data_log.csv. Connection closed. Tectonic plates will continue unsupervised. Good luck humanity.")
print("If this worked, it's innovation. If not, it's research.")