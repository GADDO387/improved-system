document.addEventListener('DOMContentLoaded', function() {
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
                    const rowCount = table.rows.length;
                    for (let i = rowCount - 1; i > 0; i--) {
                        table.deleteRow(i);
                    }

                    data.forEach(item => {
                        const row = table.insertRow();
                        const idCell = row.insertCell(0);
                        const tempCell = row.insertCell(1);
                        const humidityCell = row.insertCell(2);
                        const luxvalueCell = row.insertCell(3);  // Added luxvalue column
                        const datetimeCell = row.insertCell(4);

                        idCell.textContent = item.id;
                        tempCell.textContent = item.temperature;
                        humidityCell.textContent = item.humidity;
                        luxvalueCell.textContent = item.luxvalue;  // Display luxvalue
                        datetimeCell.textContent = item.datetime;
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching sensor data:', error);
            });
    }

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
                if (waterLevelElement && data.waterlevel !== undefined) {
                    waterLevelElement.textContent = `Current Water Level: ${data.waterlevel} cm`;

                    const threshold = 100.0; 
                    if (data.waterlevel > threshold) {
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

    if (document.getElementById('dataTable')) {
        fetchSensorData();
        setInterval(fetchSensorData, 15000);
    }

    if (document.getElementById('waterLevel')) {
        fetchWaterLevel();
        setInterval(fetchWaterLevel, 15000);
    }

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

    const pumpForm = document.getElementById('pumpForm');
    if (pumpForm) {
        pumpForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const interval = document.getElementById('interval').value;
            const duration = document.getElementById('duration').value;

            fetch('combined_script.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `interval=${encodeURIComponent(interval)}&duration=${encodeURIComponent(duration)}`
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
