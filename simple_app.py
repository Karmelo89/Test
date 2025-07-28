#!/usr/bin/env python3
"""
Simple Solar Monitor - Minimal Dependencies Version
A basic solar monitoring system that works with standard Python library only.
"""

import json
import sqlite3
import threading
import time
import math
import random
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import os

class SolarMonitor:
    def __init__(self):
        self.data = {
            'power': 0,
            'voltage': 0,
            'current': 0,
            'temperature': 0,
            'efficiency': 0,
            'daily_energy': 0,
            'status': 'Normal',
            'timestamp': datetime.now().isoformat()
        }
        self.historical_data = []
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect('solar_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solar_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                power REAL,
                voltage REAL,
                current REAL,
                temperature REAL,
                efficiency REAL,
                daily_energy REAL,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def simulate_solar_data(self):
        """Simulate realistic solar panel data"""
        current_time = datetime.now()
        hour = current_time.hour
        
        # Simulate sun intensity based on time (peak at noon)
        sun_intensity = max(0, math.sin((hour - 6) * math.pi / 12)) if 6 <= hour <= 18 else 0
        
        # Add randomness for realistic fluctuation
        weather_factor = random.uniform(0.7, 1.0)
        cloud_factor = random.uniform(0.8, 1.0)
        
        base_power = 5000  # 5kW max capacity
        power = base_power * sun_intensity * weather_factor * cloud_factor
        
        # Calculate voltage and current
        base_voltage = 48
        voltage = base_voltage + random.uniform(-2, 2)
        current = power / voltage if voltage > 0 else 0
        
        # Temperature simulation
        base_temp = 25 + (sun_intensity * 20) + random.uniform(-5, 5)
        temperature = max(0, base_temp)
        
        # Efficiency
        efficiency = max(0, min(100, 95 - (temperature - 25) * 0.4))
        
        # Daily energy (simplified)
        daily_energy = power * (1/3600)
        
        # Status
        if power < 100:
            status = "Low Output"
        elif temperature > 60:
            status = "High Temperature"
        elif efficiency < 80:
            status = "Low Efficiency"
        else:
            status = "Normal"
        
        self.data = {
            'power': round(power, 2),
            'voltage': round(voltage, 2),
            'current': round(current, 2),
            'temperature': round(temperature, 1),
            'efficiency': round(efficiency, 1),
            'daily_energy': round(daily_energy, 3),
            'status': status,
            'timestamp': current_time.isoformat()
        }
        
        # Save to database
        self.save_to_database()
        
        # Store in memory (last 100 points)
        self.historical_data.append(self.data.copy())
        if len(self.historical_data) > 100:
            self.historical_data.pop(0)
    
    def save_to_database(self):
        """Save current data to database"""
        try:
            conn = sqlite3.connect('solar_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO solar_readings 
                (timestamp, power, voltage, current, temperature, efficiency, daily_energy, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.data['timestamp'], self.data['power'], self.data['voltage'],
                self.data['current'], self.data['temperature'], self.data['efficiency'],
                self.data['daily_energy'], self.data['status']
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database error: {e}")
    
    def get_historical_data(self, hours=24):
        """Get historical data from database"""
        try:
            conn = sqlite3.connect('solar_data.db')
            cursor = conn.cursor()
            since_time = datetime.now() - timedelta(hours=hours)
            cursor.execute('''
                SELECT timestamp, power, voltage, current, temperature, efficiency, daily_energy, status
                FROM solar_readings 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC LIMIT 100
            ''', (since_time.isoformat(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            columns = ['timestamp', 'power', 'voltage', 'current', 'temperature', 
                      'efficiency', 'daily_energy', 'status']
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Database error: {e}")
            return self.historical_data

class SolarHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, monitor=None, **kwargs):
        self.monitor = monitor
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)
        
        if path == '/':
            self.serve_dashboard()
        elif path == '/api/current':
            self.serve_json(self.monitor.data)
        elif path == '/api/historical':
            hours = int(query.get('hours', [24])[0])
            data = self.monitor.get_historical_data(hours)
            self.serve_json(data)
        elif path.endswith('.css'):
            self.serve_css()
        elif path.endswith('.js'):
            self.serve_js()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Solar Monitor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        .card h3 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
        }
        .card .value {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .card .unit {
            color: #888;
            font-size: 12px;
        }
        .status {
            text-align: center;
            margin: 20px 0;
        }
        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
        }
        .status-normal { background: #27ae60; }
        .status-warning { background: #f39c12; }
        .status-error { background: #e74c3c; }
        .refresh-btn {
            background: #3498db;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .last-update {
            text-align: center;
            color: #666;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌞 Solar Monitor Dashboard</h1>
            <button class="refresh-btn" onclick="updateData()">🔄 Refresh Data</button>
        </div>
        
        <div class="cards">
            <div class="card">
                <h3>Power Output</h3>
                <div class="value" id="power">0 W</div>
                <div class="unit">Current Generation</div>
            </div>
            <div class="card">
                <h3>Voltage</h3>
                <div class="value" id="voltage">0 V</div>
                <div class="unit">System Voltage</div>
            </div>
            <div class="card">
                <h3>Current</h3>
                <div class="value" id="current">0 A</div>
                <div class="unit">System Current</div>
            </div>
            <div class="card">
                <h3>Temperature</h3>
                <div class="value" id="temperature">0°C</div>
                <div class="unit">Panel Temperature</div>
            </div>
            <div class="card">
                <h3>Efficiency</h3>
                <div class="value" id="efficiency">0%</div>
                <div class="unit">System Efficiency</div>
            </div>
            <div class="card">
                <h3>Daily Energy</h3>
                <div class="value" id="energy">0 Wh</div>
                <div class="unit">Today's Total</div>
            </div>
        </div>
        
        <div class="status">
            <div class="status-badge" id="status">Normal</div>
        </div>
        
        <div class="last-update">
            Last Updated: <span id="lastUpdate">--</span>
        </div>
    </div>

    <script>
        async function updateData() {
            try {
                const response = await fetch('/api/current');
                const data = await response.json();
                
                document.getElementById('power').textContent = data.power.toLocaleString() + ' W';
                document.getElementById('voltage').textContent = data.voltage + ' V';
                document.getElementById('current').textContent = data.current.toFixed(1) + ' A';
                document.getElementById('temperature').textContent = data.temperature + '°C';
                document.getElementById('efficiency').textContent = data.efficiency + '%';
                document.getElementById('energy').textContent = data.daily_energy.toLocaleString() + ' Wh';
                
                const statusElement = document.getElementById('status');
                statusElement.textContent = data.status;
                statusElement.className = 'status-badge status-' + 
                    (data.status === 'Normal' ? 'normal' : 
                     data.status.includes('Low') || data.status.includes('High') ? 'warning' : 'error');
                
                const lastUpdate = new Date(data.timestamp).toLocaleTimeString();
                document.getElementById('lastUpdate').textContent = lastUpdate;
                
            } catch (error) {
                console.error('Error updating data:', error);
            }
        }
        
        // Update data every 3 seconds
        setInterval(updateData, 3000);
        
        // Initial load
        updateData();
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_json(self, data):
        """Serve JSON data"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def serve_css(self):
        """Serve CSS files"""
        self.send_response(404)
        self.end_headers()
    
    def serve_js(self):
        """Serve JavaScript files"""
        self.send_response(404)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to reduce logging"""
        pass

def run_data_updater(monitor):
    """Background thread to update solar data"""
    while True:
        monitor.simulate_solar_data()
        time.sleep(2)

def main():
    print("🌞 Starting Simple Solar Monitor...")
    
    # Initialize monitor
    monitor = SolarMonitor()
    
    # Start background data updater
    data_thread = threading.Thread(target=run_data_updater, args=(monitor,), daemon=True)
    data_thread.start()
    
    # Create HTTP server
    def handler(*args, **kwargs):
        SolarHTTPHandler(*args, monitor=monitor, **kwargs)
    
    server = HTTPServer(('0.0.0.0', 8000), handler)
    
    print("🚀 Solar Monitor running at:")
    print("   📊 Dashboard: http://localhost:8000")
    print("   🔌 API Current: http://localhost:8000/api/current")
    print("   📈 API Historical: http://localhost:8000/api/historical")
    print("\n💡 Features:")
    print("   ✅ Real-time solar data simulation")
    print("   ✅ SQLite database storage")
    print("   ✅ Responsive web dashboard")
    print("   ✅ RESTful API")
    print("\n🔧 To extend with real data:")
    print("   - Modify simulate_solar_data() function")
    print("   - Add serial/API data collection")
    print("   - Integrate with your solar hardware")
    print("\n📊 Starting data simulation...")
    print("   Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down Solar Monitor...")
        server.shutdown()
        print("✅ Solar Monitor stopped successfully!")

if __name__ == '__main__':
    main()