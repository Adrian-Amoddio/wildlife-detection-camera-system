# This is a Flask application that allows for receiving sensor data from a Raspberry Pi.
# The send_sensor_data.py script runs on the pi and sends temperature, pressure, and humidity data to this server, which can be accessed via a web interface or API.

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests (important for React)

latest_data = {}


@app.route('/sensor', methods=['POST'])
def receive_sensor_data():
    global latest_data
    data = request.get_json()
    latest_data = data
    print("Received sensor data:", data)
    return '', 200


@app.route('/sensor', methods=['GET'])
def get_latest_data():
    if latest_data:
        return jsonify(latest_data)
    else:
        return jsonify({'error': 'No data received yet'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

(venv) ubuntu@ip-172-31-3-78: ~/sensor-server$
