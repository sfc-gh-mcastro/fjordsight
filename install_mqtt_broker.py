#!/usr/bin/env python3
"""
MQTT Broker Setup for FjordSight PoC
Installs and starts a local MQTT broker for the demo
"""
import subprocess
import sys
import time
import shutil
import platform

def install_mosquitto():
    """Install Mosquitto MQTT broker"""
    system = platform.system().lower()
    
    print("📦 Installing Mosquitto MQTT broker...")
    
    try:
        if system == "darwin":  # macOS
            print("   Installing with Homebrew...")
            subprocess.check_call(["brew", "install", "mosquitto"])
            
        elif system == "linux":
            # Try different package managers
            try:
                subprocess.check_call(["sudo", "apt-get", "update"])
                subprocess.check_call(["sudo", "apt-get", "install", "-y", "mosquitto", "mosquitto-clients"])
            except subprocess.CalledProcessError:
                try:
                    subprocess.check_call(["sudo", "yum", "install", "-y", "mosquitto"])
                except subprocess.CalledProcessError:
                    subprocess.check_call(["sudo", "dnf", "install", "-y", "mosquitto"])
        
        else:
            print(f"❌ Unsupported system: {system}")
            print("   Please install Mosquitto manually:")
            print("   - Windows: Download from https://mosquitto.org/download/")
            print("   - Linux: sudo apt-get install mosquitto")
            print("   - macOS: brew install mosquitto")
            return False
        
        print("✅ Mosquitto installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Mosquitto: {e}")
        return False
    except FileNotFoundError as e:
        if "brew" in str(e):
            print("❌ Homebrew not found. Please install Homebrew first:")
            print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        else:
            print(f"❌ Package manager not found: {e}")
        return False

def start_mosquitto():
    """Start Mosquitto MQTT broker"""
    print("\n🚀 Starting Mosquitto MQTT broker...")
    
    try:
        # Check if mosquitto is already running
        result = subprocess.run(["pgrep", "mosquitto"], capture_output=True)
        if result.returncode == 0:
            print("✅ Mosquitto is already running")
            return True
        
        # Start mosquitto
        if platform.system().lower() == "darwin":
            # macOS with Homebrew
            subprocess.Popen([
                "brew", "services", "start", "mosquitto"
            ])
            time.sleep(2)
            
            # Check if it started
            result = subprocess.run(["pgrep", "mosquitto"], capture_output=True)
            if result.returncode == 0:
                print("✅ Mosquitto started successfully with brew services")
                return True
            else:
                # Try starting directly
                subprocess.Popen(["mosquitto"])
                time.sleep(2)
                print("✅ Mosquitto started directly")
                return True
        
        else:
            # Linux
            subprocess.check_call(["sudo", "systemctl", "start", "mosquitto"])
            print("✅ Mosquitto started with systemctl")
            return True
        
    except Exception as e:
        print(f"❌ Failed to start Mosquitto: {e}")
        print("💡 You can start it manually:")
        print("   macOS: brew services start mosquitto")
        print("   Linux: sudo systemctl start mosquitto")
        return False

def check_mqtt_broker():
    """Check if MQTT broker is available"""
    print("🔍 Checking for MQTT broker...")
    
    if shutil.which("mosquitto"):
        print("✅ Mosquitto is installed")
        return True
    else:
        print("❌ Mosquitto not found")
        return False

def main():
    """Main setup function"""
    print("🐟 FjordSight PoC - MQTT Broker Setup")
    print("=" * 50)
    
    if check_mqtt_broker():
        if start_mosquitto():
            print("\n🎉 MQTT broker is ready!")
            print("✅ You can now run the full demo with real-time sensor simulation:")
            print("   python run_demo.py")
        else:
            print("\n⚠️  MQTT broker installation found but couldn't start")
            print("🎯 No problem! Dashboard works great without MQTT:")
            print("   python run_streamlit.py")
    else:
        print("\n🤔 Would you like to install Mosquitto MQTT broker? (y/n): ", end="")
        response = input().lower()
        
        if response in ['y', 'yes']:
            if install_mosquitto() and start_mosquitto():
                print("\n🎉 MQTT broker setup completed!")
                print("✅ You can now run the full demo:")
                print("   python run_demo.py")
            else:
                print("\n⚠️  MQTT setup failed, but demo still works:")
                print("   python run_streamlit.py")
        else:
            print("\n✅ No problem! Dashboard works perfectly without MQTT:")
            print("   python run_streamlit.py")

if __name__ == "__main__":
    main()
