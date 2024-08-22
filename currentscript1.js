document.addEventListener('DOMContentLoaded', function() {
    // Function to fetch and display sensor data
    function fetchSensorData() {
        fetch('combined_script.php')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const table = document.getElementById('dataTable');
                if (table) {
                    // Clear existing table rows except the header
                    const rowCount = table.rows.length;
                    for (let i = rowCount - 1; i > 0; i--) {
                        table.deleteRow(i);
                    }

                    data.forEach(item => {
                        const row = table.insertRow();
                        const idCell = row.insertCell(0);
                        const tempCell = row.insertCell(1);
                        const humidityCell = row.insertCell(2);
                        const luxvalueCell = row.insertCell(3);
                        const datetimeCell = row.insertCell(4);

                        idCell.textContent = item.id;
                        tempCell.textContent = item.temperature;
                        humidityCell.textContent = item.humidity;
                        luxvalueCell.textContent = item.luxvalue;
                        datetimeCell.textContent = item.datetime;
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching sensor data:', error);
            });
    }

    // Function to fetch and display the latest water level
    function fetchWaterLevel() {
        fetch('combined_script.php?action=getWaterLevel')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const waterLevelElement = document.getElementById('waterLevel');
                if (waterLevelElement && data.water_level !== undefined) {
                    waterLevelElement.textContent = `Current Water Level: ${data.water_level} cm`;

                    // Check if the water level is below the threshold
                    const threshold = 10.0; // Example threshold
                    if (data.water_level < threshold) {
                        const warningElement = document.getElementById('waterLevelWarning');
                        warningElement.textContent = "Water level is low, refill is needed!";
                        warningElement.style.color = "red";
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching water level:', error);
            });
    }

    // Call the fetchSensorData function if the dataTable exists
    if (document.getElementById('dataTable')) {
        fetchSensorData();
        // Set up interval to fetch sensor data every 45 seconds
        setInterval(fetchSensorData, 45000);
    }

    // Call the fetchWaterLevel function for pump_operation page
    if (document.getElementById('waterLevel')) {
        fetchWaterLevel();
        // Set up interval to fetch water level every 45 seconds
        setInterval(fetchWaterLevel, 45000);
    }

    // Light Control form submission
    const luxForm = document.getElementById('luxForm');
    if (luxForm) {
        luxForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const lux = document.getElementById('lux').value;

            fetch('combined_script.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `lux=${encodeURIComponent(lux)}`
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                document.getElementById('response').textContent = data.message;
            })
            .catch(error => {
                document.getElementById('response').textContent = 'Error: ' + error.message;
            });
        });
    }
});
