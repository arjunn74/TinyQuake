# Tiny Quake (Quakr)

A DIY real-time seismograph lovingly called Quakr built on an Arduino and an MPU-6050 accelerometer/gyroscope module. The Arduino streams live acceleration data over serial, and a Python script visualizes it as a live-updating amplitude trace, converts it into an approximate intensity score, and logs every reading to CSV.

## How It Works

1. **`no_lib_seismo.ino`** runs on the Arduino. It talks to the MPU-6050 over I2C (no external libraries required — registers are read directly via `Wire`), converts the raw accelerometer readings to cm/s², and prints them over serial as comma-separated `X,Y,Z` values at ~100 Hz.
2. **`SEISMOGRAPHY_FINAL_copy_2.py`** runs on a computer connected to the Arduino. It:
   - Auto-detects the Arduino's serial port
   - Auto-calibrates a resting baseline (averages ambient noise for a few seconds at startup)
   - Applies a low-pass filter to smooth out electrical noise
   - Computes a derived intensity value (VII — see below) from the filtered amplitude
   - Plots the live amplitude signal in a Matplotlib animation
   - Logs every reading (raw X/Y/Z, filtered amplitude, VII) to a CSV file
   - Prints console alerts when the vibration crosses different intensity thresholds

## Hardware Requirements

- Arduino (Uno, Nano, or similar)
- MPU-6050 accelerometer/gyroscope module
- USB cable for serial communication
- A stable, vibration-isolated surface for best results (bonus points for felt padding / decoupling from the table legs)

### Wiring (MPU-6050 → Arduino, I2C)

| MPU-6050 | Arduino |
|----------|---------|
| VCC      | 5V (or 3.3V, depending on your board) |
| GND      | GND |
| SCL      | SCL (A5 on Uno) |
| SDA      | SDA (A4 on Uno) |

## Software Requirements

**Arduino side:**
- Arduino IDE
- `Wire` library (built-in, no extra installs needed)

**Python side:**
- Python 3.8+
- Dependencies:
  ```bash
  pip install pyserial numpy matplotlib
  ```

## Setup & Usage

1. Wire the MPU-6050 to the Arduino as described above.
2. Open `no_lib_seismo.ino` in the Arduino IDE, select your board and port, and upload it.
3. Close the Arduino IDE's Serial Monitor (it will lock the port and block the Python script).
4. Run the Python script:
   ```bash
   python SEISMOGRAPHY_FINAL_copy_2.py
   ```
5. The script will attempt to auto-detect the correct serial port. If it can't confidently identify the Arduino, it lists all available ports and falls back to the first one — check the console output and edit `SERIAL_PORT` manually if needed.
6. **Do not touch the table** during the ~10-second calibration phase at startup — the script averages ambient noise to establish a resting baseline (zero offset) for each axis.
7. Once calibration finishes, a live plot window opens showing the filtered vibration amplitude in real time. Console messages will report intensity changes as they happen.
8. Close the plot window to stop the script. All readings are saved to `seismic_data_log.csv` in the working directory.

## Output

### Live Plot
A scrolling amplitude trace (last 100 samples) updated at ~100 FPS.

### CSV Log (`seismic_data_log.csv`)
Each row contains:

| Column | Description |
|---|---|
| `Timestamp` | Time of reading (HH:MM:SS.microseconds) |
| `X_Raw`, `Y_Raw`, `Z_Raw` | Raw accelerometer readings (cm/s²) after offset removal |
| `Filtered_Amplitude` | Low-pass filtered vibration magnitude |
| `VII_Magnitude` | Derived intensity score (see below) |

> Note: the script currently opens the CSV in append mode, so re-running it will add to the existing log rather than overwrite it.

### Intensity Score (VII)
"VII" is a rough, self-defined intensity scale inspired by the Modified Mercalli Intensity scale ( this is an approximation). It's computed as:

```
VII = log10(filtered_amplitude / NOISE_FLOOR) * SCALE_FACTOR
```

The script buckets VII into rough categories (resting, minor, tremor, strong, severe, extreme) and prints an alert only when the category changes, to avoid flooding the console.

## Calibration Notes

Two constants in the Python script may need tuning for your specific sensor/setup:

- `NOISE_FLOOR` — set slightly above your sensor's resting `filtered_amplitude` value to avoid false positives from electrical noise. Check the console during a quiet period to find your baseline.
- `SCALE_FACTOR` — stretches the intensity output to a roughly 1–10 scale. Adjust to taste.

## Project Structure

```
.
├── no_lib_seismo.ino              # Arduino firmware (MPU-6050 → serial)
├── SEISMOGRAPHY_FINAL_copy_2.py   # Python live-plotting & logging script
├── seismic_data_log.csv           # Generated at runtime (readings log)
└── README.md
```

## Contact

Arjun Mishra - arjun.xynapse@gmail.com
Project Link - 
