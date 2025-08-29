"""
Data Loader for Streamlit Application
Handles loading data from Snowflake for the dashboard
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import snowflake.connector
from snowflake.snowpark import Session
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

class DataLoader:
    """Handles data loading from Snowflake for the Streamlit dashboard"""
    
    def __init__(self):
        self.config = Config()
        self.session = None
        self.logger = logging.getLogger(__name__)
        
    def connect_to_snowflake(self) -> bool:
        """Establish connection to Snowflake using JWT authentication"""
        try:
            # Load private key for JWT authentication
            import os
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
            import base64
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
            self.logger.info(f"Successfully connected to Snowflake: {self.config.SNOWFLAKE_ACCOUNT}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Snowflake: {e}")
            # Check for specific error types
            error_str = str(e)
            if "Network policy is required" in error_str:
                self.logger.warning("Network policy restriction detected. Using synthetic data for demo.")
            elif "404 Not Found" in error_str:
                self.logger.warning("Account not found or credentials invalid. Using synthetic data for demo.")
            else:
                self.logger.warning(f"Connection failed: {error_str}. Using synthetic data for demo.")
            # For demo purposes, we'll generate synthetic data if connection fails
            return False
    
    def load_farm_data(self, farm_location: str, hours_back: int = 24) -> pd.DataFrame:
        """Load harmonized farm data for a specific location and time range"""
        
        if self.connect_to_snowflake():
            try:
                # Query the Dynamic Table for real-time harmonized IT/OT data
                query = f"""
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
                    FISH_ACTIVITY_INDEX,
                    FEED_INVENTORY_KG,
                    FISH_COUNT,
                    AVERAGE_WEIGHT_KG,
                    GROWTH_RATE_PERCENT as GROWTH_RATE_PERCENT,
                    MORTALITY_RATE,
                    1.4 as FEED_CONVERSION_RATIO,  -- Default value
                    8.0 as AIR_TEMP_C,  -- Default value
                    5.0 as WIND_SPEED_MS,  -- Default value
                    1.2 as WAVE_HEIGHT_M,  -- Default value
                    DATA_COMPLETENESS_SCORE,
                    LAST_UPDATED
                FROM HARMONIZED_FARM_DATA_DT
                WHERE FARM_LOCATION = '{farm_location}'
                  AND TIMESTAMP >= DATEADD('hour', -{hours_back}, CURRENT_TIMESTAMP())
                ORDER BY TIMESTAMP DESC
                """
                
                df = self.session.sql(query).to_pandas()
                self.logger.info(f"Loaded {len(df)} records from Snowflake")
                return df
                
            except Exception as e:
                self.logger.error(f"Failed to load data from Snowflake: {e}")
        
        # Generate synthetic data for demo if Snowflake is not available
        return self.generate_synthetic_data(farm_location, hours_back)
    
    def generate_synthetic_data(self, farm_location: str, hours_back: int = 24) -> pd.DataFrame:
        """Generate synthetic farm data for demonstration purposes"""
        
        # Find the farm location details
        farm_info = next((loc for loc in self.config.FARM_LOCATIONS if loc['name'] == farm_location), 
                        self.config.FARM_LOCATIONS[0])
        
        # Generate timestamps
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        timestamps = pd.date_range(start=start_time, end=end_time, freq='30min')
        
        n_points = len(timestamps)
        
        # Base values for different farms (slight variations)
        base_values = {
            'North Atlantic Site': {
                'water_temp': 11.5, 'oxygen': 9.2, 'ph': 7.6, 'salinity': 32.8,
                'turbidity': 1.8, 'current_speed': 0.9, 'fish_activity': 0.65
            },
            'Fjord Site Alpha': {
                'water_temp': 12.2, 'oxygen': 8.8, 'ph': 7.4, 'salinity': 31.9,
                'turbidity': 2.1, 'current_speed': 0.7, 'fish_activity': 0.58
            },
            'Deep Water Beta': {
                'water_temp': 10.8, 'oxygen': 9.5, 'ph': 7.8, 'salinity': 33.2,
                'turbidity': 1.5, 'current_speed': 1.2, 'fish_activity': 0.72
            }
        }
        
        base = base_values.get(farm_location, base_values['North Atlantic Site'])
        
        # Generate realistic time series data with trends and noise
        np.random.seed(42)  # For reproducible demo data
        
        # Create daily cycles and trends
        hours = np.array([(ts.hour + ts.minute/60) for ts in timestamps])
        daily_cycle = np.sin(2 * np.pi * hours / 24)
        trend = np.linspace(0, 0.1, n_points)  # Slight upward trend
        
        data = {
            'TIMESTAMP': timestamps,
            'FARM_LOCATION': [farm_location] * n_points,
            'LATITUDE': [farm_info['lat']] * n_points,
            'LONGITUDE': [farm_info['lon']] * n_points,
            
            # Environmental sensors with realistic variations
            'WATER_TEMP_C': base['water_temp'] + 1.5 * daily_cycle + trend + np.random.normal(0, 0.3, n_points),
            'OXYGEN_MG_L': base['oxygen'] - 0.5 * daily_cycle + np.random.normal(0, 0.2, n_points),
            'PH_LEVEL': base['ph'] + 0.2 * daily_cycle + np.random.normal(0, 0.1, n_points),
            'SALINITY_PPT': base['salinity'] + np.random.normal(0, 0.2, n_points),
            'TURBIDITY_NTU': base['turbidity'] + 0.3 * np.abs(daily_cycle) + np.random.normal(0, 0.2, n_points),
            'CURRENT_SPEED_MS': base['current_speed'] + 0.2 * daily_cycle + np.random.normal(0, 0.1, n_points),
            'FISH_ACTIVITY_INDEX': base['fish_activity'] + 0.1 * daily_cycle + np.random.normal(0, 0.05, n_points),
            
            # Production metrics (less frequent updates)
            'FEED_INVENTORY_KG': np.maximum(1000, 2500 - np.cumsum(np.random.uniform(10, 30, n_points))),
            'FISH_COUNT': np.maximum(9500, 10000 - np.arange(n_points) * 0.5),  # Slight mortality over time
            'AVERAGE_WEIGHT_KG': 4.2 + trend * 10 + np.random.normal(0, 0.1, n_points),
            'MORTALITY_RATE': np.maximum(0, 0.02 + np.random.normal(0, 0.005, n_points)),
            'FEED_CONVERSION_RATIO': 1.4 + np.random.normal(0, 0.1, n_points),
            'GROWTH_RATE_PERCENT': 3.2 + trend * 20 + np.random.normal(0, 0.2, n_points),
            
            # External data
            'AIR_TEMP_C': 8.0 + 3 * daily_cycle + np.random.normal(0, 1, n_points),
            'WIND_SPEED_MS': 5.0 + 2 * np.abs(daily_cycle) + np.random.normal(0, 1, n_points),
            'WAVE_HEIGHT_M': 1.2 + 0.3 * daily_cycle + np.random.normal(0, 0.2, n_points),
            
            # Data quality
            'DATA_COMPLETENESS_SCORE': np.random.uniform(0.85, 1.0, n_points),
            'LAST_UPDATED': [end_time] * n_points
        }
        
        df = pd.DataFrame(data)
        
        # Add some occasional anomalies for demo purposes
        anomaly_indices = np.random.choice(n_points, size=max(1, n_points//20), replace=False)
        for idx in anomaly_indices:
            if np.random.random() > 0.5:
                df.loc[idx, 'WATER_TEMP_C'] += np.random.uniform(2, 4)  # Temperature spike
            else:
                df.loc[idx, 'OXYGEN_MG_L'] -= np.random.uniform(1, 2)  # Oxygen drop
        
        # Ensure realistic bounds
        df['WATER_TEMP_C'] = np.clip(df['WATER_TEMP_C'], 8, 18)
        df['OXYGEN_MG_L'] = np.clip(df['OXYGEN_MG_L'], 6, 12)
        df['PH_LEVEL'] = np.clip(df['PH_LEVEL'], 6.8, 8.2)
        df['SALINITY_PPT'] = np.clip(df['SALINITY_PPT'], 30, 35)
        df['TURBIDITY_NTU'] = np.clip(df['TURBIDITY_NTU'], 0.5, 5)
        df['CURRENT_SPEED_MS'] = np.clip(df['CURRENT_SPEED_MS'], 0.1, 2)
        df['FISH_ACTIVITY_INDEX'] = np.clip(df['FISH_ACTIVITY_INDEX'], 0.2, 1)
        
        return df.sort_values('TIMESTAMP')
    
    def load_hab_predictions(self, farm_location: str, hours_back: int = 24) -> pd.DataFrame:
        """Load HAB risk predictions for a specific farm"""
        
        if self.connect_to_snowflake():
            try:
                query = f"""
                SELECT 
                    PREDICTION_ID,
                    TIMESTAMP,
                    FARM_LOCATION,
                    RISK_SCORE,
                    RISK_LEVEL,
                    PREDICTION_HORIZON_HOURS,
                    MODEL_VERSION,
                    FEATURES,
                    CONTRIBUTING_FACTORS,
                    RECOMMENDATIONS,
                    ANOMALY_DETECTED,
                    ANOMALY_SCORE,
                    CREATED_AT
                FROM ML_MODELS.HAB_RISK_PREDICTIONS
                WHERE FARM_LOCATION = '{farm_location}'
                  AND CREATED_AT >= DATEADD('hour', -{hours_back}, CURRENT_TIMESTAMP())
                ORDER BY CREATED_AT DESC
                """
                
                return self.session.sql(query).to_pandas()
                
            except Exception as e:
                self.logger.error(f"Failed to load HAB predictions: {e}")
        
        # Return empty DataFrame if no connection
        return pd.DataFrame()
    
    def load_customer_data(self) -> pd.DataFrame:
        """Load customer profiles for sales co-pilot"""
        
        if self.connect_to_snowflake():
            try:
                # Try to query customer data from FJORDSIGHT_POC schema
                query = """
                SELECT 
                    CUSTOMER_ID,
                    CUSTOMER_NAME,
                    CUSTOMER_TYPE,
                    LOCATION,
                    AVERAGE_ORDER_SIZE_KG,
                    AVERAGE_ORDER_VALUE,
                    PURCHASE_FREQUENCY_DAYS,
                    PROFITABILITY_TIER,
                    RISK_TOLERANCE,
                    PRICE_SENSITIVITY,
                    TOTAL_LIFETIME_VALUE,
                    RELATIONSHIP_SCORE
                FROM FJORDSIGHT_POC.CUSTOMER_PROFILES
                ORDER BY TOTAL_LIFETIME_VALUE DESC
                """
                
                return self.session.sql(query).to_pandas()
                
            except Exception as e:
                self.logger.error(f"Failed to load customer data from Snowflake: {e}")
                self.logger.info("Using synthetic customer data for demo")
        
        # Generate synthetic customer data for demo
        return self.generate_synthetic_customer_data()
    
    def generate_synthetic_customer_data(self) -> pd.DataFrame:
        """Generate synthetic customer data for demo"""
        
        customers = [
            {
                'CUSTOMER_ID': 'CUST_001',
                'CUSTOMER_NAME': 'Nordic Seafood Restaurant Group',
                'CUSTOMER_TYPE': 'restaurant',
                'LOCATION': 'Oslo, Norway',
                'PREFERRED_PRODUCTS': ['Premium Atlantic Salmon', 'Organic Salmon'],
                'AVERAGE_ORDER_SIZE_KG': 150.0,
                'AVERAGE_ORDER_VALUE': 2250.0,
                'PURCHASE_FREQUENCY_DAYS': 14,
                'PROFITABILITY_TIER': 'HIGH',
                'RISK_TOLERANCE': 'MEDIUM',
                'PRICE_SENSITIVITY': 0.3,
                'LAST_ORDER_DATE': datetime.now() - timedelta(days=10),
                'TOTAL_LIFETIME_VALUE': 45000.0,
                'RELATIONSHIP_SCORE': 4.5
            },
            {
                'CUSTOMER_ID': 'CUST_002',
                'CUSTOMER_NAME': 'Fjord Fish Distributors',
                'CUSTOMER_TYPE': 'distributor',
                'LOCATION': 'Bergen, Norway',
                'PREFERRED_PRODUCTS': ['Standard Atlantic Salmon', 'Whole Fish'],
                'AVERAGE_ORDER_SIZE_KG': 500.0,
                'AVERAGE_ORDER_VALUE': 6000.0,
                'PURCHASE_FREQUENCY_DAYS': 7,
                'PROFITABILITY_TIER': 'MEDIUM',
                'RISK_TOLERANCE': 'HIGH',
                'PRICE_SENSITIVITY': 0.6,
                'LAST_ORDER_DATE': datetime.now() - timedelta(days=5),
                'TOTAL_LIFETIME_VALUE': 78000.0,
                'RELATIONSHIP_SCORE': 4.0
            },
            {
                'CUSTOMER_ID': 'CUST_003',
                'CUSTOMER_NAME': 'Gourmet Market Chain',
                'CUSTOMER_TYPE': 'retailer',
                'LOCATION': 'Stavanger, Norway',
                'PREFERRED_PRODUCTS': ['Premium Atlantic Salmon', 'Smoked Salmon'],
                'AVERAGE_ORDER_SIZE_KG': 200.0,
                'AVERAGE_ORDER_VALUE': 3200.0,
                'PURCHASE_FREQUENCY_DAYS': 10,
                'PROFITABILITY_TIER': 'HIGH',
                'RISK_TOLERANCE': 'LOW',
                'PRICE_SENSITIVITY': 0.2,
                'LAST_ORDER_DATE': datetime.now() - timedelta(days=8),
                'TOTAL_LIFETIME_VALUE': 52000.0,
                'RELATIONSHIP_SCORE': 4.2
            },
            {
                'CUSTOMER_ID': 'CUST_004',
                'CUSTOMER_NAME': 'Export Trading Company',
                'CUSTOMER_TYPE': 'distributor',
                'LOCATION': 'International',
                'PREFERRED_PRODUCTS': ['Standard Atlantic Salmon', 'Frozen Fillets'],
                'AVERAGE_ORDER_SIZE_KG': 1000.0,
                'AVERAGE_ORDER_VALUE': 11000.0,
                'PURCHASE_FREQUENCY_DAYS': 21,
                'PROFITABILITY_TIER': 'MEDIUM',
                'RISK_TOLERANCE': 'HIGH',
                'PRICE_SENSITIVITY': 0.7,
                'LAST_ORDER_DATE': datetime.now() - timedelta(days=15),
                'TOTAL_LIFETIME_VALUE': 125000.0,
                'RELATIONSHIP_SCORE': 3.5
            }
        ]
        
        return pd.DataFrame(customers)
    
    def close_connection(self):
        """Close Snowflake connection"""
        if self.session:
            self.session.close()
