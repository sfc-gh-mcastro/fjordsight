#!/usr/bin/env python3
"""
Simple Streamlit App Runner for FjordSight PoC
Runs just the dashboard without the full demo orchestration
"""
import subprocess
import sys
import os

def main():
    """Run the Streamlit dashboard"""
    print("🐟 Starting FjordSight Digital Farm Command Center Dashboard")
    print("="*60)
    
    try:
        # Change to the project directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Run Streamlit
        print("🖥️  Launching Streamlit dashboard...")
        print("🌐 Dashboard will be available at: http://localhost:8501")
        print("Press Ctrl+C to stop")
        print("="*60)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/streamlit_app/main.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Make sure all dependencies are installed: uv pip install -r requirements.txt")
        print("2. Check that Streamlit is installed: streamlit --version")
        print("3. Try running directly: streamlit run src/streamlit_app/main.py")

if __name__ == "__main__":
    main()
