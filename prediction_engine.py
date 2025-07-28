import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class SolarPredictionEngine:
    """Machine learning engine for solar power and energy predictions"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.models = {}
        self.scalers = {}
        self.feature_columns = [
            'hour', 'day_of_year', 'month', 'day_of_week',
            'temperature', 'irradiance', 'cloud_cover', 'humidity',
            'pressure', 'wind_speed', 'voltage', 'efficiency',
            'lag_power_1h', 'lag_power_3h', 'lag_power_24h',
            'rolling_mean_power_6h', 'rolling_mean_power_24h'
        ]
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for machine learning"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        df['month'] = df['timestamp'].dt.month
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Lag features (previous values)
        df['lag_power_1h'] = df['power'].shift(1)
        df['lag_power_3h'] = df['power'].shift(3)
        df['lag_power_24h'] = df['power'].shift(24)
        
        # Rolling averages
        df['rolling_mean_power_6h'] = df['power'].rolling(window=6, min_periods=1).mean()
        df['rolling_mean_power_24h'] = df['power'].rolling(window=24, min_periods=1).mean()
        
        # Weather interaction features
        df['temp_irradiance'] = df['temperature'] * df['irradiance']
        df['cloud_irradiance'] = (100 - df['cloud_cover']) * df['irradiance'] / 100
        
        # Cyclical encoding for time features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        
        return df
    
    def load_training_data(self, days: int = 30) -> pd.DataFrame:
        """Load and prepare training data from database"""
        historical_data = self.data_manager.get_historical_data(hours=days * 24)
        
        if not historical_data:
            logger.warning("No historical data available for training")
            return pd.DataFrame()
        
        df = pd.DataFrame(historical_data)
        
        # Fill missing values
        numeric_columns = ['power', 'voltage', 'current', 'temperature', 
                          'efficiency', 'irradiance', 'cloud_cover', 
                          'humidity', 'pressure', 'wind_speed']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = 0
        
        return self.prepare_features(df)
    
    def train_models(self, target: str = 'power') -> Dict:
        """Train multiple ML models for prediction"""
        df = self.load_training_data()
        
        if df.empty or len(df) < 50:
            logger.error("Insufficient data for training")
            return {}
        
        # Prepare features and target
        feature_cols = [col for col in self.feature_columns if col in df.columns]
        X = df[feature_cols].fillna(0)
        y = df[target]
        
        # Remove rows with missing target values
        mask = ~y.isna()
        X = X[mask]
        y = y[mask]
        
        if len(X) < 20:
            logger.error("Insufficient valid data for training")
            return {}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train multiple models
        models = {
            'linear': LinearRegression(),
            'random_forest': RandomForestRegressor(
                n_estimators=100, random_state=42, n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100, random_state=42
            )
        }
        
        results = {}
        
        for name, model in models.items():
            try:
                if name == 'linear':
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                
                # Calculate metrics
                mae = mean_absolute_error(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                results[name] = {
                    'model': model,
                    'mae': mae,
                    'mse': mse,
                    'r2': r2,
                    'feature_importance': self._get_feature_importance(model, feature_cols)
                }
                
                logger.info(f"Trained {name} model - MAE: {mae:.2f}, R²: {r2:.3f}")
                
            except Exception as e:
                logger.error(f"Failed to train {name} model: {e}")
        
        # Select best model based on R² score
        if results:
            best_model_name = max(results.keys(), key=lambda k: results[k]['r2'])
            self.models[target] = results[best_model_name]['model']
            self.scalers[target] = scaler if best_model_name == 'linear' else None
            
            logger.info(f"Best model for {target}: {best_model_name}")
            
            # Save models
            self._save_models(target)
        
        return results
    
    def predict_power(self, hours_ahead: int = 24, current_data: Dict = None) -> List[Dict]:
        """Predict solar power generation for the next N hours"""
        if 'power' not in self.models:
            logger.warning("Power prediction model not trained")
            return []
        
        predictions = []
        
        # Get recent data for context
        recent_data = self.data_manager.get_historical_data(hours=48)
        if not recent_data:
            logger.warning("No recent data available for prediction")
            return []
        
        df = pd.DataFrame(recent_data)
        df = self.prepare_features(df)
        
        # Use current data if provided
        if current_data:
            current_row = pd.DataFrame([current_data])
            current_row = self.prepare_features(current_row)
            df = pd.concat([df, current_row], ignore_index=True)
        
        model = self.models['power']
        scaler = self.scalers.get('power')
        
        # Make predictions for each hour ahead
        for h in range(1, hours_ahead + 1):
            future_time = datetime.now() + timedelta(hours=h)
            
            # Create feature vector for future time
            features = self._create_future_features(df, future_time, h)
            
            # Make prediction
            if scaler:
                features_scaled = scaler.transform([features])
                predicted_power = model.predict(features_scaled)[0]
            else:
                predicted_power = model.predict([features])[0]
            
            # Ensure realistic bounds
            predicted_power = max(0, predicted_power)
            if future_time.hour < 6 or future_time.hour > 18:
                predicted_power = 0  # No solar power at night
            
            # Calculate confidence (simplified)
            confidence = self._calculate_confidence(features, df)
            
            prediction = {
                'timestamp': future_time.isoformat(),
                'hours_ahead': h,
                'predicted_power': round(predicted_power, 2),
                'confidence': round(confidence, 3),
                'model_version': 'v1.0'
            }
            
            predictions.append(prediction)
            
            # Save prediction to database
            self._save_prediction(prediction)
        
        return predictions
    
    def predict_daily_energy(self, date: datetime = None) -> Dict:
        """Predict total energy generation for a specific day"""
        if not date:
            date = datetime.now().date()
        
        # Get hourly predictions for the day
        start_time = datetime.combine(date, datetime.min.time())
        hourly_predictions = []
        
        for hour in range(24):
            hour_time = start_time + timedelta(hours=hour)
            if hour_time > datetime.now():
                # Future prediction
                power_predictions = self.predict_power(hours_ahead=1, current_data=None)
                if power_predictions:
                    predicted_power = power_predictions[0]['predicted_power']
                else:
                    predicted_power = 0
            else:
                # Historical data
                historical = self.data_manager.get_historical_data(hours=1)
                if historical:
                    predicted_power = historical[0].get('power', 0)
                else:
                    predicted_power = 0
            
            hourly_predictions.append(predicted_power)
        
        # Calculate total daily energy (kWh)
        daily_energy = sum(hourly_predictions) / 1000  # Convert W to kW
        
        return {
            'date': date.isoformat(),
            'predicted_daily_energy': round(daily_energy, 2),
            'hourly_breakdown': hourly_predictions,
            'peak_power': max(hourly_predictions),
            'peak_hour': hourly_predictions.index(max(hourly_predictions))
        }
    
    def get_feature_importance(self, target: str = 'power') -> Dict:
        """Get feature importance from the trained model"""
        if target not in self.models:
            return {}
        
        model = self.models[target]
        return self._get_feature_importance(model, self.feature_columns)
    
    def _create_future_features(self, df: pd.DataFrame, future_time: datetime, hours_ahead: int) -> List:
        """Create feature vector for future prediction"""
        # Get latest available data
        latest_row = df.iloc[-1] if not df.empty else {}
        
        features = []
        for col in self.feature_columns:
            if col == 'hour':
                features.append(future_time.hour)
            elif col == 'day_of_year':
                features.append(future_time.timetuple().tm_yday)
            elif col == 'month':
                features.append(future_time.month)
            elif col == 'day_of_week':
                features.append(future_time.weekday())
            elif col.startswith('lag_'):
                # Use recent values for lag features
                features.append(latest_row.get(col, 0))
            elif col.startswith('rolling_'):
                # Use recent rolling averages
                features.append(latest_row.get(col, 0))
            else:
                # Use latest available value for other features
                features.append(latest_row.get(col, 0))
        
        return features
    
    def _calculate_confidence(self, features: List, df: pd.DataFrame) -> float:
        """Calculate prediction confidence based on feature similarity"""
        if df.empty:
            return 0.5
        
        # Simple confidence based on data availability and time of day
        hour = features[0] if features else 12
        
        # Higher confidence during peak solar hours
        if 9 <= hour <= 15:
            base_confidence = 0.8
        elif 6 <= hour <= 18:
            base_confidence = 0.6
        else:
            base_confidence = 0.9  # High confidence for night (zero power)
        
        # Adjust based on data availability
        data_factor = min(1.0, len(df) / 100)
        
        return base_confidence * data_factor
    
    def _get_feature_importance(self, model, feature_columns: List) -> Dict:
        """Extract feature importance from model"""
        try:
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
                return dict(zip(feature_columns, importance))
            elif hasattr(model, 'coef_'):
                importance = np.abs(model.coef_)
                return dict(zip(feature_columns, importance))
        except:
            pass
        
        return {}
    
    def _save_prediction(self, prediction: Dict) -> None:
        """Save prediction to database"""
        conn = sqlite3.connect(self.data_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO predictions 
            (target_timestamp, predicted_power, confidence, model_version, features)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            prediction['timestamp'],
            prediction['predicted_power'],
            prediction['confidence'],
            prediction['model_version'],
            json.dumps({'hours_ahead': prediction['hours_ahead']})
        ))
        
        conn.commit()
        conn.close()
    
    def _save_models(self, target: str) -> None:
        """Save trained models to disk"""
        try:
            model_path = f"models/solar_{target}_model.pkl"
            scaler_path = f"models/solar_{target}_scaler.pkl"
            
            import os
            os.makedirs("models", exist_ok=True)
            
            joblib.dump(self.models[target], model_path)
            if self.scalers.get(target):
                joblib.dump(self.scalers[target], scaler_path)
            
            logger.info(f"Saved {target} model to {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def load_models(self, target: str = 'power') -> bool:
        """Load pre-trained models from disk"""
        try:
            model_path = f"models/solar_{target}_model.pkl"
            scaler_path = f"models/solar_{target}_scaler.pkl"
            
            if os.path.exists(model_path):
                self.models[target] = joblib.load(model_path)
                
                if os.path.exists(scaler_path):
                    self.scalers[target] = joblib.load(scaler_path)
                
                logger.info(f"Loaded {target} model from {model_path}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
        
        return False

class WeatherPredictor:
    """Simple weather-based solar prediction"""
    
    def __init__(self):
        self.clear_sky_irradiance = 1000  # W/m²
    
    def predict_from_weather_forecast(self, weather_forecast: List[Dict]) -> List[Dict]:
        """Predict solar power from weather forecast data"""
        predictions = []
        
        for forecast in weather_forecast:
            # Extract weather parameters
            cloud_cover = forecast.get('cloud_cover', 50)
            temperature = forecast.get('temperature', 25)
            hour = datetime.fromisoformat(forecast['timestamp']).hour
            
            # Calculate expected irradiance
            irradiance = self._calculate_irradiance(hour, cloud_cover)
            
            # Estimate power output (simplified model)
            # Assumes 5kW system with temperature derating
            max_power = 5000  # Watts
            temp_factor = 1 - (temperature - 25) * 0.004  # -0.4% per °C above 25°C
            
            predicted_power = max_power * (irradiance / 1000) * temp_factor
            predicted_power = max(0, predicted_power)
            
            predictions.append({
                'timestamp': forecast['timestamp'],
                'predicted_power': round(predicted_power, 2),
                'irradiance': round(irradiance, 2),
                'temperature': temperature,
                'cloud_cover': cloud_cover,
                'confidence': 0.7  # Weather-based predictions have medium confidence
            })
        
        return predictions
    
    def _calculate_irradiance(self, hour: int, cloud_cover: float) -> float:
        """Calculate solar irradiance based on time and cloud cover"""
        # Time-based factor (solar elevation)
        if 6 <= hour <= 18:
            time_factor = max(0, np.sin((hour - 6) * np.pi / 12))
        else:
            time_factor = 0
        
        # Cloud factor
        cloud_factor = 1 - (cloud_cover / 100) * 0.8
        
        return self.clear_sky_irradiance * time_factor * cloud_factor