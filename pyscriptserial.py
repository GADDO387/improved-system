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

# Serial Setup
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Update the port as needed

# Connect to MySQL database
db = MySQLdb.connect(
    host="127.0.0.1",
    user="Gaddo",  # Replace with your MySQL username
    passwd="12345",  # Replace with your MySQL password
    db="sensor_data"  # Replace with your database name
)

cursor = db.cursor()

def get_distance():
    """Measure distance using ultrasonic sensor."""
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    return distance

def read_serial_data():
    """Read sensor data from the Arduino via serial."""
    try:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').strip()
            print(f"Received data: {data}")
            return data
    except Exception as e:
        print(f"Error reading from serial: {e}")
        return None

def send_lux_setpoint(setpoint):
    """Send lux setpoint to the Arduino via serial."""
    try:
        ser.write(f"{setpoint}\n".encode('utf-8'))
        print(f"Sending lux setpoint to Arduino: {setpoint}")
    except Exception as e:
        print(f"Error sending lux setpoint: {e}")

while True:
    try:
        # Read sensor data from Arduino
        sensor_data = read_serial_data()
        if sensor_data:
            # Split the incoming data string into float values
            humidity, avgTempC, luxvalue = map(float, sensor_data.split(','))
        
            # Get the ultrasonic sensor reading
            water_level = get_distance()
        
            # Insert data into the MySQL database, including water level
            sql = "INSERT INTO DHT11 (humidity, temperature, luxvalue, water_level) VALUES (%s, %s, %s, %s)"
            val = (humidity, avgTempC, luxvalue, water_level)
            cursor.execute(sql, val)
            db.commit()

            print(f"Inserted into DB: Humidity={humidity}, Temperature={avgTempC}°C, LuxValue={luxvalue}, Water Level={water_level} cm")

            # Send the lux setpoint to the Arduino
            cursor.execute("SELECT setpoints FROM luxvalues ORDER BY datetime DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                lux_setpoint = int(result[0])
                send_lux_setpoint(lux_setpoint)

        # Sleep to avoid overwhelming the serial communication
        time.sleep(1)

    except Exception as e:
        print(f"Error: {e}")

db.close()
GPIO.cleanup()
ser.close()
