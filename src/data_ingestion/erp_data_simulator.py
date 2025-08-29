#!/usr/bin/env python3
"""
ERP Data Simulator for FjordSight PoC
Simulates feed inventory, production metrics, and other IT system data
"""
import json
import random
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import snowflake.connector
import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import Config

class ERPDataSimulator:
    """Simulates ERP data for feed inventory, production metrics, etc."""
    
    def __init__(self):
        self.config = Config()
        self.running = False
        self.connection = None
        
        # ERP data generation intervals (less frequent than sensors)
        self.feed_inventory_interval = 300  # 5 minutes
        self.production_metrics_interval = 600  # 10 minutes
        
        # Base values for different farms
        self.base_inventory = {
            'North Atlantic Site': {'feed_kg': 2500, 'fish_count': 10000},
            'Fjord Site Alpha': {'feed_kg': 2200, 'fish_count': 9800},
            'Deep Water Beta': {'feed_kg': 2800, 'fish_count': 10200}
        }
        
    def connect_to_snowflake(self) -> bool:
        """Connect to Snowflake for data storage"""
        try:
            # Load private key for JWT authentication
            private_key_path = os.path.expanduser(self.config.SNOWFLAKE_PRIVATE_KEY_PATH)
            with open(private_key_path, 'rb') as key_file:
                private_key = load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            
            # Convert to base64 string as required by Snowflake
            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            private_key_b64 = base64.b64encode(private_key_bytes).decode('utf-8')
            
            self.connection = snowflake.connector.connect(
                account=self.config.SNOWFLAKE_ACCOUNT,
                user=self.config.SNOWFLAKE_USER,
                authenticator=self.config.SNOWFLAKE_AUTHENTICATOR,
                private_key=private_key_b64,
                warehouse=self.config.SNOWFLAKE_WAREHOUSE,
                database=self.config.SNOWFLAKE_DATABASE,
                role=self.config.SNOWFLAKE_ROLE
            )
            
            cursor = self.connection.cursor()
            cursor.execute('USE SCHEMA FJORDSIGHT_POC')
            
            # Create ERP tables if they don't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS RAW_ERP_DATA (
                    TIMESTAMP TIMESTAMP_NTZ,
                    DATA_TYPE VARCHAR(50),
                    LOCATION VARCHAR(100),
                    DATA_JSON VARIANT,
                    SOURCE_SYSTEM VARCHAR(50),
                    INGESTION_TIME TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """)
            
            cursor.close()
            print("✅ Connected to Snowflake for ERP data storage")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Snowflake: {e}")
            return False
    
    def generate_feed_inventory_data(self, farm_location: str) -> Dict[str, Any]:
        """Generate feed inventory data"""
        base_data = self.base_inventory[farm_location]
        
        # Simulate feed consumption over time
        current_inventory = base_data['feed_kg'] - random.randint(50, 200)
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'feed_type': random.choice(['Premium Pellets', 'Standard Feed', 'Organic Mix', 'Starter Feed']),
            'quantity_kg': max(500, current_inventory),
            'supplier': random.choice(['AquaFeed Co', 'Nordic Nutrition', 'Marine Feeds Ltd', 'Ocean Harvest']),
            'expiry_date': (datetime.now() + timedelta(days=random.randint(30, 180))).isoformat(),
            'cost_per_kg': round(random.uniform(2.5, 4.5), 2),
            'location': farm_location,
            'quality_grade': random.choice(['Premium', 'Standard', 'Organic']),
            'batch_id': f"FEED_{random.randint(1000, 9999)}",
            'storage_temperature': round(random.uniform(15, 25), 1)
        }
    
    def generate_production_data(self, farm_location: str) -> Dict[str, Any]:
        """Generate production metrics data"""
        base_data = self.base_inventory[farm_location]
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'batch_id': f"BATCH_{random.randint(1000, 9999)}",
            'fish_count': base_data['fish_count'] + random.randint(-100, 50),
            'average_weight_kg': round(random.uniform(3.5, 6.0), 2),
            'mortality_rate': round(random.uniform(0.01, 0.05), 4),
            'feed_conversion_ratio': round(random.uniform(1.1, 1.8), 2),
            'growth_rate_percent': round(random.uniform(2.0, 4.5), 2),
            'location': farm_location,
            'harvest_readiness_score': round(random.uniform(0.3, 0.9), 2),
            'health_score': round(random.uniform(0.7, 1.0), 2),
            'feeding_schedule': random.choice(['Morning', 'Afternoon', 'Evening', 'Night']),
            'water_quality_index': round(random.uniform(0.8, 1.0), 2)
        }
    
    def store_erp_data(self, data_type: str, location: str, data: Dict[str, Any], source_system: str):
        """Store ERP data in Snowflake using the correct table structure"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('USE SCHEMA FJORDSIGHT_POC')
            
            # Insert ERP data using the actual table columns
            if data_type == 'feed_inventory':
                cursor.execute("""
                    INSERT INTO RAW_ERP_DATA 
                    (DATA_TYPE, LOCATION, FEED_QUANTITY_KG, FISH_COUNT, AVERAGE_WEIGHT_KG, 
                     GROWTH_RATE_PERCENT, MORTALITY_RATE, SOURCE_SYSTEM)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data_type,
                    location,
                    data.get('quantity_kg', 0),
                    0,  # Not applicable for feed data
                    0,  # Not applicable for feed data
                    0,  # Not applicable for feed data
                    0,  # Not applicable for feed data
                    source_system
                ))
            elif data_type == 'production_metrics':
                cursor.execute("""
                    INSERT INTO RAW_ERP_DATA 
                    (DATA_TYPE, LOCATION, FEED_QUANTITY_KG, FISH_COUNT, AVERAGE_WEIGHT_KG, 
                     GROWTH_RATE_PERCENT, MORTALITY_RATE, SOURCE_SYSTEM)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data_type,
                    location,
                    0,  # Not applicable for production data
                    data.get('fish_count', 0),
                    data.get('average_weight_kg', 0),
                    data.get('growth_rate_percent', 0),
                    data.get('mortality_rate', 0),
                    source_system
                ))
            
            cursor.close()
            print(f"📊 Stored {data_type} data for {location}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to store ERP data: {e}")
            return False
    
    def simulate_erp_data(self):
        """Continuously generate and store ERP data"""
        last_feed_update = {}
        last_production_update = {}
        
        for location in [loc['name'] for loc in self.config.FARM_LOCATIONS]:
            last_feed_update[location] = 0
            last_production_update[location] = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                for location in [loc['name'] for loc in self.config.FARM_LOCATIONS]:
                    
                    # Generate feed inventory data
                    if current_time - last_feed_update[location] >= self.feed_inventory_interval:
                        feed_data = self.generate_feed_inventory_data(location)
                        self.store_erp_data('feed_inventory', location, feed_data, 'SAP_ERP')
                        last_feed_update[location] = current_time
                    
                    # Generate production metrics data
                    if current_time - last_production_update[location] >= self.production_metrics_interval:
                        production_data = self.generate_production_data(location)
                        self.store_erp_data('production_metrics', location, production_data, 'Production_System')
                        last_production_update[location] = current_time
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Error in ERP simulation: {e}")
                time.sleep(60)  # Wait longer on error
    
    def start_simulation(self):
        """Start the ERP data simulation"""
        if not self.connect_to_snowflake():
            print("❌ Cannot connect to Snowflake - ERP simulation cannot start")
            return False
        
        self.running = True
        
        # Start ERP simulation in a separate thread
        erp_thread = threading.Thread(target=self.simulate_erp_data)
        erp_thread.daemon = True
        erp_thread.start()
        
        print("🏭 ERP data simulation started")
        print("   Feed inventory updates: every 5 minutes")
        print("   Production metrics: every 10 minutes")
        print("Press Ctrl+C to stop...")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping ERP simulation...")
            self.stop_simulation()
    
    def stop_simulation(self):
        """Stop the ERP data simulation"""
        self.running = False
        if self.connection:
            self.connection.close()
        print("✅ ERP simulation stopped")

if __name__ == "__main__":
    simulator = ERPDataSimulator()
    simulator.start_simulation()
