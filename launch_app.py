#!/usr/bin/env python3
"""
Launcher script for the FinOps Streamlit application.
This script ensures the Python path is set correctly for imports.
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def launch_streamlit():
    """Launch the Streamlit application with correct Python path."""
    # Add the current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
        
    print("Starting FinOps Streamlit application...")
    
    # Launch Streamlit
    streamlit_cmd = [
        "streamlit", "run", 
        os.path.join(current_dir, "app", "app.py"),
        "--browser.serverAddress=localhost",
        "--server.port=8501"
    ]
    
    try:
        subprocess.run(streamlit_cmd)
    except KeyboardInterrupt:
        print("\nShutting down Streamlit application...")
    except Exception as e:
        print(f"Error running Streamlit: {str(e)}")

if __name__ == "__main__":
    launch_streamlit()
