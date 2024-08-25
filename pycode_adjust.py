import serial
import time
import MySQLdb
import RPi.GPIO as GPIO
import threading

# Setup GPIO
GPIO.setwarnings(False)  # Ignore GPIO warnings
TRIG = 23  # GPIO pin for TRIG
ECHO = 24  # GPIO pin for ECHO
PUMP_PIN = 17  # GPIO pin connected to the relay controlling the pump

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(PUMP_PIN, GPIO.OUT)
GPIO.output(PUMP_PIN, GPIO.LOW)  # Ensure pump is off initially

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

# Function to control the pump operation in a separate thread
def operate_pump(pump_duration):
    GPIO.output(PUMP_PIN, GPIO.HIGH)
    print("Pump ON")
    time.sleep(pump_duration)
    GPIO.output(PUMP_PIN, GPIO.LOW)
    print("Pump OFF")

# Function to initiate pump control based on interval and duration
def control_pump(pump_interval, pump_duration):
    global last_pump_time, pump_thread

    current_time = time.time()

    if last_pump_time is None or current_time - last_pump_time >= pump_interval:
        # If there is no active pump thread or the last one has finished, start a new one
        if not pump_thread or not pump_thread.is_alive():
            pump_thread = threading.Thread(target=operate_pump, args=(pump_duration,))
            pump_thread.start()
            last_pump_time = current_time
            print(f"Pump thread started at {time.ctime()}")

# Open serial port
try:
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    time.sleep(2)  # Wait for serial connection to initialize
    print("Serial connection established.")
except Exception as e:
    print(f"Error opening serial port: {e}")
    exit(1)

# Connect to MySQL database
try:
    db = MySQLdb.connect(
        host="127.0.0.1",
        user="Gaddo",
        passwd="12345",
        db="sensor_data"
    )
    cursor = db.cursor()
    print("Connected to MySQL database.")
except Exception as e:
    print(f"Error connecting to database: {e}")
    exit(1)

last_pump_time = None
pump_thread = None  # Initialize the pump thread

while True:
    print("Starting loop iteration...")  # Debug print

    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8').rstrip()
            print(f"Received line: {line}")
            
            if "Humidity:" in line:
                humidity = float(line.split(": ")[1])
                
                line = ser.readline().decode('utf-8').rstrip()
                avgTempC = float(line.split(": ")[1])
                
                line = ser.readline().decode('utf-8').rstrip()
                avgTempF = float(line.split(": ")[1])
                
                line = ser.readline().decode('utf-8').rstrip()
                luxvalue = float(line.split(": ")[1])

                water_level = get_distance()
                print(f"Water level: {water_level} cm")

                sql = "INSERT INTO DHT11 (humidity, temperature, luxvalue, waterlevel) VALUES (%s, %s, %s, %s)"
                val = (humidity, avgTempC, luxvalue, water_level)
                cursor.execute(sql, val)
                db.commit()
                print("Data inserted into DB")

                cursor.execute("SELECT setpoints FROM luxvalues ORDER BY datetime DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    lux_setpoint = result[0]
                    print(f"Sending lux setpoint to Arduino: {lux_setpoint}")
                    ser.write(f"{lux_setpoint}\n".encode())

                cursor.execute("SELECT pump_interval, pump_duration FROM DHT11 ORDER BY datetime DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    pump_interval = result[0]
                    pump_duration = result[1]
                    control_pump(pump_interval, pump_duration)
        except Exception as e:
            print(f"Error: {e}")

    print("Ending loop iteration...")  # Debug print
    time.sleep(1)

ser.close()
db.close()
GPIO.cleanup()

