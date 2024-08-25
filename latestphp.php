<?php
header('Content-Type: application/json');

$servername = "127.0.0.1";
$username = "Gaddo";
$password = "12345";
$dbname = "sensor_data";

$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die(json_encode(['error' => 'Database connection failed: ' . $conn->connect_error]));
}

// Handle GET requests
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (isset($_GET['action']) && $_GET['action'] === 'getWaterLevel') {
        $sql = "SELECT waterlevel FROM DHT11 ORDER BY datetime DESC LIMIT 1";
        $result = $conn->query($sql);

        if ($result->num_rows > 0) {
            $row = $result->fetch_assoc();
            echo json_encode(['waterlevel' => $row['waterlevel']]);
        } else {
            echo json_encode(['error' => 'No water level data found']);
        }
    } else {
        $sql = "SELECT id, temperature, humidity, luxvalue, datetime FROM DHT11 ORDER BY datetime DESC LIMIT 10";
        $result = $conn->query($sql);

        $data = array();
        if ($result->num_rows > 0) {
            while($row = $result->fetch_assoc()) {
                $data[] = [
                    'id' => $row['id'],
                    'temperature' => $row['temperature'],
                    'humidity' => $row['humidity'],
                    'luxvalue' => $row['luxvalue'],
                    'datetime' => $row['datetime']
                ];
            }
        }

        echo json_encode($data);
    }
}

// Handle POST requests
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['lux'])) {
        $lux = intval($_POST['lux']);
        if ($lux >= 0 && $lux <= 255) {
            $sql = "INSERT INTO luxvalues (setpoints) VALUES ($lux)";
            if ($conn->query($sql) === TRUE) {
                echo json_encode(['message' => 'Setpoints value stored successfully.']);
            } else {
                echo json_encode(['message' => 'Error: ' . $conn->error]);
            }
        } else {
            echo json_encode(['message' => 'Error: Please enter a value between 0 and 255.']);
        }
    }

    if (isset($_POST['interval']) && isset($_POST['duration'])) {
        $interval = intval($_POST['interval']);
        $duration = intval($_POST['duration']);
        
        // Update the latest entry with pump interval and duration
        $sql = "UPDATE DHT11 SET pump_interval = $interval, pump_duration = $duration ORDER BY datetime DESC LIMIT 1";

        if ($conn->query($sql) === TRUE) {
            echo json_encode(['message' => 'Pump interval and duration stored successfully.']);
        } else {
            echo json_encode(['message' => 'Error: ' . $conn->error]);
        }
    }
}

$conn->close();
?>

