#!/usr/bin/env python3
"""
Test JWT Connection for FjordSight PoC
Simple test to verify JWT authentication is working
"""
import snowflake.connector
import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
from config import Config

def test_jwt_connection():
    """Test JWT connection to Snowflake"""
    config = Config()
    
    print("🔐 Testing JWT Authentication...")
    print(f"Account: {config.SNOWFLAKE_ACCOUNT}")
    print(f"User: {config.SNOWFLAKE_USER}")
    print(f"Database: {config.SNOWFLAKE_DATABASE}")
    print(f"Warehouse: {config.SNOWFLAKE_WAREHOUSE}")
    print(f"Private Key Path: {config.SNOWFLAKE_PRIVATE_KEY_PATH}")
    
    try:
        # Load private key
        private_key_path = os.path.expanduser(config.SNOWFLAKE_PRIVATE_KEY_PATH)
        print(f"Loading private key from: {private_key_path}")
        
        with open(private_key_path, 'rb') as key_file:
            private_key = load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        
        # Convert to base64-encoded DER format
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        private_key_b64 = base64.b64encode(private_key_bytes).decode('utf-8')
        print("✅ Private key loaded and converted successfully")
        
        # Test connection
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
        
        # Test basic queries
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ Connected! Snowflake version: {version}")
        
        cursor.execute("SELECT CURRENT_ROLE(), CURRENT_USER(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
        context = cursor.fetchone()
        print(f"✅ Context - Role: {context[0]}, User: {context[1]}, Database: {context[2]}, Schema: {context[3]}")
        
        # Test creating a simple table
        try:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS FJORDSIGHT_POC")
            cursor.execute("USE SCHEMA FJORDSIGHT_POC")
            print("✅ Successfully created/accessed FJORDSIGHT_POC schema")
            
            # Test table creation
            cursor.execute("""
                CREATE OR REPLACE TABLE TEST_CONNECTION (
                    ID INT,
                    MESSAGE VARCHAR(100),
                    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """)
            
            cursor.execute("INSERT INTO TEST_CONNECTION (ID, MESSAGE) VALUES (1, 'JWT Connection Test Successful!')")
            
            cursor.execute("SELECT * FROM TEST_CONNECTION")
            result = cursor.fetchone()
            print(f"✅ Table test successful: {result}")
            
            # Clean up
            cursor.execute("DROP TABLE TEST_CONNECTION")
            
        except Exception as schema_error:
            print(f"⚠️  Schema/table creation limited: {schema_error}")
            print("   This is normal - you may have read-only access")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 JWT Authentication is working perfectly!")
        print("✅ You can now run the FjordSight dashboard with real Snowflake data")
        
        return True
        
    except Exception as e:
        print(f"❌ JWT connection failed: {e}")
        return False

if __name__ == "__main__":
    if test_jwt_connection():
        print("\n🚀 Ready to run FjordSight PoC:")
        print("   python run_streamlit.py")
    else:
        print("\n🎯 Demo will work with synthetic data:")
        print("   python run_streamlit.py")
