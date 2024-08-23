import serial
import time
import MySQLdb
import RPi.GPIO as GPIO

# Setup for ultrasonic sensor
TRIG = 23  # Example GPIO pin for TRIG
ECHO = 24  # Example GPIO pin for ECHO

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

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
                sql = "INSERT INTO DHT11 (humidity, temperature, luxvalue, water_level) VALUES (%s, %s, %s, %s)"
                val = (humidity, avgTempC, luxvalue, water_level)
                cursor.execute(sql, val)
                db.commit()

                print(f"Inserted into DB: Humidity={humidity}, Temperature={avgTempC}°C, {avgTempF}°F, LuxValue={luxvalue}, Water Level={water_level} cm")

                # After processing and storing the sensor data, send the lux setpoint to Arduino
                cursor.execute("SELECT setpoints FROM luxvalues ORDER BY datetime DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    lux_setpoint = result[0]
                    print(f"Sending lux setpoint to Arduino: {lux_setpoint}")
                    ser.write(f"{lux_setpoint}\n".encode())

                # Sleep to avoid overwhelming the serial port
                time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")

ser.close()
db.close()
GPIO.cleanup()
