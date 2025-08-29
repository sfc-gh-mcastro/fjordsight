"""
Snowflake Data Ingestion Layer for FjordSight PoC
Handles data ingestion from MQTT and ERP systems into Snowflake
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import pandas as pd
import snowflake.connector
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit
from snowflake.snowpark.types import StructType, StructField, StringType, DoubleType, TimestampType
import paho.mqtt.client as mqtt
import sys
import os
# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import Config

class SnowflakeConnection:
    """Manages Snowflake connection and session"""
    
    def __init__(self):
        self.config = Config()
        self.connection = None
        self.session = None
        
    def connect(self) -> bool:
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
            
            # Serialize the private key to PEM format
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
            
            self.connection = snowflake.connector.connect(**connection_params)
            self.session = Session.builder.configs(connection_params).create()
            
            logging.info("Successfully connected to Snowflake using JWT")
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect to Snowflake: {e}")
            return False
    
    def close(self):
        """Close Snowflake connections"""
        if self.connection:
            self.connection.close()
        if self.session:
            self.session.close()

class MQTTToSnowflakeIngestion:
    """Ingests MQTT sensor data into Snowflake in near real-time"""
    
    def __init__(self):
        self.config = Config()
        self.sf_conn = SnowflakeConnection()
        self.mqtt_client = mqtt.Client()
        self.message_buffer = []
        self.buffer_size = 100  # Batch size for efficiency
        
        # Setup MQTT callbacks
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def setup_snowflake_tables(self):
        """Create necessary tables in Snowflake if they don't exist"""
        if not self.sf_conn.connect():
            return False
        
        try:
            cursor = self.sf_conn.connection.cursor()
            
            # Raw sensor data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS RAW_SENSOR_DATA (
                    TIMESTAMP TIMESTAMP_NTZ,
                    FARM_LOCATION VARCHAR(100),
                    LATITUDE FLOAT,
                    LONGITUDE FLOAT,
                    SENSOR_TYPE VARCHAR(50),
                    VALUE FLOAT,
                    UNIT VARCHAR(20),
                    QUALITY VARCHAR(20),
                    DEVICE_ID VARCHAR(100),
                    INGESTION_TIME TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """)
            
            # Raw ERP data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS RAW_ERP_DATA (
                    TIMESTAMP TIMESTAMP_NTZ,
                    DATA_TYPE VARCHAR(50),
                    LOCATION VARCHAR(100),
                    DATA_JSON VARIANT,
                    INGESTION_TIME TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """)
            
            # Harmonized data table (combining IT/OT data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS HARMONIZED_FARM_DATA (
                    TIMESTAMP TIMESTAMP_NTZ,
                    FARM_LOCATION VARCHAR(100),
                    LATITUDE FLOAT,
                    LONGITUDE FLOAT,
                    WATER_TEMP_C FLOAT,
                    OXYGEN_MG_L FLOAT,
                    PH_LEVEL FLOAT,
                    SALINITY_PPT FLOAT,
                    TURBIDITY_NTU FLOAT,
                    CURRENT_SPEED_MS FLOAT,
                    FISH_ACTIVITY_INDEX FLOAT,
                    FEED_INVENTORY_KG FLOAT,
                    FISH_COUNT INT,
                    AVERAGE_WEIGHT_KG FLOAT,
                    MORTALITY_RATE FLOAT,
                    LAST_UPDATED TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """)
            
            # HAB risk predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS HAB_RISK_PREDICTIONS (
                    PREDICTION_ID VARCHAR(100),
                    TIMESTAMP TIMESTAMP_NTZ,
                    FARM_LOCATION VARCHAR(100),
                    RISK_SCORE FLOAT,
                    RISK_LEVEL VARCHAR(20),
                    PREDICTION_HORIZON_HOURS INT,
                    MODEL_VERSION VARCHAR(50),
                    FEATURES VARIANT,
                    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """)
            
            cursor.close()
            self.logger.info("Snowflake tables created/verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup Snowflake tables: {e}")
            return False
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.logger.info("Connected to MQTT broker")
            # Subscribe to all sensor topics
            for topic in self.config.MQTT_TOPICS:
                client.subscribe(topic)
                self.logger.info(f"Subscribed to topic: {topic}")
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code {rc}")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Callback for MQTT messages - buffer messages for batch processing"""
        try:
            message_data = json.loads(msg.payload.decode())
            message_data['mqtt_topic'] = msg.topic
            self.message_buffer.append(message_data)
            
            # Process buffer when it reaches the batch size
            if len(self.message_buffer) >= self.buffer_size:
                self.process_message_buffer()
                
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")
    
    def process_message_buffer(self):
        """Process buffered messages and insert into Snowflake"""
        if not self.message_buffer:
            return
        
        try:
            cursor = self.sf_conn.connection.cursor()
            
            # Prepare batch insert
            insert_data = []
            for msg in self.message_buffer:
                insert_data.append((
                    msg['timestamp'],
                    msg['farm_location'],
                    msg['latitude'],
                    msg['longitude'],
                    msg['sensor_type'],
                    msg['value'],
                    msg['unit'],
                    msg['quality'],
                    msg['device_id']
                ))
            
            # Batch insert into Snowflake
            cursor.executemany("""
                INSERT INTO RAW_SENSOR_DATA 
                (TIMESTAMP, FARM_LOCATION, LATITUDE, LONGITUDE, SENSOR_TYPE, VALUE, UNIT, QUALITY, DEVICE_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, insert_data)
            
            cursor.close()
            self.logger.info(f"Inserted {len(insert_data)} sensor readings into Snowflake")
            
            # Clear buffer
            self.message_buffer.clear()
            
        except Exception as e:
            self.logger.error(f"Failed to insert data into Snowflake: {e}")
    
    def start_ingestion(self):
        """Start the MQTT to Snowflake ingestion process"""
        if not self.setup_snowflake_tables():
            self.logger.warning("Snowflake setup failed, but continuing for demo")
        
        try:
            # Connect to MQTT broker
            self.mqtt_client.connect(self.config.MQTT_BROKER, self.config.MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            self.logger.info("MQTT to Snowflake ingestion started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start ingestion: {e}")
            self.logger.info("MQTT broker not available - this is normal for demo")
            # Exit gracefully instead of staying alive and failing
            return False
    
    def stop_ingestion(self):
        """Stop the ingestion process"""
        # Process any remaining messages
        if self.message_buffer:
            self.process_message_buffer()
        
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        self.sf_conn.close()
        
        self.logger.info("MQTT to Snowflake ingestion stopped")

class DataHarmonizer:
    """Harmonizes IT/OT data in Snowflake using Dynamic Tables or Streams & Tasks"""
    
    def __init__(self):
        self.config = Config()
        self.sf_conn = SnowflakeConnection()
    
    def create_harmonization_dynamic_table(self):
        """Create a Dynamic Table for real-time data harmonization"""
        if not self.sf_conn.connect():
            return False
        
        try:
            cursor = self.sf_conn.connection.cursor()
            
            # Create Dynamic Table that automatically harmonizes sensor data
            cursor.execute("""
                CREATE OR REPLACE DYNAMIC TABLE HARMONIZED_FARM_DATA_DT
                TARGET_LAG = '1 minute'
                WAREHOUSE = COMPUTE_WH
                AS
                SELECT 
                    DATE_TRUNC('minute', s.TIMESTAMP) as TIMESTAMP,
                    s.FARM_LOCATION,
                    s.LATITUDE,
                    s.LONGITUDE,
                    MAX(CASE WHEN s.SENSOR_TYPE = 'water_temp' THEN s.VALUE END) as WATER_TEMP_C,
                    MAX(CASE WHEN s.SENSOR_TYPE = 'oxygen' THEN s.VALUE END) as OXYGEN_MG_L,
                    MAX(CASE WHEN s.SENSOR_TYPE = 'ph' THEN s.VALUE END) as PH_LEVEL,
                    MAX(CASE WHEN s.SENSOR_TYPE = 'salinity' THEN s.VALUE END) as SALINITY_PPT,
                    MAX(CASE WHEN s.SENSOR_TYPE = 'turbidity' THEN s.VALUE END) as TURBIDITY_NTU,
                    MAX(CASE WHEN s.SENSOR_TYPE = 'current_speed' THEN s.VALUE END) as CURRENT_SPEED_MS,
                    MAX(CASE WHEN s.SENSOR_TYPE = 'fish_activity' THEN s.VALUE END) as FISH_ACTIVITY_INDEX,
                    NULL as FEED_INVENTORY_KG,  -- To be enriched with ERP data
                    NULL as FISH_COUNT,
                    NULL as AVERAGE_WEIGHT_KG,
                    NULL as MORTALITY_RATE,
                    CURRENT_TIMESTAMP() as LAST_UPDATED
                FROM RAW_SENSOR_DATA s
                WHERE s.QUALITY = 'good'
                  AND s.TIMESTAMP >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
                GROUP BY 
                    DATE_TRUNC('minute', s.TIMESTAMP),
                    s.FARM_LOCATION,
                    s.LATITUDE,
                    s.LONGITUDE
            """)
            
            cursor.close()
            self.logger.info("Dynamic Table for data harmonization created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create harmonization Dynamic Table: {e}")
            return False

if __name__ == "__main__":
    # For testing the ingestion
    print("🔄 Starting MQTT to Snowflake data ingestion...")
    ingestion = MQTTToSnowflakeIngestion()
    
    # Test Snowflake connection first
    if not ingestion.sf_conn.connect():
        print("❌ Cannot connect to Snowflake - exiting gracefully")
        sys.exit(0)
    else:
        print("✅ Snowflake connection successful")
    
    if ingestion.start_ingestion():
        print("✅ MQTT ingestion started successfully")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping ingestion...")
            ingestion.stop_ingestion()
    else:
        print("⚠️  MQTT ingestion not available - exiting gracefully")
        print("   (This is normal if MQTT broker is not configured)")
        # Exit cleanly if MQTT broker is not available
        sys.exit(0)
