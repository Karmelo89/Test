# Solar Monitor Dashboard

A comprehensive solar panel monitoring system with real-time data visualization, machine learning predictions, and multiple data source integrations.

## Features

### 🌟 Core Features
- **Real-time Monitoring**: Live solar panel data with WebSocket updates
- **Beautiful Dashboard**: Modern, responsive web interface with animated charts
- **Multiple Data Sources**: Support for APIs, Serial devices, Modbus, and CSV imports
- **Machine Learning**: Predictive analytics for power generation forecasting
- **Historical Data**: SQLite database for data storage and analysis
- **Weather Integration**: Weather data correlation for improved predictions

### 📊 Dashboard Components
- Power generation monitoring
- Voltage, current, and temperature tracking
- System efficiency calculations
- Daily energy production
- Real-time status indicators
- Interactive charts with Chart.js
- 24-hour power predictions

### 🔌 Data Sources Supported
- **REST APIs**: SolarEdge, Enphase, and custom solar APIs
- **Serial Devices**: Arduino, Raspberry Pi, and other microcontrollers
- **Modbus**: Industrial solar inverters and monitoring systems
- **CSV Import**: Historical data from files
- **Weather APIs**: OpenWeatherMap integration
- **Simulation**: Built-in realistic solar data simulation

### 🤖 Machine Learning Features
- Multiple ML algorithms (Random Forest, Gradient Boosting, Linear Regression)
- Feature engineering with time-series analysis
- Weather-based predictions
- Model training and evaluation
- Confidence scoring for predictions
- Automated model selection

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd solar-monitor
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Access the dashboard**
   - Main Dashboard: http://localhost:5000
   - Configuration: http://localhost:5000/config

## Configuration

### Data Sources Setup

1. **Navigate to Settings**: Click the ⚙️ Settings button in the dashboard
2. **Configure Data Sources**: Add your solar panel data sources
3. **Enable Real Data**: Check "Use Real Data Sources"
4. **Save Configuration**: Click "Save Configuration"

### API Sources Example

```json
{
  "name": "SolarEdge API",
  "url": "https://monitoringapi.solaredge.com/site/{site_id}/currentPowerFlow.json",
  "headers": {
    "Authorization": "Bearer YOUR_API_KEY"
  },
  "mapping": {
    "power": "siteCurrentPowerFlow.PV.currentPower",
    "voltage": "siteCurrentPowerFlow.GRID.voltage"
  }
}
```

### Serial Device Setup

For Arduino or similar devices:

```json
{
  "name": "Arduino Solar Monitor",
  "port": "/dev/ttyUSB0",
  "baudrate": 9600,
  "timeout": 5
}
```

See `example_configs/arduino_code_example.ino` for Arduino code.

### Weather Integration

Get an API key from [OpenWeatherMap](https://openweathermap.org/api):

```json
{
  "api_key": "your_openweather_api_key",
  "location": "San Francisco, CA, US"
}
```

## Machine Learning

### Training Models

1. **Collect Data**: Ensure you have historical data (at least 30 days recommended)
2. **Go to Settings**: Navigate to the Machine Learning section
3. **Select Target**: Choose what to predict (Power, Efficiency, Daily Energy)
4. **Train Model**: Click "Train Model" and wait for completion
5. **Generate Predictions**: Click "Generate Predictions" to create forecasts

### Supported Algorithms

- **Linear Regression**: Fast, interpretable baseline
- **Random Forest**: Robust ensemble method
- **Gradient Boosting**: High-accuracy ensemble method

### Features Used

- Time-based features (hour, day of year, seasonality)
- Weather data (temperature, irradiance, cloud cover)
- Lag features (previous power values)
- Rolling averages
- Interaction features

## Data Import

### CSV Import

1. **Prepare CSV**: Ensure your CSV has timestamp and solar data columns
2. **Create Mapping**: Define how CSV columns map to standard fields
3. **Import**: Use the CSV import feature in settings

Example mapping:
```json
{
  "power": "power_watts",
  "voltage": "voltage_volts",
  "current": "current_amps",
  "temperature": "temp_celsius",
  "timestamp": "datetime"
}
```

## API Endpoints

### Data Endpoints
- `GET /api/current` - Get current solar data
- `GET /api/historical?hours=24` - Get historical data
- `GET /api/predictions?hours=24` - Get power predictions
- `GET /api/daily-prediction?date=2024-01-01` - Get daily energy prediction

### Configuration Endpoints
- `GET /api/data-sources` - Get data source configuration
- `POST /api/data-sources` - Update data source configuration
- `POST /api/collect-real-data` - Manually trigger data collection
- `POST /api/import-csv` - Import CSV data
- `POST /api/train-model` - Train ML model

## Getting Started with Real Data

### Option 1: Arduino/ESP32 Setup
1. Wire voltage and current sensors to your solar panel
2. Upload the example Arduino code (`example_configs/arduino_code_example.ino`)
3. Connect via USB and configure the serial port in settings
4. Enable real data sources

### Option 2: API Integration
1. Get API credentials from your solar inverter manufacturer
2. Add API configuration in the settings page
3. Test the connection
4. Enable real data sources

### Option 3: CSV Import
1. Export historical data from your existing system
2. Use the CSV import feature to load historical data
3. Train ML models on your historical data

## Running the System

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py

# Access the dashboard
# Open http://localhost:5000 in your browser
```

The system will start with simulated data. To use real data:
1. Go to http://localhost:5000/config
2. Configure your data sources
3. Enable "Use Real Data Sources"
4. Save the configuration

## Support

For support and questions:
- Check the example configurations in `example_configs/`
- Review the API documentation above
- Check the console logs for error messages

This system provides a complete solar monitoring solution with modern web technologies, machine learning predictions, and support for various data sources!