import time
import MySQLdb
import RPi.GPIO as GPIO

# Setup for ultrasonic sensor
TRIG = 23  # GPIO pin for TRIG
ECHO = 24  # GPIO pin for ECHO

# Setup for the pump relay
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

# Open serial port
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)  # Wait for the serial connection to initialize

# Connect to MySQL database
db = MySQLdb.connect(
    host="127.0.0.1",
    user="Gaddo",  # Replace with your MySQL username
    passwd="12345",  # Replace with your MySQL password
    db="sensor_data"  # Replace with your database name
)

cursor = db.cursor()

# Initialize variables to track the previous pump settings
previous_pump_interval = None
previous_pump_duration = None
last_pump_time = None  # To track the last time the pump was operated

# Function to control the pump
def control_pump(pump_interval, pump_duration):
    global last_pump_time

    if last_pump_time is None or time.time() - last_pump_time >= pump_interval:
        # Turn on the pump
        GPIO.output(PUMP_PIN, GPIO.HIGH)
        print("Pump ON")
        time.sleep(pump_duration)  # Run the pump for the specified duration

        # Turn off the pump
        GPIO.output(PUMP_PIN, GPIO.LOW)
        print("Pump OFF")

        # Update the last pump time
        last_pump_time = time.time()

while True:
    # Read sensor data from Arduino
    if ser.in_waiting > 0:
        try:
            # Read lines from Arduino
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

                # Get the ultrasonic sensor reading
                water_level = get_distance()

                # Insert data into the MySQL database, including water level
                sql = "INSERT INTO DHT11 (humidity, temperature, luxvalue, waterlevel) VALUES (%s, %s, %s, %s)"
                val = (humidity, avgTempC, luxvalue, water_level)
                cursor.execute(sql, val)
                db.commit()

                print(f"Inserted into DB: Humidity={humidity}, Temperature={avgTempC}°C, LuxValue={luxvalue}, Water Level={water_level} cm")

                # After processing and storing the sensor data, send the lux setpoint to Arduino
                cursor.execute("SELECT setpoints FROM luxvalues ORDER BY datetime DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    lux_setpoint = result[0]
                    print(f"Sending lux setpoint to Arduino: {lux_setpoint}")
                    ser.write(f"{lux_setpoint}\n".encode())

                # Fetch the latest pump control parameters
                cursor.execute("SELECT pump_interval, pump_duration FROM DHT11 ORDER BY datetime DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    pump_interval = result[0]
                    pump_duration = result[1]

                    # Control the pump using the non-blocking timing function
                    control_pump(pump_interval, pump_duration)

        except Exception as e:
            print(f"Error: {e}")

    # Wait for 5 seconds before the next loop iteration
    time.sleep(5)

ser.close()
db.close()
GPIO.cleanup()
