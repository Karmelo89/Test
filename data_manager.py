import json
import sqlite3
import requests
import serial
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    """Manages real solar panel data from various sources and historical data storage"""
    
    def __init__(self, db_path: str = "solar_data.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for historical data storage"""
        conn = sqlite3.connect(self.db_path)
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
                irradiance REAL,
                weather_condition TEXT,
                source TEXT,
                raw_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                target_timestamp DATETIME,
                predicted_power REAL,
                predicted_energy REAL,
                confidence REAL,
                model_version TEXT,
                features TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def save_reading(self, data: Dict) -> None:
        """Save a solar reading to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO solar_readings 
            (timestamp, power, voltage, current, temperature, efficiency, daily_energy, 
             irradiance, weather_condition, source, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('timestamp', datetime.now().isoformat()),
            data.get('power', 0),
            data.get('voltage', 0),
            data.get('current', 0),
            data.get('temperature', 0),
            data.get('efficiency', 0),
            data.get('daily_energy', 0),
            data.get('irradiance', 0),
            data.get('weather_condition', 'Unknown'),
            data.get('source', 'Unknown'),
            json.dumps(data.get('raw_data', {}))
        ))
        
        conn.commit()
        conn.close()
    
    def get_historical_data(self, hours: int = 24) -> List[Dict]:
        """Retrieve historical data from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT * FROM solar_readings 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC
        ''', (since_time.isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'timestamp', 'power', 'voltage', 'current', 'temperature', 
                  'efficiency', 'daily_energy', 'irradiance', 'weather_condition', 
                  'source', 'raw_data']
        
        return [dict(zip(columns, row)) for row in rows]

class RealDataCollector:
    """Collects real solar panel data from various sources"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        
    def collect_from_api(self, api_config: Dict) -> Optional[Dict]:
        """Collect data from a REST API endpoint"""
        try:
            response = requests.get(
                api_config['url'],
                headers=api_config.get('headers', {}),
                params=api_config.get('params', {}),
                timeout=10
            )
            response.raise_for_status()
            
            raw_data = response.json()
            
            # Transform API data to standard format
            parsed_data = self._parse_api_data(raw_data, api_config.get('mapping', {}))
            parsed_data['source'] = f"API: {api_config['name']}"
            parsed_data['raw_data'] = raw_data
            
            self.data_manager.save_reading(parsed_data)
            logger.info(f"Successfully collected data from API: {api_config['name']}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Failed to collect data from API {api_config['name']}: {e}")
            return None
    
    def collect_from_serial(self, serial_config: Dict) -> Optional[Dict]:
        """Collect data from serial device (e.g., Arduino, Raspberry Pi)"""
        try:
            ser = serial.Serial(
                port=serial_config['port'],
                baudrate=serial_config.get('baudrate', 9600),
                timeout=serial_config.get('timeout', 5)
            )
            
            # Read data from serial
            raw_data = ser.readline().decode('utf-8').strip()
            ser.close()
            
            # Parse serial data (assuming JSON format)
            if raw_data:
                data = json.loads(raw_data)
                data['source'] = f"Serial: {serial_config['name']}"
                data['raw_data'] = {'serial_data': raw_data}
                
                self.data_manager.save_reading(data)
                logger.info(f"Successfully collected data from serial: {serial_config['name']}")
                return data
                
        except Exception as e:
            logger.error(f"Failed to collect data from serial {serial_config['name']}: {e}")
            return None
    
    def collect_from_modbus(self, modbus_config: Dict) -> Optional[Dict]:
        """Collect data from Modbus devices (common in industrial solar systems)"""
        try:
            from pymodbus.client.sync import ModbusTcpClient
            
            client = ModbusTcpClient(
                host=modbus_config['host'],
                port=modbus_config.get('port', 502)
            )
            
            if client.connect():
                # Read holding registers
                registers = modbus_config.get('registers', {})
                data = {}
                
                for param, reg_info in registers.items():
                    result = client.read_holding_registers(
                        reg_info['address'], 
                        reg_info.get('count', 1)
                    )
                    if not result.isError():
                        value = result.registers[0] * reg_info.get('scale', 1)
                        data[param] = value
                
                client.close()
                
                data['source'] = f"Modbus: {modbus_config['name']}"
                data['timestamp'] = datetime.now().isoformat()
                
                self.data_manager.save_reading(data)
                logger.info(f"Successfully collected data from Modbus: {modbus_config['name']}")
                return data
                
        except Exception as e:
            logger.error(f"Failed to collect data from Modbus {modbus_config['name']}: {e}")
            return None
    
    def collect_weather_data(self, weather_config: Dict) -> Optional[Dict]:
        """Collect weather data for correlation with solar performance"""
        try:
            # Example using OpenWeatherMap API
            api_key = weather_config.get('api_key')
            location = weather_config.get('location')
            
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': location,
                'appid': api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Extract relevant weather parameters
            data = {
                'temperature': weather_data['main']['temp'],
                'humidity': weather_data['main']['humidity'],
                'pressure': weather_data['main']['pressure'],
                'weather_condition': weather_data['weather'][0]['description'],
                'cloud_cover': weather_data.get('clouds', {}).get('all', 0),
                'wind_speed': weather_data.get('wind', {}).get('speed', 0),
                'source': 'Weather API',
                'timestamp': datetime.now().isoformat(),
                'raw_data': weather_data
            }
            
            # Calculate solar irradiance estimate based on weather
            data['irradiance'] = self._estimate_irradiance(data)
            
            self.data_manager.save_reading(data)
            logger.info("Successfully collected weather data")
            return data
            
        except Exception as e:
            logger.error(f"Failed to collect weather data: {e}")
            return None
    
    def _parse_api_data(self, raw_data: Dict, mapping: Dict) -> Dict:
        """Parse API data using field mapping configuration"""
        parsed = {}
        
        for standard_field, api_field in mapping.items():
            if '.' in api_field:
                # Handle nested fields
                value = raw_data
                for key in api_field.split('.'):
                    value = value.get(key, 0)
                parsed[standard_field] = value
            else:
                parsed[standard_field] = raw_data.get(api_field, 0)
        
        parsed['timestamp'] = datetime.now().isoformat()
        return parsed
    
    def _estimate_irradiance(self, weather_data: Dict) -> float:
        """Estimate solar irradiance based on weather conditions"""
        base_irradiance = 1000  # W/m² (clear sky)
        
        # Adjust for cloud cover
        cloud_factor = 1 - (weather_data.get('cloud_cover', 0) / 100) * 0.8
        
        # Adjust for weather conditions
        condition = weather_data.get('weather_condition', '').lower()
        if 'rain' in condition or 'storm' in condition:
            weather_factor = 0.2
        elif 'cloud' in condition:
            weather_factor = 0.6
        elif 'clear' in condition or 'sun' in condition:
            weather_factor = 1.0
        else:
            weather_factor = 0.7
        
        # Time of day adjustment (simplified)
        hour = datetime.now().hour
        if 6 <= hour <= 18:
            time_factor = max(0, 1 - abs(hour - 12) / 6)
        else:
            time_factor = 0
        
        estimated_irradiance = base_irradiance * cloud_factor * weather_factor * time_factor
        return max(0, estimated_irradiance)

class CSVDataImporter:
    """Import historical data from CSV files"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def import_csv(self, file_path: str, mapping: Dict) -> int:
        """Import data from CSV file with field mapping"""
        import pandas as pd
        
        try:
            df = pd.read_csv(file_path)
            imported_count = 0
            
            for _, row in df.iterrows():
                data = {}
                
                # Map CSV columns to standard fields
                for standard_field, csv_field in mapping.items():
                    if csv_field in row:
                        data[standard_field] = row[csv_field]
                
                data['source'] = f'CSV Import: {file_path}'
                
                self.data_manager.save_reading(data)
                imported_count += 1
            
            logger.info(f"Successfully imported {imported_count} records from {file_path}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import CSV {file_path}: {e}")
            return 0