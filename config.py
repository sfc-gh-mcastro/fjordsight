"""
FjordSight PoC Configuration
Centralized configuration management for the proof of concept
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for FjordSight PoC"""
    
    # Snowflake Configuration - Using JWT Authentication
    SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT', 'VWYEHVK-UF96240')
    SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER', 'mlops_user')
    SNOWFLAKE_AUTHENTICATOR = os.getenv('SNOWFLAKE_AUTHENTICATOR', 'SNOWFLAKE_JWT')
    SNOWFLAKE_PRIVATE_KEY_PATH = os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH', '~/.ssh/mlops_hol_rsa_private_key.pem')
    SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE', 'aicollege')
    SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE', 'aicollege')
    SNOWFLAKE_SCHEMA = os.getenv('SNOWFLAKE_SCHEMA', 'FJORDSIGHT_POC')
    SNOWFLAKE_ROLE = os.getenv('SNOWFLAKE_ROLE', 'aicollege')
    # Fallback password for components that haven't been updated to JWT yet
    SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD', 'fallback_password')
    
    # MQTT Configuration
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
    MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
    MQTT_TOPICS = os.getenv('MQTT_TOPICS', 'sensors/water_temp,sensors/oxygen,sensors/ph,sensors/salinity,sensors/turbidity,sensors/current_speed,sensors/fish_activity').split(',')
    
    # API Keys
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', 'your_api_key')
    
    # Data Simulation Settings
    SIMULATION_INTERVAL = 30  # seconds
    FARM_LOCATIONS = [
        {"name": "North Atlantic Site", "lat": 60.5, "lon": 5.3},
        {"name": "Fjord Site Alpha", "lat": 61.2, "lon": 6.1},
        {"name": "Deep Water Beta", "lat": 59.8, "lon": 4.9}
    ]
    
    # HAB Model Configuration
    HAB_RISK_THRESHOLD = 0.7
    PREDICTION_HORIZON_HOURS = 48
    
    # Sales Co-Pilot Configuration
    TOP_CUSTOMERS_COUNT = 3
