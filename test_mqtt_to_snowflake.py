#!/usr/bin/env python3
"""
Test MQTT to Snowflake Data Flow
Verifies that MQTT sensor data is being stored in Snowflake
"""
import time
import snowflake.connector
import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
from config import Config

def check_snowflake_data():
    """Check if MQTT data is being stored in Snowflake"""
    config = Config()
    
    print("🔍 Checking MQTT data in Snowflake...")
    
    try:
        # Load private key
        private_key_path = os.path.expanduser(config.SNOWFLAKE_PRIVATE_KEY_PATH)
        with open(private_key_path, 'rb') as key_file:
            private_key = load_pem_private_key(key_file.read(), password=None, backend=default_backend())
        
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        private_key_b64 = base64.b64encode(private_key_bytes).decode('utf-8')
        
        # Connect to Snowflake
        conn = snowflake.connector.connect(
            account=config.SNOWFLAKE_ACCOUNT,
            user=config.SNOWFLAKE_USER,
            authenticator=config.SNOWFLAKE_AUTHENTICATOR,
            private_key=private_key_b64,
            warehouse=config.SNOWFLAKE_WAREHOUSE,
            database=config.SNOWFLAKE_DATABASE,
            role=config.SNOWFLAKE_ROLE
        )
        
        cursor = conn.cursor()
        cursor.execute('USE SCHEMA FJORDSIGHT_POC')
        
        # Check if RAW_SENSOR_DATA table exists and has data
        cursor.execute("SHOW TABLES LIKE 'RAW_SENSOR_DATA'")
        tables = cursor.fetchall()
        
        if tables:
            print("✅ RAW_SENSOR_DATA table exists")
            
            # Check row count
            cursor.execute("SELECT COUNT(*) FROM RAW_SENSOR_DATA")
            count = cursor.fetchone()[0]
            print(f"📊 Total sensor records: {count}")
            
            if count > 0:
                # Show recent data
                cursor.execute("""
                    SELECT 
                        TIMESTAMP,
                        FARM_LOCATION,
                        SENSOR_TYPE,
                        VALUE,
                        UNIT,
                        QUALITY
                    FROM RAW_SENSOR_DATA 
                    ORDER BY INGESTION_TIME DESC 
                    LIMIT 10
                """)
                
                recent_data = cursor.fetchall()
                print("\n📈 Recent sensor data:")
                for row in recent_data:
                    print(f"   {row[1]} | {row[2]}: {row[3]} {row[4]} | {row[5]}")
                
                return True
            else:
                print("⚠️  No sensor data found in table")
                return False
        else:
            print("❌ RAW_SENSOR_DATA table not found")
            
            # Check what tables do exist
            cursor.execute("SHOW TABLES")
            existing_tables = cursor.fetchall()
            print("📋 Existing tables:")
            for table in existing_tables:
                print(f"   - {table[1]}")
            
            return False
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking Snowflake data: {e}")
        return False

def test_end_to_end_flow():
    """Test the complete MQTT to Streamlit flow"""
    print("\n🔄 Testing end-to-end data flow...")
    
    # Check initial state
    initial_count = 0
    if check_snowflake_data():
        # Get initial count for comparison
        pass
    
    print("\n⏱️  Waiting 60 seconds for new MQTT data to arrive...")
    print("   (MQTT simulator publishes every 30 seconds)")
    
    time.sleep(60)
    
    print("\n🔍 Checking for new data...")
    if check_snowflake_data():
        print("✅ MQTT to Snowflake data flow is working!")
        return True
    else:
        print("⚠️  No new data detected")
        return False

def main():
    """Main test function"""
    print("🐟 FjordSight PoC - MQTT to Snowflake Test")
    print("=" * 60)
    
    # Check current state
    if check_snowflake_data():
        print("\n🎉 MQTT data is being stored in Snowflake!")
        
        print("\n💡 To see live data flow:")
        print("   1. Open another terminal")
        print("   2. Run: mosquitto_sub -h localhost -p 1883 -t 'sensors/#' -v")
        print("   3. Watch real-time sensor data")
        
        print("\n🌐 Dashboard should show this data at:")
        print("   http://localhost:8501")
        
    else:
        print("\n🤔 MQTT data not found in Snowflake")
        print("💡 Try running the data ingestion manually:")
        print("   python src/data_ingestion/snowflake_ingestion.py")
        
        # Offer to test the flow
        response = input("\n🔄 Test end-to-end flow? (y/n): ").lower()
        if response in ['y', 'yes']:
            test_end_to_end_flow()

if __name__ == "__main__":
    main()
