#!/usr/bin/env python3
"""
FjordSight PoC Demo Runner
Orchestrates the complete demonstration flow
"""
import subprocess
import sys
import time
import threading
from datetime import datetime
import signal
import os

class FjordSightDemo:
    """Orchestrates the complete FjordSight PoC demonstration"""
    
    def __init__(self):
        self.processes = []
        self.running = False
        
    def print_banner(self):
        """Print demo banner"""
        print("=" * 70)
        print("🐟 FjordSight Digital Farm Command Center - PoC Demo")
        print("=" * 70)
        print("Demonstrating unified IT/OT data with AI-powered insights")
        print("for sustainable salmon farming operations")
        print("=" * 70)
        print()
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("📋 Checking dependencies...")
        
        required_packages = [
            'streamlit', 'pandas', 'numpy', 'plotly', 
            'scikit-learn', 'snowflake-connector-python',
            'paho-mqtt'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                # Handle special package name mappings
                import_name = package.replace('-', '_')
                if package == 'scikit-learn':
                    import_name = 'sklearn'
                elif package == 'paho-mqtt':
                    import_name = 'paho.mqtt'
                elif package == 'snowflake-connector-python':
                    import_name = 'snowflake.connector'
                
                __import__(import_name)
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package} - MISSING")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("Please run: pip install -r requirements.txt")
            return False
        
        print("✅ All dependencies satisfied!")
        return True
    
    def start_mqtt_simulator(self):
        """Start MQTT sensor data simulator"""
        print("\n🌊 Starting MQTT sensor data simulator...")
        
        try:
            process = subprocess.Popen([
                sys.executable, 
                "src/data_ingestion/mqtt_simulator.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(("MQTT Simulator", process))
            print("✅ MQTT simulator started (PID: {})".format(process.pid))
            
            # Give it a moment to start and check if it's still running
            time.sleep(3)
            
            # Check if process is still alive
            if process.poll() is None:
                print("✅ MQTT simulator running successfully")
                return True
            else:
                print("⚠️  MQTT simulator exited (likely no MQTT broker available)")
                print("   This is normal - dashboard will use synthetic data")
                return True  # Still return True to continue demo
            
        except Exception as e:
            print(f"❌ Failed to start MQTT simulator: {e}")
            print("   Dashboard will work with synthetic data")
            return True  # Continue demo even if MQTT fails
    
    def start_data_ingestion(self):
        """Start Snowflake data ingestion"""
        print("\n📊 Starting Snowflake data ingestion...")
        
        try:
            process = subprocess.Popen([
                sys.executable, 
                "src/data_ingestion/snowflake_ingestion.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(("Data Ingestion", process))
            print("✅ Data ingestion started (PID: {})".format(process.pid))
            
            # Give it a moment to start and check if it's still running
            time.sleep(3)
            
            # Check if process is still alive
            if process.poll() is None:
                print("✅ Data ingestion running successfully")
                return True
            else:
                print("⚠️  Data ingestion exited (likely MQTT broker unavailable)")
                print("   This is normal - dashboard will use Snowflake data directly")
                return True  # Still return True to continue demo
            
        except Exception as e:
            print(f"❌ Failed to start data ingestion: {e}")
            print("   Dashboard will work with existing Snowflake data")
            return True  # Continue demo even if ingestion fails
    
    def train_hab_model(self):
        """Train the HAB prediction model"""
        print("\n🧠 Training HAB prediction model...")
        
        try:
            process = subprocess.run([
                sys.executable, 
                "-c", 
                "from src.models.hab_prediction_model import HABPredictionModel; "
                "model = HABPredictionModel(); "
                "success = model.train_model(); "
                "print('Model training completed!' if success else 'Model training failed!')"
            ], capture_output=True, text=True, timeout=120)
            
            if process.returncode == 0:
                print("✅ HAB model trained successfully!")
                return True
            else:
                print(f"❌ HAB model training failed: {process.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ HAB model training timed out (using demo mode)")
            return True
        except Exception as e:
            print(f"❌ Failed to train HAB model: {e}")
            print("ℹ️  Demo will use synthetic predictions")
            return True  # Continue with demo even if training fails
    
    def start_streamlit_dashboard(self):
        """Start the Streamlit dashboard"""
        print("\n🖥️  Starting Streamlit dashboard...")
        
        try:
            process = subprocess.Popen([
                sys.executable, 
                "-m", "streamlit", "run", 
                "src/streamlit_app/main.py",
                "--server.port", "8501",
                "--server.headless", "true"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(("Streamlit Dashboard", process))
            print("✅ Streamlit dashboard started (PID: {})".format(process.pid))
            print("🌐 Dashboard available at: http://localhost:8501")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Streamlit dashboard: {e}")
            return False
    
    def show_demo_instructions(self):
        """Show demo walkthrough instructions"""
        print("\n" + "="*70)
        print("🎯 DEMO WALKTHROUGH INSTRUCTIONS")
        print("="*70)
        
        print("\n📋 Vignette 1: Unified IT/OT Data Foundation")
        print("   1. Open dashboard at http://localhost:8501")
        print("   2. Navigate to 'Dashboard' tab")
        print("   3. Observe real-time sensor data streaming")
        print("   4. Switch between different farm locations")
        print("   5. Show harmonized environmental + production data")
        
        print("\n🚨 Vignette 2: HAB Early Warning System")
        print("   1. Click on 'HAB Risk' tab")
        print("   2. Observe real-time risk assessment gauge")
        print("   3. Review contributing risk factors")
        print("   4. Show automated recommendations")
        print("   5. Demonstrate anomaly detection alerts")
        
        print("\n🤖 Vignette 3: AI Sales Co-Pilot")
        print("   1. Go to 'Sales Co-Pilot' tab")
        print("   2. Enter a production scenario (volume mismatch)")
        print("   3. Generate AI-powered customer recommendations")
        print("   4. Review prioritized calling list with reasons")
        print("   5. Demonstrate turning problems into profit opportunities")
        
        print("\n🗺️  Additional Features:")
        print("   • Interactive farm location map")
        print("   • Real-time KPI monitoring")
        print("   • Historical trend analysis")
        print("   • Data quality scoring")
        
        print("\n" + "="*70)
        print("💡 KEY MESSAGES TO EMPHASIZE:")
        print("="*70)
        print("✅ Unified platform eliminates data silos")
        print("✅ Near real-time processing (< 1 minute latency)")
        print("✅ AI-driven insights enable proactive decisions")
        print("✅ Scalable architecture grows with business")
        print("✅ Governed access for all user types")
        print("="*70)
    
    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            for name, process in self.processes:
                if process.poll() is not None:
                    print(f"⚠️  {name} process terminated unexpectedly")
            time.sleep(5)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down demo...")
        self.stop_demo()
    
    def stop_demo(self):
        """Stop all demo processes"""
        print("\n🛑 Stopping demo processes...")
        self.running = False
        
        for name, process in self.processes:
            if process.poll() is None:
                print(f"   Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   Force killing {name}...")
                    process.kill()
        
        print("✅ Demo stopped successfully!")
        sys.exit(0)
    
    def run_demo(self):
        """Run the complete demo"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.print_banner()
        
        # Check dependencies
        if not self.check_dependencies():
            sys.exit(1)
        
        # Start components in order
        print("\n🚀 Starting demo components...")
        
        # 1. Start MQTT simulator
        if not self.start_mqtt_simulator():
            print("❌ Failed to start MQTT simulator")
            sys.exit(1)
        
        # 2. Start data ingestion (optional - demo works without Snowflake)
        self.start_data_ingestion()
        
        # 3. Train HAB model (optional - demo has fallback)
        self.train_hab_model()
        
        # 4. Start Streamlit dashboard
        if not self.start_streamlit_dashboard():
            print("❌ Failed to start dashboard")
            self.stop_demo()
            sys.exit(1)
        
        # Start monitoring
        self.running = True
        monitor_thread = threading.Thread(target=self.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Show instructions
        time.sleep(3)  # Wait for dashboard to start
        self.show_demo_instructions()
        
        # Keep demo running
        try:
            print(f"\n⏰ Demo started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("Press Ctrl+C to stop the demo")
            
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.stop_demo()

if __name__ == "__main__":
    demo = FjordSightDemo()
    demo.run_demo()
