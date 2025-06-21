"""
FinOps application entry point.
This is a wrapper around launch_app.py to maintain backwards compatibility.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the Python path to fix import issues
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Main entry point for the application."""
    logger.info("Starting AWS FinOps application...")
    
    # Import and run the launcher
    from launch_app import launch_streamlit
    launch_streamlit()


if __name__ == "__main__":
    main()
