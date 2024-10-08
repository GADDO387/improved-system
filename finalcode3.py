import serial
import time
import MySQLdb
import RPi.GPIO as GPIO
from picamera2 import Picamera2, Preview

# Setup for ultrasonic sensor
TRIG = 23  # GPIO pin for TRIG
ECHO = 24  # GPIO pin for ECHO
GPIO.setwarnings(False)
# Setup for the pump relay (This won't be used for direct control anymore)
PUMP_PIN = 17  # GPIO pin connected to the relay controlling the pump
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(PUMP_PIN, GPIO.OUT)
GPIO.output(PUMP_PIN, GPIO.LOW)  # Make sure the pump is off initially

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

# Open serial port for Arduino Nano
ser_nano = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
# Open serial port for Arduino Uno (for pump control)
ser_uno = serial.Serial('/dev/ttyACM1', 9600, timeout=1)
time.sleep(2)  # Wait for the serial connection to initialize

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

# Setup camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

def capture_image():
    picam2.capture_file("/var/www/html/images/test.jpg")

while True:
    # Take a picture every 30 seconds
    capture_image()
    time.sleep(30)
    
    # Read sensor data from Arduino Nano
    if ser_nano.in_waiting > 0:
        try:
            # Read lines from Arduino
            line = ser_nano.readline().decode('utf-8').rstrip()
            print(f"Received line: {line}")
            
            if "Humidity:" in line:
                humidity = float(line.split(": ")[1])
                
                line = ser_nano.readline().decode('utf-8').rstrip()
                avgTempC = float(line.split(": ")[1])
                
                line = ser_nano.readline().decode('utf-8').rstrip()
                avgTempF = float(line.split(": ")[1])
                
                line = ser_nano.readline().decode('utf-8').rstrip()
                luxvalue = float(line.split(": ")[1])

                # Get the ultrasonic sensor reading
                water_level = get_distance()

                # Insert data into the MySQL database, including water level
                sql = "INSERT INTO DHT11 (humidity, temperature, luxvalue, waterlevel, pump_interval, pump_duration) VALUES (%s, %s, %s, %s, %s, %s)"
                val = (humidity, avgTempC, luxvalue, water_level, pump_interval, pump_duration)
                cursor.execute(sql, val)
                db.commit()

                print(f"Inserted into DB: Humidity={humidity}, Temperature={avgTempC}°C, LuxValue={luxvalue}, Water Level={water_level} cm")

                # After processing and storing the sensor data, send the lux setpoint to Arduino Nano
                cursor.execute("SELECT setpoints FROM luxvalues ORDER BY datetime DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    lux_setpoint = result[0]
                    print(f"Sending lux setpoint to Arduino: {lux_setpoint}")
                    ser_nano.write(f"{lux_setpoint}\n".encode())

                # Fetch the latest pump control parameters from the database
                cursor.execute("SELECT pump_interval, pump_duration FROM DHT11 ORDER BY datetime DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    pump_interval = result[0]
                    pump_duration = result[1]
                    print(f"Using new pump settings: Interval={pump_interval}, Duration={pump_duration}")

                # Send the pump control values to Arduino Uno
                ser_uno.write(f"interval:{pump_interval}\n".encode())
                ser_uno.write(f"duration:{pump_duration}\n".encode())

        except Exception as e:
            print(f"Error: {e}")

ser_nano.close()
ser_uno.close()
db.close()
GPIO.cleanup()
