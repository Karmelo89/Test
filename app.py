from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import random
import time
import threading
import math
from datetime import datetime, timedelta
import json
import os

# Import our custom modules
from data_manager import DataManager, RealDataCollector, CSVDataImporter
from prediction_engine import SolarPredictionEngine, WeatherPredictor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'solar_monitor_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize data management and prediction components
data_manager = DataManager()
data_collector = RealDataCollector(data_manager)
prediction_engine = SolarPredictionEngine(data_manager)
weather_predictor = WeatherPredictor()
csv_importer = CSVDataImporter(data_manager)

# Global variables to store solar panel data
solar_data = {
    'power': 0,
    'voltage': 0,
    'current': 0,
    'temperature': 0,
    'efficiency': 0,
    'daily_energy': 0,
    'status': 'Normal',
    'timestamp': datetime.now().isoformat(),
    'source': 'Simulation'
}

# Historical data storage (in-memory for simplicity)
historical_data = []

# Configuration for real data sources
DATA_SOURCES_CONFIG = {
    'api_sources': [],
    'serial_sources': [],
    'modbus_sources': [],
    'weather_config': {},
    'use_real_data': False
}

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
    
    # Load configuration if exists
    try:
        if os.path.exists('data_sources_config.json'):
            with open('data_sources_config.json', 'r') as f:
                DATA_SOURCES_CONFIG.update(json.load(f))
    except Exception as e:
        print(f"Failed to load data sources config: {e}")
    
    # Try to load existing ML model
    prediction_engine.load_models()
    
    while True:
        # Try to collect real data if configured
        real_data_collected = False
        
        if DATA_SOURCES_CONFIG.get('use_real_data'):
            try:
                # Collect from API sources
                for api_config in DATA_SOURCES_CONFIG.get('api_sources', []):
                    data = data_collector.collect_from_api(api_config)
                    if data:
                        solar_data.update(data)
                        real_data_collected = True
                        break
                
                # Collect from serial sources
                if not real_data_collected:
                    for serial_config in DATA_SOURCES_CONFIG.get('serial_sources', []):
                        data = data_collector.collect_from_serial(serial_config)
                        if data:
                            solar_data.update(data)
                            real_data_collected = True
                            break
                
                # Collect weather data periodically (every 15 minutes)
                if time.time() % 900 < 5:  # Every 15 minutes
                    weather_config = DATA_SOURCES_CONFIG.get('weather_config')
                    if weather_config:
                        data_collector.collect_weather_data(weather_config)
                        
            except Exception as e:
                print(f"Error collecting real data: {e}")
        
        # Fallback to simulation if no real data
        if not real_data_collected:
            solar_data = simulate_solar_data()
        
        # Save data to database
        data_manager.save_reading(solar_data)
        
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

@app.route('/config')
def config():
    """Configuration page"""
    return render_template('config.html')

@app.route('/api/current')
def get_current_data():
    """API endpoint to get current solar data"""
    return jsonify(solar_data)

@app.route('/api/historical')
def get_historical_data():
    """API endpoint to get historical data for charts"""
    hours = request.args.get('hours', 24, type=int)
    
    # Try to get real historical data from database
    db_data = data_manager.get_historical_data(hours=hours)
    
    if db_data:
        return jsonify(db_data)
    else:
        # Fallback to in-memory data
        return jsonify(historical_data)

@app.route('/api/predictions')
def get_predictions():
    """API endpoint to get power predictions"""
    hours_ahead = request.args.get('hours', 24, type=int)
    
    try:
        predictions = prediction_engine.predict_power(hours_ahead=hours_ahead)
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-prediction')
def get_daily_prediction():
    """API endpoint to get daily energy prediction"""
    date_str = request.args.get('date')
    
    try:
        if date_str:
            date = datetime.fromisoformat(date_str).date()
        else:
            date = None
            
        prediction = prediction_engine.predict_daily_energy(date=date)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/train-model', methods=['POST'])
def train_prediction_model():
    """API endpoint to train the prediction model"""
    try:
        target = request.json.get('target', 'power')
        results = prediction_engine.train_models(target=target)
        return jsonify({
            'status': 'success',
            'results': {k: {
                'mae': v['mae'],
                'mse': v['mse'],
                'r2': v['r2']
            } for k, v in results.items()}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-csv', methods=['POST'])
def import_csv_data():
    """API endpoint to import CSV data"""
    try:
        file_path = request.json.get('file_path')
        mapping = request.json.get('mapping', {})
        
        count = csv_importer.import_csv(file_path, mapping)
        return jsonify({
            'status': 'success',
            'imported_records': count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-sources', methods=['GET', 'POST'])
def manage_data_sources():
    """API endpoint to manage real data sources"""
    if request.method == 'GET':
        return jsonify(DATA_SOURCES_CONFIG)
    
    elif request.method == 'POST':
        try:
            config = request.json
            DATA_SOURCES_CONFIG.update(config)
            
            # Save configuration
            with open('data_sources_config.json', 'w') as f:
                json.dump(DATA_SOURCES_CONFIG, f, indent=2)
            
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/collect-real-data', methods=['POST'])
def collect_real_data():
    """API endpoint to manually trigger real data collection"""
    try:
        results = {}
        
        # Collect from API sources
        for api_config in DATA_SOURCES_CONFIG.get('api_sources', []):
            data = data_collector.collect_from_api(api_config)
            if data:
                results[f"api_{api_config['name']}"] = 'success'
            else:
                results[f"api_{api_config['name']}"] = 'failed'
        
        # Collect from serial sources
        for serial_config in DATA_SOURCES_CONFIG.get('serial_sources', []):
            data = data_collector.collect_from_serial(serial_config)
            if data:
                results[f"serial_{serial_config['name']}"] = 'success'
            else:
                results[f"serial_{serial_config['name']}"] = 'failed'
        
        # Collect weather data
        weather_config = DATA_SOURCES_CONFIG.get('weather_config')
        if weather_config:
            data = data_collector.collect_weather_data(weather_config)
            if data:
                results['weather'] = 'success'
            else:
                results['weather'] = 'failed'
        
        return jsonify({
            'status': 'completed',
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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