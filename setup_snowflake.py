#!/usr/bin/env python3
"""
Snowflake Setup Script for FjordSight PoC
Tests connection and sets up the required schema and tables
"""
import snowflake.connector
from config import Config
import sys

def test_snowflake_connection():
    """Test the Snowflake connection"""
    config = Config()
    
    print("🔗 Testing Snowflake connection...")
    print(f"Account: {config.SNOWFLAKE_ACCOUNT}")
    print(f"User: {config.SNOWFLAKE_USER}")
    print(f"Database: {config.SNOWFLAKE_DATABASE}")
    print(f"Warehouse: {config.SNOWFLAKE_WAREHOUSE}")
    
    try:
        # Load private key for JWT authentication
        import os
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        from cryptography.hazmat.backends import default_backend
        
        # Expand the tilde in the path
        private_key_path = os.path.expanduser(config.SNOWFLAKE_PRIVATE_KEY_PATH)
        
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
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ Successfully connected to Snowflake!")
        print(f"   Snowflake version: {version}")
        
        # Test warehouse access
        cursor.execute(f"USE WAREHOUSE {config.SNOWFLAKE_WAREHOUSE}")
        print(f"✅ Successfully accessed warehouse: {config.SNOWFLAKE_WAREHOUSE}")
        
        # Test database access
        cursor.execute(f"USE DATABASE {config.SNOWFLAKE_DATABASE}")
        print(f"✅ Successfully accessed database: {config.SNOWFLAKE_DATABASE}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
        # Provide specific guidance based on error type
        error_str = str(e)
        if "Network policy is required" in error_str:
            print("\n💡 Network Policy Issue:")
            print("   Your Snowflake account has IP restrictions enabled.")
            print("   Solutions:")
            print("   1. Contact your Snowflake admin to add your IP to the allowed list")
            print("   2. Connect from an approved network/VPN")
            print("   3. Use the demo with synthetic data (no Snowflake connection needed)")
            
        elif "404 Not Found" in error_str:
            print("\n💡 Account/Credentials Issue:")
            print("   The account identifier or credentials may be incorrect.")
            print("   Please verify your Snowflake account details in config.py")
            
        elif "does not exist or not authorized" in error_str:
            print("\n💡 Permission Issue:")
            print("   Your user may not have access to the specified database/warehouse.")
            print("   Contact your Snowflake admin for proper permissions.")
        
        print(f"\n🎯 Demo will work with synthetic data even without Snowflake connection!")
        return False

def setup_fjordsight_schema():
    """Set up the FjordSight schema and tables"""
    config = Config()
    
    try:
        # Load private key for JWT authentication
        import os
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        from cryptography.hazmat.backends import default_backend
        
        # Expand the tilde in the path
        private_key_path = os.path.expanduser(config.SNOWFLAKE_PRIVATE_KEY_PATH)
        
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
        
        conn = snowflake.connector.connect(
            account=config.SNOWFLAKE_ACCOUNT,
            user=config.SNOWFLAKE_USER,
            authenticator=config.SNOWFLAKE_AUTHENTICATOR,
            private_key=private_key_b64,
            warehouse=config.SNOWFLAKE_WAREHOUSE,
            database=config.SNOWFLAKE_DATABASE,
            role=config.SNOWFLAKE_ROLE
        )
        
        print(f"\n🏗️  Setting up FjordSight schema...")
        
        # Read and execute the setup script
        with open('sql/00_setup_fjordsight_schema.sql', 'r') as f:
            sql_commands = f.read()
        
        cursor = conn.cursor()
        
        # Split by semicolon and execute each command
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
        
        for i, command in enumerate(commands):
            if command:
                print(f"   Executing command {i+1}/{len(commands)}...")
                cursor.execute(command)
        
        print("✅ FjordSight schema setup completed!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema setup failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🐟 FjordSight PoC - Snowflake Setup")
    print("=" * 50)
    
    # Test connection
    if test_snowflake_connection():
        print("\n" + "=" * 50)
        
        # Ask user if they want to set up the schema
        response = input("\n🤔 Would you like to set up the FjordSight schema? (y/n): ").lower()
        
        if response in ['y', 'yes']:
            if setup_fjordsight_schema():
                print("\n🎉 Setup completed successfully!")
                print("You can now run the dashboard with real Snowflake data:")
                print("   python run_streamlit.py")
            else:
                print("\n⚠️  Schema setup failed, but demo will work with synthetic data.")
        else:
            print("\n✅ Connection test completed. You can run the demo anytime!")
    
    else:
        print("\n🎯 No problem! The demo works great with synthetic data.")
        print("Run the dashboard: python run_streamlit.py")

if __name__ == "__main__":
    main()
