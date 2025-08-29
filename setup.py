"""
FjordSight PoC Setup Script
Prepares the environment for the demonstration
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "models",
        "data/raw",
        "data/processed",
        "outputs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Try uv first (faster), fallback to pip
    try:
        subprocess.check_call(["uv", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully with uv!")
        return True
    except FileNotFoundError:
        print("⚠️  uv not found, falling back to pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencies installed successfully with pip!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies with pip: {e}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies with uv: {e}")
        print("💡 Tip: Install uv for faster package management: https://github.com/astral-sh/uv")
        return False

def setup_config():
    """Setup configuration file"""
    config_example = Path("config.py")
    
    if config_example.exists():
        print("✅ Configuration file already exists")
        return True
    
    print("⚙️  Please configure your Snowflake credentials in config.py")
    print("   (The demo will work with synthetic data if Snowflake is not available)")
    return True

def check_optional_dependencies():
    """Check for optional dependencies"""
    print("\n🔍 Checking optional dependencies...")
    
    optional_deps = {
        "mosquitto": "MQTT broker (for realistic sensor simulation)",
        "docker": "Container runtime (for production deployment)"
    }
    
    for dep, description in optional_deps.items():
        if shutil.which(dep):
            print(f"✅ {dep} - {description}")
        else:
            print(f"⚠️  {dep} - {description} (optional)")

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🎉 FjordSight PoC Setup Complete!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. Configure Snowflake credentials in config.py (optional)")
    print("2. Run the demo: python run_demo.py")
    print("3. Or start components individually:")
    print("   • MQTT Simulator: python src/data_ingestion/mqtt_simulator.py")
    print("   • Streamlit Dashboard: streamlit run src/streamlit_app/main.py")
    
    print("\n🌐 Demo URLs:")
    print("• Streamlit Dashboard: http://localhost:8501")
    
    print("\n📚 Documentation:")
    print("• README.md - Complete setup and usage guide")
    print("• docs/PRD.md - Product Requirements Document")
    print("• notebooks/ - Jupyter notebooks for model development")
    
    print("\n🎯 Demo Highlights:")
    print("• Real-time sensor data visualization")
    print("• HAB (Harmful Algal Bloom) risk prediction")
    print("• AI-powered sales recommendations")
    print("• Unified IT/OT data dashboard")
    
    print("="*60)

def main():
    """Main setup function"""
    print("🐟 FjordSight PoC - Setup Script")
    print("="*40)
    
    # Create directories
    print("\n📁 Creating project directories...")
    create_directories()
    
    # Install dependencies
    print("\n📦 Setting up Python environment...")
    if not install_dependencies():
        print("❌ Setup failed. Please install dependencies manually.")
        sys.exit(1)
    
    # Setup configuration
    print("\n⚙️  Setting up configuration...")
    setup_config()
    
    # Check optional dependencies
    check_optional_dependencies()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
