# Solar Monitor Usage Guide

## Quick Start

### Option 1: Automatic Launcher (Recommended)
```bash
python3 run_solar_monitor.py
```
This will automatically detect your system and run the appropriate version.

### Option 2: Simple Version (No Dependencies)
```bash
python3 simple_app.py
```
Runs on port 8000 with basic features.

### Option 3: Full Version (With Dependencies)
```bash
# Install dependencies first
pip install -r requirements.txt

# Run the full application
python3 app.py
```
Runs on port 5000 with all features.

## Accessing the Dashboard

### Simple Version
- **Dashboard**: http://localhost:8000
- **Current Data API**: http://localhost:8000/api/current
- **Historical Data API**: http://localhost:8000/api/historical

### Full Version
- **Main Dashboard**: http://localhost:5000
- **Configuration Page**: http://localhost:5000/config
- **Current Data API**: http://localhost:5000/api/current
- **Predictions API**: http://localhost:5000/api/predictions
- **All APIs**: See README.md for complete list

## Features Comparison

| Feature | Simple Version | Full Version |
|---------|---------------|--------------|
| Real-time Data | ✅ | ✅ |
| Web Dashboard | ✅ | ✅ |
| SQLite Database | ✅ | ✅ |
| Data Simulation | ✅ | ✅ |
| Charts/Graphs | ❌ | ✅ |
| Machine Learning | ❌ | ✅ |
| Real Data Sources | ❌ | ✅ |
| Weather Integration | ❌ | ✅ |
| CSV Import | ❌ | ✅ |
| WebSocket Updates | ❌ | ✅ |

## Adding Real Data

### For Simple Version
Edit the `simulate_solar_data()` function in `simple_app.py`:

```python
def simulate_solar_data(self):
    # Replace simulation with real sensor readings
    # Example for serial data:
    # import serial
    # ser = serial.Serial('/dev/ttyUSB0', 9600)
    # data = ser.readline().decode('utf-8')
    # parsed_data = json.loads(data)
    
    # Your real data collection code here
    pass
```

### For Full Version
1. Go to http://localhost:5000/config
2. Configure your data sources (API, Serial, etc.)
3. Enable "Use Real Data Sources"
4. Save configuration

## Example Data Sources

### Arduino Serial Data
```json
{
  "power": 2500.5,
  "voltage": 48.2,
  "current": 51.9,
  "temperature": 32.1,
  "efficiency": 94.2,
  "timestamp": "2024-01-01T12:30:00"
}
```

### SolarEdge API
```json
{
  "name": "SolarEdge",
  "url": "https://monitoringapi.solaredge.com/site/SITE_ID/currentPowerFlow.json",
  "headers": {"Authorization": "Bearer YOUR_TOKEN"},
  "mapping": {
    "power": "siteCurrentPowerFlow.PV.currentPower"
  }
}
```

## Machine Learning (Full Version Only)

1. **Collect Historical Data**: Let the system run for several days
2. **Train Model**: Go to Settings → Machine Learning → Train Model
3. **Generate Predictions**: Click "Generate Predictions"
4. **View Predictions**: See the predictions chart on the main dashboard

## Troubleshooting

### Simple Version Issues
- **Port 8000 in use**: Change port in `simple_app.py`
- **Database errors**: Check file permissions
- **No data updates**: Check console for errors

### Full Version Issues
- **Import errors**: Install dependencies with `pip install -r requirements.txt`
- **Port 5000 in use**: Change port in `app.py`
- **ML training fails**: Ensure sufficient historical data (>50 records)

### Common Issues
- **Permission denied**: Run with appropriate permissions
- **Database locked**: Stop all instances before restarting
- **Browser cache**: Clear cache or use incognito mode

## Extending the System

### Adding New Sensors
1. Modify the data collection function
2. Update the database schema if needed
3. Add new fields to the dashboard

### Custom APIs
1. Add new endpoints in the HTTP handler
2. Update the frontend to use new data
3. Test with your API client

### New Features
1. Fork the repository
2. Add your features
3. Test thoroughly
4. Submit a pull request

## System Requirements

### Minimum (Simple Version)
- Python 3.6+
- 100MB disk space
- 64MB RAM

### Recommended (Full Version)
- Python 3.8+
- 500MB disk space
- 512MB RAM
- Internet connection (for weather data)

## Data Storage

- **Database**: SQLite file `solar_data.db`
- **Configuration**: JSON file `data_sources_config.json`
- **Models**: Pickle files in `models/` directory

## Security Notes

- The system runs on localhost by default
- For production, configure proper authentication
- Secure API keys and tokens
- Use HTTPS in production environments

## Performance Tips

- **Simple Version**: Handles 1000+ records efficiently
- **Full Version**: Optimized for 10,000+ records
- **Database**: Automatically prunes old data
- **Memory**: Limits in-memory data points

## Support

1. Check the console output for errors
2. Review the log messages
3. Verify your configuration
4. Test with simulated data first
5. Check the GitHub issues page

## Next Steps

1. **Start Simple**: Begin with the simple version
2. **Add Real Data**: Connect your actual solar sensors
3. **Upgrade**: Move to full version for advanced features
4. **Customize**: Modify for your specific needs
5. **Share**: Contribute improvements back to the project

Enjoy monitoring your solar panels! 🌞