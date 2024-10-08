<?php
header('Content-Type: application/json');

$servername = "127.0.0.1";
$username = "Gaddo";
$password = "12345";
$dbname = "sensor_data";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die(json_encode(['error' => 'Database connection failed: ' . $conn->connect_error]));
}

// Handle GET request to fetch data
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
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

// Handle POST request to store the setpoint value in the new luxvalues table
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $lux = intval($_POST['lux']);

    if ($lux >= 0 && $lux <= 255) {
        // Insert the lux setpoint into the new table
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

// Close the database connection
$conn->close();
?>

