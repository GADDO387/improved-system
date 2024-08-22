import smbus2
import time
import MySQLdb
import RPi.GPIO as GPIO

# Setup for ultrasonic sensor
TRIG = 23  # Example GPIO pin for TRIG
ECHO = 24  # Example GPIO pin for ECHO

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# I2C Setup
ARDUINO_ADDR = 0x04  # I2C address of the Arduino
bus = smbus2.SMBus(1)  # 1 indicates /dev/i2c-1

def get_distance():
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

# Connect to MySQL database
db = MySQLdb.connect(
    host="172.20.10.4",
    user="Gaddo",  # Replace with your MySQL username
    passwd="12345",  # Replace with your MySQL password
    db="sensor_data"  # Replace with your database name
)

cursor = db.cursor()

while True:
    try:
        # Request sensor data from Arduino
        data = bus.read_i2c_block_data(ARDUINO_ADDR, 0, 12)  # Read 12 bytes (4 bytes for each float)
        
        # Convert the byte data back to float
        humidity = float.from_bytes(data[0:4], byteorder='little')
        avgTempC = float.from_bytes(data[4:8], byteorder='little')
        luxvalue = float.from_bytes(data[8:12], byteorder='little')
        
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
            bus.write_byte(ARDUINO_ADDR, lux_setpoint)
            print(f"Sending lux setpoint to Arduino: {lux_setpoint}")

        # Sleep to avoid overwhelming the I2C bus
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")

db.close()
GPIO.cleanup()
