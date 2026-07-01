#include <Wire.h>

#define MPU_ADDR      0x68 // I2C address of the MPU-6050
#define ACCEL_XOUT_H  0x3B // Register address for accelerometer data

// Conversion constant: MPU6050 full-scale ±2g => 16384 LSB/g
// We convert to cm/s²: 1g = 9.8 m/s² = 980 cm/s²
const float CONV_FACTOR = 9.8 * 100.0 / 16384.0;

void setup() {
  Wire.begin(); // Initialize I2C
  Serial.begin(115200); // Initialize serial comm at 115200 baud
  delay(100);

// Wake up MPU6050 (it starts in sleep mode)
 Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0x00); // Set to zero (wakes up the sensor)
  Wire.endTransmission(true);
}

void loop() {
  int16_t rawAx, rawAy, rawAz;
  readRawAccel(rawAx, rawAy, rawAz);

// Convert raw values to cm/s²
   float ax = rawAx * CONV_FACTOR;
   float ay = rawAy * CONV_FACTOR;
   float az = rawAz * CONV_FACTOR;

// Output as comma-separated values: X,Y,Z
  Serial.print(ax, 2);
  Serial.print(',');
  Serial.print(ay, 2);
  Serial.print(',');
  Serial.println(az, 2);

  delay(10); // 100 Hz sampling rate
}

// Reads raw accelerometer data from MPU-6050
void readRawAccel(int16_t &ax, int16_t &ay, int16_t &az) {
   Wire.beginTransmission(MPU_ADDR);
   Wire.write(ACCEL_XOUT_H);// Start at ACCEL_XOUT_H register
   Wire.endTransmission(false);
   Wire.requestFrom(MPU_ADDR, 6, true);

// Combine high and low bytes for each axis
   ax = (Wire.read() << 8) | Wire.read();
   ay = (Wire.read() << 8) | Wire.read();
   az = (Wire.read() << 8) | Wire.read();
}