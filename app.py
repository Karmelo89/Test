from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import random
import time
import threading
import math
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'solar_monitor_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables to store solar panel data
solar_data = {
    'power': 0,
    'voltage': 0,
    'current': 0,
    'temperature': 0,
    'efficiency': 0,
    'daily_energy': 0,
    'status': 'Normal',
    'timestamp': datetime.now().isoformat()
}

# Historical data storage (in-memory for simplicity)
historical_data = []

def simulate_solar_data():
    """Simulate realistic solar panel data based on time of day"""
    current_time = datetime.now()
    hour = current_time.hour
    minute = current_time.minute
    
    # Simulate sun intensity based on time (peak at noon)
    sun_intensity = max(0, math.sin((hour - 6) * math.pi / 12)) if 6 <= hour <= 18 else 0
    
    # Add some randomness for realistic fluctuation
    weather_factor = random.uniform(0.7, 1.0)
    cloud_factor = random.uniform(0.8, 1.0)
    
    base_power = 5000  # 5kW max capacity
    power = base_power * sun_intensity * weather_factor * cloud_factor
    
    # Calculate voltage and current (P = V * I)
    base_voltage = 48  # 48V system
    voltage = base_voltage + random.uniform(-2, 2)
    current = power / voltage if voltage > 0 else 0
    
    # Temperature simulation (affects efficiency)
    base_temp = 25 + (sun_intensity * 20) + random.uniform(-5, 5)
    temperature = max(0, base_temp)
    
    # Efficiency decreases with temperature
    efficiency = max(0, min(100, 95 - (temperature - 25) * 0.4))
    
    # Daily energy accumulation (simplified)
    daily_energy = power * (1/3600)  # Wh (assuming 1-second intervals)
    
    # Status determination
    if power < 100:
        status = "Low Output"
    elif temperature > 60:
        status = "High Temperature"
    elif efficiency < 80:
        status = "Low Efficiency"
    else:
        status = "Normal"
    
    return {
        'power': round(power, 2),
        'voltage': round(voltage, 2),
        'current': round(current, 2),
        'temperature': round(temperature, 1),
        'efficiency': round(efficiency, 1),
        'daily_energy': round(daily_energy, 3),
        'status': status,
        'timestamp': current_time.isoformat()
    }

def background_data_update():
    """Background thread to continuously update solar data"""
    global solar_data, historical_data
    
    while True:
        solar_data = simulate_solar_data()
        
        # Store historical data (keep last 100 points for charts)
        historical_data.append(solar_data.copy())
        if len(historical_data) > 100:
            historical_data.pop(0)
        
        # Emit data to connected clients
        socketio.emit('solar_update', solar_data)
        
        time.sleep(2)  # Update every 2 seconds

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/current')
def get_current_data():
    """API endpoint to get current solar data"""
    return jsonify(solar_data)

@app.route('/api/historical')
def get_historical_data():
    """API endpoint to get historical data for charts"""
    return jsonify(historical_data)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('solar_update', solar_data)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    # Start background data simulation thread
    data_thread = threading.Thread(target=background_data_update)
    data_thread.daemon = True
    data_thread.start()
    
    # Run the Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)