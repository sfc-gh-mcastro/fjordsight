#!/usr/bin/env python3
"""
MQTT Test Script for FjordSight PoC
Tests MQTT broker connectivity and sensor data simulation
"""
import json
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from config import Config

class MQTTTester:
    """Test MQTT broker functionality"""
    
    def __init__(self):
        self.config = Config()
        self.client = mqtt.Client()
        self.received_messages = []
        
        # Setup callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {self.config.MQTT_BROKER}:{self.config.MQTT_PORT}")
            # Subscribe to all sensor topics
            client.subscribe("sensors/+")
            print("📡 Subscribed to sensors/+ (all sensor topics)")
        else:
            print(f"❌ Failed to connect to MQTT broker, return code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback for received messages"""
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"📨 [{timestamp}] {topic}: {payload}")
            
            # Try to parse as JSON
            try:
                data = json.loads(payload)
                self.received_messages.append({
                    'topic': topic,
                    'data': data,
                    'timestamp': timestamp
                })
            except json.JSONDecodeError:
                print(f"   ⚠️  Message is not valid JSON")
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for disconnection"""
        print(f"🔌 Disconnected from MQTT broker (code: {rc})")
    
    def publish_test_message(self):
        """Publish a test sensor message"""
        test_message = {
            "timestamp": datetime.now().isoformat(),
            "farm_location": "Test Farm",
            "latitude": 60.0,
            "longitude": 5.0,
            "sensor_type": "water_temp",
            "value": 12.5,
            "unit": "celsius",
            "quality": "good",
            "device_id": "test_device_001"
        }
        
        topic = "sensors/water_temp"
        payload = json.dumps(test_message)
        
        try:
            result = self.client.publish(topic, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Published test message to {topic}")
                return True
            else:
                print(f"❌ Failed to publish message (code: {result.rc})")
                return False
        except Exception as e:
            print(f"❌ Error publishing message: {e}")
            return False
    
    def test_mqtt_connection(self):
        """Test MQTT broker connection and functionality"""
        print("🔍 Testing MQTT broker connection...")
        
        try:
            # Connect to broker
            self.client.connect(self.config.MQTT_BROKER, self.config.MQTT_PORT, 60)
            self.client.loop_start()
            
            # Wait a moment for connection
            time.sleep(2)
            
            # Publish test message
            print("\n📤 Publishing test message...")
            if self.publish_test_message():
                print("✅ Test message published successfully")
            
            # Wait for messages
            print("\n👂 Listening for messages (10 seconds)...")
            time.sleep(10)
            
            # Show summary
            print(f"\n📊 Summary:")
            print(f"   Messages received: {len(self.received_messages)}")
            
            if self.received_messages:
                print("   Recent messages:")
                for msg in self.received_messages[-3:]:  # Show last 3 messages
                    print(f"     [{msg['timestamp']}] {msg['topic']}")
            
            self.client.loop_stop()
            self.client.disconnect()
            
            return len(self.received_messages) > 0
            
        except Exception as e:
            print(f"❌ MQTT test failed: {e}")
            return False

def test_mqtt_commands():
    """Test MQTT using command line tools"""
    print("\n🛠️  Testing MQTT with command line tools...")
    print("💡 You can also test MQTT manually with these commands:")
    print()
    print("📡 Listen to all sensor topics:")
    print("   mosquitto_sub -h localhost -p 1883 -t 'sensors/#' -v")
    print()
    print("📤 Publish test messages:")
    print("   mosquitto_pub -h localhost -p 1883 -t 'sensors/water_temp' -m '{\"value\": 12.5, \"unit\": \"celsius\"}'")
    print("   mosquitto_pub -h localhost -p 1883 -t 'sensors/oxygen' -m '{\"value\": 8.9, \"unit\": \"mg/L\"}'")
    print("   mosquitto_pub -h localhost -p 1883 -t 'sensors/ph' -m '{\"value\": 7.6, \"unit\": \"pH\"}'")
    print()
    print("🔍 Check broker status:")
    print("   brew services list | grep mosquitto")
    print()
    print("🛑 Stop/Start broker:")
    print("   brew services stop mosquitto")
    print("   brew services start mosquitto")

def main():
    """Main test function"""
    print("🐟 FjordSight PoC - MQTT Broker Test")
    print("=" * 50)
    
    # Test MQTT with Python client
    tester = MQTTTester()
    
    if tester.test_mqtt_connection():
        print("\n🎉 MQTT broker is working correctly!")
        print("✅ Your sensor simulation should work properly")
    else:
        print("\n⚠️  MQTT broker test failed")
        print("💡 Try restarting the broker:")
        print("   brew services restart mosquitto")
    
    # Show command line testing options
    test_mqtt_commands()
    
    print("\n🚀 To run the complete demo with MQTT:")
    print("   python run_demo.py")

if __name__ == "__main__":
    main()
