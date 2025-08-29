"""
MQTT Sensor Data Simulator for FjordSight PoC
Simulates real-time sensor data from salmon farms for demonstration purposes
"""
import json
import random
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import paho.mqtt.client as mqtt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import Config

class SensorDataSimulator:
    """Simulates sensor data for salmon farm operations"""
    
    def __init__(self):
        self.config = Config()
        self.client = mqtt.Client()
        self.running = False
        
        # Sensor data ranges (realistic values for salmon farming)
        self.sensor_ranges = {
            'water_temp': {'min': 8.0, 'max': 18.0, 'unit': 'celsius'},
            'oxygen': {'min': 6.0, 'max': 12.0, 'unit': 'mg/L'},
            'ph': {'min': 6.8, 'max': 8.2, 'unit': 'pH'},
            'salinity': {'min': 30.0, 'max': 35.0, 'unit': 'ppt'},
            'turbidity': {'min': 0.5, 'max': 5.0, 'unit': 'NTU'},
            'current_speed': {'min': 0.1, 'max': 2.0, 'unit': 'm/s'},
            'fish_activity': {'min': 0.2, 'max': 1.0, 'unit': 'activity_index'}
        }
        
        # Simulate some seasonal/daily patterns
        self.base_values = {
            'water_temp': 12.0,
            'oxygen': 9.0,
            'ph': 7.5,
            'salinity': 32.5,
            'turbidity': 2.0,
            'current_speed': 0.8,
            'fish_activity': 0.6
        }
        
    def connect_mqtt(self) -> bool:
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.config.MQTT_BROKER, self.config.MQTT_PORT, 60)
            print(f"Connected to MQTT broker at {self.config.MQTT_BROKER}:{self.config.MQTT_PORT}")
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            print("💡 MQTT broker not available. This is normal for demo purposes.")
            print("   The dashboard will work with synthetic data.")
            return False
    
    def generate_sensor_reading(self, sensor_type: str, farm_location: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a realistic sensor reading with some variation and trends"""
        
        # Add some time-based variation (simulating daily cycles)
        hour = datetime.now().hour
        daily_factor = 0.1 * (1 + 0.3 * (hour - 12) / 12)  # Temperature varies by time of day
        
        # Add random variation
        base_value = self.base_values[sensor_type]
        variation = random.uniform(-0.1, 0.1) * base_value
        seasonal_drift = random.uniform(-0.05, 0.05) * base_value
        
        # Apply daily cycle for temperature
        if sensor_type == 'water_temp':
            daily_cycle = 2.0 * daily_factor
            value = base_value + variation + seasonal_drift + daily_cycle
        else:
            value = base_value + variation + seasonal_drift
        
        # Ensure value stays within realistic bounds
        sensor_range = self.sensor_ranges[sensor_type]
        value = max(sensor_range['min'], min(sensor_range['max'], value))
        
        # Occasionally simulate anomalous readings (for HAB detection)
        if random.random() < 0.05:  # 5% chance of anomaly
            if sensor_type == 'oxygen':
                value *= 0.7  # Oxygen drop
            elif sensor_type == 'ph':
                value += random.uniform(0.5, 1.0)  # pH spike
            elif sensor_type == 'turbidity':
                value *= 2.0  # Turbidity increase
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'farm_location': farm_location['name'],
            'latitude': farm_location['lat'],
            'longitude': farm_location['lon'],
            'sensor_type': sensor_type,
            'value': round(value, 2),
            'unit': sensor_range['unit'],
            'quality': 'good' if random.random() > 0.02 else 'warning',  # 2% chance of warning
            'device_id': f"{farm_location['name'].replace(' ', '_').lower()}_{sensor_type}_{random.randint(1000, 9999)}"
        }
    
    def publish_sensor_data(self):
        """Continuously publish sensor data to MQTT topics"""
        while self.running:
            try:
                for farm_location in self.config.FARM_LOCATIONS:
                    for sensor_type in self.sensor_ranges.keys():
                        reading = self.generate_sensor_reading(sensor_type, farm_location)
                        topic = f"sensors/{sensor_type}"
                        
                        # Publish to MQTT
                        payload = json.dumps(reading)
                        self.client.publish(topic, payload)
                        
                        print(f"Published to {topic}: {reading['value']} {reading['unit']} from {reading['farm_location']}")
                
                time.sleep(self.config.SIMULATION_INTERVAL)
                
            except Exception as e:
                print(f"Error publishing sensor data: {e}")
                time.sleep(5)
    
    def start_simulation(self):
        """Start the sensor data simulation"""
        if self.connect_mqtt():
            self.running = True
            self.client.loop_start()
            
            # Start publishing in a separate thread
            publish_thread = threading.Thread(target=self.publish_sensor_data)
            publish_thread.daemon = True
            publish_thread.start()
            
            print("Sensor simulation started. Press Ctrl+C to stop.")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping sensor simulation...")
                self.stop_simulation()
        else:
            print("⚠️  MQTT broker not available - skipping sensor simulation")
            print("   Dashboard will use synthetic data instead")
            # Exit gracefully instead of crashing
            return
    
    def stop_simulation(self):
        """Stop the sensor data simulation"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        print("Sensor simulation stopped.")

class ERPDataSimulator:
    """Simulates ERP data for feed inventory, production metrics, etc."""
    
    def __init__(self):
        self.config = Config()
    
    def generate_feed_inventory_data(self) -> Dict[str, Any]:
        """Generate feed inventory data"""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'feed_type': random.choice(['Premium Pellets', 'Standard Feed', 'Organic Mix']),
            'quantity_kg': random.randint(500, 5000),
            'supplier': random.choice(['AquaFeed Co', 'Nordic Nutrition', 'Marine Feeds Ltd']),
            'expiry_date': (datetime.now() + timedelta(days=random.randint(30, 180))).isoformat(),
            'cost_per_kg': round(random.uniform(2.5, 4.5), 2),
            'location': random.choice([loc['name'] for loc in self.config.FARM_LOCATIONS])
        }
    
    def generate_production_data(self) -> Dict[str, Any]:
        """Generate production metrics data"""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'batch_id': f"BATCH_{random.randint(1000, 9999)}",
            'fish_count': random.randint(8000, 12000),
            'average_weight_kg': round(random.uniform(3.5, 6.0), 2),
            'mortality_rate': round(random.uniform(0.01, 0.05), 4),
            'feed_conversion_ratio': round(random.uniform(1.1, 1.8), 2),
            'growth_rate_percent': round(random.uniform(2.0, 4.5), 2),
            'location': random.choice([loc['name'] for loc in self.config.FARM_LOCATIONS])
        }

if __name__ == "__main__":
    # For testing the simulator
    simulator = SensorDataSimulator()
    simulator.start_simulation()
