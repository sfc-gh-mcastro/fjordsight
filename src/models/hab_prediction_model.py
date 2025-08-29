"""
HAB (Harmful Algal Bloom) Prediction Model for FjordSight PoC
Uses Snowpark ML and Cortex AI to predict harmful algal bloom risks
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import snowflake.connector
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit, when, avg, max as sf_max, min as sf_min
from snowflake.snowpark.types import StructType, StructField, StringType, DoubleType, TimestampType
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import Config

class HABPredictionModel:
    """
    Harmful Algal Bloom prediction model using environmental sensor data
    and external oceanographic data from Snowflake Marketplace
    """
    
    def __init__(self):
        self.config = Config()
        self.session = None
        self.model = None
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.feature_columns = [
            'WATER_TEMP_C', 'PH_LEVEL', 'OXYGEN_MG_L', 'SALINITY_PPT',
            'TURBIDITY_NTU', 'CURRENT_SPEED_MS', 'AIR_TEMP_C', 
            'WIND_SPEED_MS', 'WAVE_HEIGHT_M'
        ]
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def connect_to_snowflake(self) -> bool:
        """Establish Snowflake connection using JWT authentication"""
        try:
            # Load private key for JWT authentication
            import os
            import base64
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            from cryptography.hazmat.backends import default_backend
            
            # Expand the tilde in the path
            private_key_path = os.path.expanduser(self.config.SNOWFLAKE_PRIVATE_KEY_PATH)
            
            # Read and parse the private key
            with open(private_key_path, 'rb') as key_file:
                private_key = load_pem_private_key(
                    key_file.read(),
                    password=None,  # Assuming the key is not password-protected
                    backend=default_backend()
                )
            
            # Serialize the private key to DER format and encode as base64 string (required by Snowflake)
            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Convert to base64 string as required by Snowflake
            private_key_b64 = base64.b64encode(private_key_bytes).decode('utf-8')
            
            connection_params = {
                'account': self.config.SNOWFLAKE_ACCOUNT,
                'user': self.config.SNOWFLAKE_USER,
                'authenticator': self.config.SNOWFLAKE_AUTHENTICATOR,
                'private_key': private_key_b64,
                'warehouse': self.config.SNOWFLAKE_WAREHOUSE,
                'database': self.config.SNOWFLAKE_DATABASE,
                'schema': self.config.SNOWFLAKE_SCHEMA,
                'role': self.config.SNOWFLAKE_ROLE
            }
            
            self.session = Session.builder.configs(connection_params).create()
            self.logger.info("Connected to Snowflake successfully using JWT")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Snowflake: {e}")
            return False
    
    def create_training_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create engineered features for HAB prediction"""
        
        # Sort by timestamp for time-series features
        df = df.sort_values(['FARM_LOCATION', 'TIMESTAMP'])
        
        # Create time-based features
        df['HOUR'] = pd.to_datetime(df['TIMESTAMP']).dt.hour
        df['DAY_OF_YEAR'] = pd.to_datetime(df['TIMESTAMP']).dt.dayofyear
        df['MONTH'] = pd.to_datetime(df['TIMESTAMP']).dt.month
        
        # Create moving averages (3-hour and 6-hour windows)
        for col in ['WATER_TEMP_C', 'PH_LEVEL', 'OXYGEN_MG_L', 'TURBIDITY_NTU']:
            if col in df.columns:
                df[f'{col}_MA3H'] = df.groupby('FARM_LOCATION')[col].rolling(window=3, min_periods=1).mean().reset_index(0, drop=True)
                df[f'{col}_MA6H'] = df.groupby('FARM_LOCATION')[col].rolling(window=6, min_periods=1).mean().reset_index(0, drop=True)
        
        # Create rate of change features
        for col in ['WATER_TEMP_C', 'PH_LEVEL', 'OXYGEN_MG_L']:
            if col in df.columns:
                df[f'{col}_RATE'] = df.groupby('FARM_LOCATION')[col].diff()
        
        # Create interaction features (known HAB risk factors)
        if 'WATER_TEMP_C' in df.columns and 'PH_LEVEL' in df.columns:
            df['TEMP_PH_INTERACTION'] = df['WATER_TEMP_C'] * df['PH_LEVEL']
        
        if 'OXYGEN_MG_L' in df.columns and 'TURBIDITY_NTU' in df.columns:
            df['OXYGEN_TURBIDITY_RATIO'] = df['OXYGEN_MG_L'] / (df['TURBIDITY_NTU'] + 0.1)
        
        # HAB risk indicators based on domain knowledge
        df['HIGH_TEMP_RISK'] = (df['WATER_TEMP_C'] > 15.0).astype(int) if 'WATER_TEMP_C' in df.columns else 0
        df['LOW_OXYGEN_RISK'] = (df['OXYGEN_MG_L'] < 7.0).astype(int) if 'OXYGEN_MG_L' in df.columns else 0
        df['HIGH_PH_RISK'] = (df['PH_LEVEL'] > 8.0).astype(int) if 'PH_LEVEL' in df.columns else 0
        df['HIGH_TURBIDITY_RISK'] = (df['TURBIDITY_NTU'] > 3.0).astype(int) if 'TURBIDITY_NTU' in df.columns else 0
        
        return df
    
    def create_synthetic_hab_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create synthetic HAB risk labels for training
        In a real scenario, this would come from historical HAB observations
        """
        
        # Create HAB risk score based on environmental conditions
        risk_score = 0.0
        
        # Temperature contribution (higher temp = higher risk)
        if 'WATER_TEMP_C' in df.columns:
            temp_risk = np.clip((df['WATER_TEMP_C'] - 10) / 8, 0, 1)  # Risk increases above 10°C
            risk_score += 0.3 * temp_risk
        
        # pH contribution (alkaline conditions favor some HAB species)
        if 'PH_LEVEL' in df.columns:
            ph_risk = np.clip((df['PH_LEVEL'] - 7.5) / 1.0, 0, 1)  # Risk increases above 7.5
            risk_score += 0.2 * ph_risk
        
        # Low oxygen contribution
        if 'OXYGEN_MG_L' in df.columns:
            oxygen_risk = np.clip((9 - df['OXYGEN_MG_L']) / 3, 0, 1)  # Risk increases below 9 mg/L
            risk_score += 0.2 * oxygen_risk
        
        # High turbidity contribution
        if 'TURBIDITY_NTU' in df.columns:
            turbidity_risk = np.clip((df['TURBIDITY_NTU'] - 1) / 4, 0, 1)  # Risk increases above 1 NTU
            risk_score += 0.15 * turbidity_risk
        
        # Stagnant water (low current) contribution
        if 'CURRENT_SPEED_MS' in df.columns:
            current_risk = np.clip((1 - df['CURRENT_SPEED_MS']) / 1, 0, 1)  # Risk increases with low current
            risk_score += 0.15 * current_risk
        
        # Add some random variation and seasonal effects
        seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * df['DAY_OF_YEAR'] / 365 - np.pi/2)  # Peak in summer
        risk_score *= seasonal_factor
        
        # Add noise
        risk_score += np.random.normal(0, 0.1, len(df))
        
        # Clip to [0, 1] range
        df['HAB_RISK_SCORE'] = np.clip(risk_score, 0, 1)
        
        # Create categorical risk levels
        df['HAB_RISK_LEVEL'] = pd.cut(df['HAB_RISK_SCORE'], 
                                     bins=[0, 0.3, 0.7, 1.0], 
                                     labels=['LOW', 'MEDIUM', 'HIGH'])
        
        return df
    
    def load_training_data(self) -> pd.DataFrame:
        """Load and prepare training data from Snowflake"""
        if not self.connect_to_snowflake():
            return None
        
        try:
            # Query harmonized data for training
            query = """
            SELECT 
                TIMESTAMP,
                FARM_LOCATION,
                LATITUDE,
                LONGITUDE,
                WATER_TEMP_C,
                OXYGEN_MG_L,
                PH_LEVEL,
                SALINITY_PPT,
                TURBIDITY_NTU,
                CURRENT_SPEED_MS,
                AIR_TEMP_C,
                WIND_SPEED_MS,
                WAVE_HEIGHT_M,
                DATA_COMPLETENESS_SCORE
            FROM HARMONIZED_FARM_DATA
            WHERE TIMESTAMP >= DATEADD('day', -30, CURRENT_TIMESTAMP())
              AND DATA_COMPLETENESS_SCORE > 0.7
            ORDER BY FARM_LOCATION, TIMESTAMP
            """
            
            df = self.session.sql(query).to_pandas()
            self.logger.info(f"Loaded {len(df)} records for training")
            
            # Handle missing values
            df = df.fillna(method='forward').fillna(method='backward')
            
            # Create features and synthetic labels
            df = self.create_training_features(df)
            df = self.create_synthetic_hab_labels(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load training data: {e}")
            return None
    
    def train_model(self) -> bool:
        """Train the HAB prediction model"""
        
        # Load training data
        df = self.load_training_data()
        if df is None or len(df) == 0:
            self.logger.error("No training data available")
            return False
        
        try:
            # Prepare features
            feature_cols = [col for col in self.feature_columns if col in df.columns]
            feature_cols.extend([f'{col}_MA3H' for col in ['WATER_TEMP_C', 'PH_LEVEL', 'OXYGEN_MG_L', 'TURBIDITY_NTU'] if f'{col}_MA3H' in df.columns])
            feature_cols.extend([f'{col}_RATE' for col in ['WATER_TEMP_C', 'PH_LEVEL', 'OXYGEN_MG_L'] if f'{col}_RATE' in df.columns])
            feature_cols.extend(['TEMP_PH_INTERACTION', 'OXYGEN_TURBIDITY_RATIO', 'HIGH_TEMP_RISK', 
                               'LOW_OXYGEN_RISK', 'HIGH_PH_RISK', 'HIGH_TURBIDITY_RISK'])
            
            # Filter available features
            available_features = [col for col in feature_cols if col in df.columns]
            
            X = df[available_features].fillna(0)
            y = df['HAB_RISK_SCORE']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            self.logger.info(f"Model trained successfully - MSE: {mse:.4f}, R2: {r2:.4f}")
            
            # Train anomaly detection model
            self.anomaly_detector.fit(X_train_scaled)
            
            # Save model
            self.save_model()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to train model: {e}")
            return False
    
    def predict_hab_risk(self, farm_location: str, prediction_hours: int = 48) -> Dict:
        """Predict HAB risk for the next N hours"""
        
        if not self.connect_to_snowflake():
            return None
        
        try:
            # Get latest data for the farm
            query = f"""
            SELECT 
                TIMESTAMP,
                FARM_LOCATION,
                WATER_TEMP_C,
                OXYGEN_MG_L,
                PH_LEVEL,
                SALINITY_PPT,
                TURBIDITY_NTU,
                CURRENT_SPEED_MS,
                AIR_TEMP_C,
                WIND_SPEED_MS,
                WAVE_HEIGHT_M
            FROM HARMONIZED_FARM_DATA
            WHERE FARM_LOCATION = '{farm_location}'
              AND TIMESTAMP >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
            ORDER BY TIMESTAMP DESC
            LIMIT 24
            """
            
            df = self.session.sql(query).to_pandas()
            
            if len(df) == 0:
                return {"error": f"No recent data found for {farm_location}"}
            
            # Create features
            df = self.create_training_features(df)
            
            # Get latest record for prediction
            latest_data = df.iloc[0]
            
            # Prepare features
            feature_cols = [col for col in self.feature_columns if col in df.columns]
            features = latest_data[feature_cols].fillna(0).values.reshape(1, -1)
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            risk_score = self.model.predict(features_scaled)[0]
            risk_score = np.clip(risk_score, 0, 1)  # Ensure valid range
            
            # Determine risk level
            if risk_score < 0.3:
                risk_level = "LOW"
            elif risk_score < 0.7:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"
            
            # Check for anomalies
            anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
            is_anomaly = self.anomaly_detector.predict(features_scaled)[0] == -1
            
            # Create prediction result
            prediction = {
                "farm_location": farm_location,
                "timestamp": datetime.now().isoformat(),
                "prediction_horizon_hours": prediction_hours,
                "risk_score": float(risk_score),
                "risk_level": risk_level,
                "anomaly_detected": bool(is_anomaly),
                "anomaly_score": float(anomaly_score),
                "contributing_factors": self.get_risk_factors(latest_data),
                "recommendations": self.get_recommendations(risk_score, is_anomaly)
            }
            
            # Store prediction in Snowflake
            self.store_prediction(prediction)
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"Failed to predict HAB risk: {e}")
            return {"error": str(e)}
    
    def get_risk_factors(self, data: pd.Series) -> List[str]:
        """Identify the main contributing risk factors"""
        factors = []
        
        if data.get('WATER_TEMP_C', 0) > 15:
            factors.append(f"High water temperature ({data.get('WATER_TEMP_C', 0):.1f}°C)")
        
        if data.get('PH_LEVEL', 0) > 8.0:
            factors.append(f"Elevated pH level ({data.get('PH_LEVEL', 0):.1f})")
        
        if data.get('OXYGEN_MG_L', 0) < 7.0:
            factors.append(f"Low oxygen level ({data.get('OXYGEN_MG_L', 0):.1f} mg/L)")
        
        if data.get('TURBIDITY_NTU', 0) > 3.0:
            factors.append(f"High turbidity ({data.get('TURBIDITY_NTU', 0):.1f} NTU)")
        
        if data.get('CURRENT_SPEED_MS', 0) < 0.3:
            factors.append(f"Low water current ({data.get('CURRENT_SPEED_MS', 0):.1f} m/s)")
        
        return factors
    
    def get_recommendations(self, risk_score: float, is_anomaly: bool) -> List[str]:
        """Generate recommendations based on risk level"""
        recommendations = []
        
        if risk_score > 0.7:
            recommendations.extend([
                "Increase monitoring frequency to every 15 minutes",
                "Consider reducing feed amounts to minimize nutrient load",
                "Prepare contingency plans for potential harvest acceleration",
                "Alert marine biology team for detailed water sampling"
            ])
        elif risk_score > 0.3:
            recommendations.extend([
                "Monitor conditions closely over next 24 hours",
                "Review recent feeding schedules and adjust if necessary",
                "Check water circulation systems for optimal flow"
            ])
        else:
            recommendations.append("Continue normal monitoring schedule")
        
        if is_anomaly:
            recommendations.append("Anomalous conditions detected - investigate sensor readings and environmental factors")
        
        return recommendations
    
    def store_prediction(self, prediction: Dict):
        """Store prediction results in Snowflake"""
        try:
            # Insert into predictions table
            insert_query = f"""
            INSERT INTO ML_MODELS.HAB_RISK_PREDICTIONS 
            (PREDICTION_ID, TIMESTAMP, FARM_LOCATION, RISK_SCORE, RISK_LEVEL, 
             PREDICTION_HORIZON_HOURS, MODEL_VERSION, FEATURES)
            VALUES 
            ('{prediction['farm_location']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}',
             '{prediction['timestamp']}',
             '{prediction['farm_location']}',
             {prediction['risk_score']},
             '{prediction['risk_level']}',
             {prediction['prediction_horizon_hours']},
             'HAB_RF_v1.0',
             PARSE_JSON('{json.dumps(prediction['contributing_factors'])}'))
            """
            
            self.session.sql(insert_query).collect()
            self.logger.info(f"Stored prediction for {prediction['farm_location']}")
            
        except Exception as e:
            self.logger.error(f"Failed to store prediction: {e}")
    
    def connect_to_snowflake(self) -> bool:
        """Establish connection to Snowflake"""
        try:
            connection_params = {
                'account': self.config.SNOWFLAKE_ACCOUNT,
                'user': self.config.SNOWFLAKE_USER,
                'password': self.config.SNOWFLAKE_PASSWORD,
                'warehouse': self.config.SNOWFLAKE_WAREHOUSE,
                'database': self.config.SNOWFLAKE_DATABASE,
                'schema': 'ML_MODELS'
            }
            
            self.session = Session.builder.configs(connection_params).create()
            self.logger.info("Connected to Snowflake successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Snowflake: {e}")
            return False
    
    def save_model(self):
        """Save the trained model to disk"""
        try:
            joblib.dump(self.model, '/tmp/hab_model.pkl')
            joblib.dump(self.scaler, '/tmp/hab_scaler.pkl')
            joblib.dump(self.anomaly_detector, '/tmp/hab_anomaly_detector.pkl')
            self.logger.info("Model saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save model: {e}")
    
    def load_model(self):
        """Load the trained model from disk"""
        try:
            self.model = joblib.load('/tmp/hab_model.pkl')
            self.scaler = joblib.load('/tmp/hab_scaler.pkl')
            self.anomaly_detector = joblib.load('/tmp/hab_anomaly_detector.pkl')
            self.logger.info("Model loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False

# Cortex AI integration for advanced anomaly detection
class CortexAnomalyDetector:
    """Uses Snowflake Cortex AI for anomaly detection in sensor data"""
    
    def __init__(self):
        self.config = Config()
        self.session = None
    
    def setup_cortex_anomaly_detection(self):
        """Set up Cortex anomaly detection on sensor data"""
        
        if not self.connect_to_snowflake():
            return False
        
        try:
            # Create view for Cortex anomaly detection
            cortex_query = """
            CREATE OR REPLACE VIEW SENSOR_ANOMALY_DETECTION AS
            SELECT 
                FARM_LOCATION,
                TIMESTAMP,
                WATER_TEMP_C,
                OXYGEN_MG_L,
                PH_LEVEL,
                TURBIDITY_NTU,
                -- Use Cortex anomaly detection function
                SNOWFLAKE.CORTEX.ANOMALY_DETECTION(
                    ARRAY_CONSTRUCT(WATER_TEMP_C, OXYGEN_MG_L, PH_LEVEL, TURBIDITY_NTU)
                ) OVER (
                    PARTITION BY FARM_LOCATION 
                    ORDER BY TIMESTAMP 
                    ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
                ) AS ANOMALY_SCORE
            FROM HARMONIZED_FARM_DATA
            WHERE TIMESTAMP >= DATEADD('hour', -48, CURRENT_TIMESTAMP())
            ORDER BY FARM_LOCATION, TIMESTAMP
            """
            
            self.session.sql(cortex_query).collect()
            self.logger.info("Cortex anomaly detection view created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup Cortex anomaly detection: {e}")
            return False

if __name__ == "__main__":
    # Train and test the HAB prediction model
    hab_model = HABPredictionModel()
    
    if hab_model.train_model():
        # Make a prediction for each farm location
        for location in hab_model.config.FARM_LOCATIONS:
            prediction = hab_model.predict_hab_risk(location['name'])
            print(f"\nHAB Risk Prediction for {location['name']}:")
            print(f"Risk Score: {prediction.get('risk_score', 'N/A')}")
            print(f"Risk Level: {prediction.get('risk_level', 'N/A')}")
            print(f"Contributing Factors: {prediction.get('contributing_factors', [])}")
    else:
        print("Failed to train HAB prediction model")
