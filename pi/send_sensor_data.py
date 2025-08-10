import requests
from PiicoDev_BME280 import PiicoDev_BME280
from time import sleep

# This script sends temperature, pressure, and humidity data from a BME280 sensor to a Flask server running on an EC2 instance.


# Initialize the BME280 sensor
sensor = PiicoDev_BME280()
SERVER_URL = 'http://<YOUR-EC2-SERVER-IP>:5000/sensor'  # Add your server IP here


# Loop to send BMP280 sensor data
while True:
    try:
        temperature, pressure, humidity = sensor.values()
        data = {
            'temperature': temperature,
            'pressure': pressure,
            'humidity': humidity
        }
        response = requests.post(SERVER_URL, json=data)
        print(f"Sent: {data}, Response: {response.status_code}")
    except Exception as e:
        print("Error:", e)

    sleep(10)
