import serial
import time
import MySQLdb

# Open serial port
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)  # Wait for the serial connection to initialize

# Connect to MySQL database
db = MySQLdb.connect(
    host="172.20.10.4",
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
                
                # Insert data into the MySQL database
                sql = "INSERT INTO DHT11 (humidity, temperature, luxvalue) VALUES (%s, %s, %s)"
                val = (humidity, avgTempC, luxvalue)
                cursor.execute(sql, val)
                db.commit()

                print(f"Inserted into DB: Humidity={humidity}, Temperature={avgTempC}°C, {avgTempF}°F, LuxValue={luxvalue}")

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
