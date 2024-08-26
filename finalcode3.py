import serial
import time
import MySQLdb
import RPi.GPIO as GPIO
from picamera2 import Picamera2

# Initialize the camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

# Open serial ports
ser_arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)  # Arduino Nano
ser_uno = serial.Serial('/dev/ttyACM1', 9600, timeout=1)  # Arduino Uno
time.sleep(2)  # Wait for the serial connections to initialize

# Connect to MySQL database
db = MySQLdb.connect(
    host="127.0.0.1",
    user="Gaddo",  # Replace with your MySQL username
    passwd="12345",  # Replace with your MySQL password
    db="sensor_data"  # Replace with your database name
)

cursor = db.cursor()

# Default values for pump control
pump_interval = 3600  # 1 hour
pump_duration = 600   # 10 minutes

# Function to measure the distance using the ultrasonic sensor
def get_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = time.time()
    pulse_end = time.time()

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    return distance

while True:
    # Capture a picture every 30 seconds
    picam2.capture_file("/var/www/html/images/test.jpg")
    time.sleep(30)

    # Read sensor data from Arduino Nano
    if ser_arduino.in_waiting > 0:
        try:
            # Read lines from Arduino Nano
            line = ser_arduino.readline().decode('utf-8').rstrip()
            print(f"Received line: {line}")

            if "Humidity:" in line:
                humidity = float(line.split(": ")[1])

                line = ser_arduino.readline().decode('utf-8').rstrip()
                avgTempC = float(line.split(": ")[1])

                line = ser_arduino.readline().decode('utf-8').rstrip()
                avgTempF = float(line.split(": ")[1])

                line = ser_arduino.readline().decode('utf-8').rstrip()
                luxvalue = float(line.split(": ")[1])

                # Get the ultrasonic sensor reading
                water_level = get_distance()

                # Insert data into the MySQL database, including water level
                sql = "INSERT INTO DHT11 (humidity, temperature, luxvalue, waterlevel, pump_interval, pump_duration) VALUES (%s, %s, %s, %s, %s, %s)"
                val = (humidity, avgTempC, luxvalue, water_level, pump_interval, pump_duration)
                cursor.execute(sql, val)
                db.commit()

                print(f"Inserted into DB: Humidity={humidity}, Temperature={avgTempC}°C, LuxValue={luxvalue}, Water Level={water_level} cm")

                # Send the lux setpoint to Arduino Nano
                cursor.execute("SELECT setpoints FROM luxvalues ORDER BY datetime DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    lux_setpoint = result[0]
                    print(f"Sending lux setpoint to Arduino Nano: {lux_setpoint}")
                    ser_arduino.write(f"{lux_setpoint}\n".encode())

                # Fetch the latest pump control parameters from the database
                cursor.execute("SELECT pump_interval, pump_duration FROM DHT11 ORDER BY datetime DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    pump_interval = result[0]
                    pump_duration = result[1]
                    print(f"Using new pump settings: Interval={pump_interval}, Duration={pump_duration}")

                # Send pump control parameters to Arduino Uno
                pump_control_data = f"{pump_interval},{pump_duration}\n"
                print(f"Sending pump control data to Arduino Uno: {pump_control_data}")
                ser_uno.write(pump_control_data.encode())

        except Exception as e:
            print(f"Error: {e}")

    time.sleep(1)

ser_arduino.close()
ser_uno.close()
db.close()
GPIO.cleanup()
