#include <Wire.h>
#include <DFRobot_VEML7700.h>
#include <DHT.h>

#define DHTTYPE DHT11  // Define DHT sensor type
const int sensepin = 2;  // Pin connected to the DHT11 sensor

// Sensor objects
DFRobot_VEML7700 als;
DHT dht(sensepin, DHTTYPE);

// PI control variables
float setpoint = 0;  // Desired lux value
float integral = 0;  // Integral term for PI control
const float Kp = 1.0;  // Proportional gain
const float Ki = 0.1;  // Integral gain

// Variables for timing and data accumulation
unsigned long previousMillis = 0;
const unsigned long interval = 5000; // 5 seconds
const int luxInterval = 100;  // Interval between VEML7700 readings (100 ms)
const int numLuxReadings = interval / luxInterval; // Number of readings in 5 seconds

void setup() {
  // Initialize serial communication
  Serial.begin(9600);

  // Initialize DHT11 sensor
  dht.begin();

  // Initialize VEML7700 sensor
  als.begin(); 

  // Initialize PWM output pin (e.g., pin 9)
  pinMode(9, OUTPUT);

  Serial.println("Sensors Initialized.");
}

void loop() {
  // Read sensor data every 5 seconds
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    // Accumulate readings for VEML7700 (lux) over 5 seconds
    float totalLux = 0;
    for (int i = 0; i < numLuxReadings; i++) {
      float lux;
      als.getALSLux(lux);
      totalLux += lux;
      delay(luxInterval);
    }
    float avgLux = totalLux / numLuxReadings;

    // Accumulate readings for DHT11 (temperature and humidity) over 5 seconds
    float humiditySum = 0;
    float tempCSum = 0;
    float tempFSum = 0;
    int numReadings = 5;  // Take 5 readings, 1 per second
    for (int i = 0; i < numReadings; i++) {
      humiditySum += dht.readHumidity();
      tempCSum += dht.readTemperature();
      tempFSum += dht.readTemperature(true);
      delay(1000);
    }
    float avgHumidity = humiditySum / numReadings;
    float avgTempC = tempCSum / numReadings;
    float avgTempF = tempFSum / numReadings;

    // Calculate error and PI control signal
    float error = setpoint - avgLux;
    integral += error * (interval / 1000.0);  // Integral term
    float controlSignal = Kp * error + Ki * integral;
    controlSignal = constrain(controlSignal, 0, 255);  // Constrain control signal to PWM range

    // Control output based on PI control signal
    analogWrite(9, controlSignal);

    // Send the averaged data to the Raspberry Pi
    Serial.print("Humidity: ");
    Serial.println(avgHumidity);
    Serial.print("Temperature C: ");
    Serial.println(avgTempC);
    Serial.print("Temperature F: ");
    Serial.println(avgTempF);
    Serial.print("Lux: ");
    Serial.println(avgLux);

    // Reset timer
    previousMillis = currentMillis;
  }

  // Check for incoming serial data
  if (Serial.available() > 0) {
    // Read the incoming setpoint value
    setpoint = Serial.parseFloat();
    Serial.print("Lux setpoint received: ");
    Serial.println(setpoint);
  }
}
