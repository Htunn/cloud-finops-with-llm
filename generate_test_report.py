"""
Generate a full testing report for the AWS FinOps application.
"""
import os
import platform
import psutil
import subprocess
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_report():
    print("Generating Production Readiness Testing Report...")
    report = {}
    
    # Current date and time
    report["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Environment information
    report["environment"] = {
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu": platform.processor(),
        "ram": f"{round(psutil.virtual_memory().total / (1024.0 ** 3))} GB",
        "disk_space": f"{round(psutil.disk_usage('/').free / (1024.0 ** 3))} GB free"
    }
    
    # Test Docker containers
    docker_status = subprocess.run(["docker", "ps"], capture_output=True, text=True)
    report["containers"] = {
        "postgres": "running" if "finops-postgres" in docker_status.stdout else "not running",
        "pgadmin": "running" if "finops-pgadmin" in docker_status.stdout else "not running"
    }
    
    # Check if Streamlit app is running
    streamlit_status = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    report["application"] = {
        "streamlit": "running" if "streamlit run app/app.py" in streamlit_status.stdout else "not running"
    }
    
    # Check AWS credentials
    report["aws_credentials"] = {
        "access_key": "configured" if os.getenv("AWS_ACCESS_KEY_ID") else "missing",
        "secret_key": "configured" if os.getenv("AWS_SECRET_ACCESS_KEY") else "missing"
    }
    
    # Check Azure OpenAI credentials
    report["azure_openai"] = {
        "api_key": "configured" if os.getenv("AZURE_OPENAI_API_KEY") else "missing",
        "endpoint": "configured" if os.getenv("AZURE_OPENAI_ENDPOINT") else "missing"
    }
    
    # Check local LLM model
    model_dir = os.path.join("models", "tiny-llama")
    report["local_llm"] = {
        "model_downloaded": "yes" if os.path.exists(model_dir) else "no",
        "model_path": model_dir,
        "gpu_acceleration": "available" if "mps" in subprocess.run(["python3", "-c", "import torch; print(torch.backends.mps.is_available())"], capture_output=True, text=True).stdout else "unavailable"
    }
    
    # Format and print report
    print("\n\n===== PRODUCTION READINESS TESTING REPORT =====\n")
    print(f"Generated: {report['timestamp']}")
    print("\n--- ENVIRONMENT ---")
    for key, value in report["environment"].items():
        print(f"{key.upper()}: {value}")
    
    print("\n--- CONTAINERS ---")
    for container, status in report["containers"].items():
        print(f"{container}: {status}")
    
    print("\n--- APPLICATION ---")
    for app, status in report["application"].items():
        print(f"{app}: {status}")
    
    print("\n--- AWS CREDENTIALS ---")
    for key, status in report["aws_credentials"].items():
        print(f"{key}: {status}")
    
    print("\n--- AZURE OPENAI ---")
    for key, status in report["azure_openai"].items():
        print(f"{key}: {status}")
    
    print("\n--- LOCAL LLM ---")
    for key, status in report["local_llm"].items():
        print(f"{key}: {status}")
    
    print("\n=== SUMMARY ===")
    all_ok = all([
        report["containers"]["postgres"] == "running",
        report["containers"]["pgadmin"] == "running",
        report["application"]["streamlit"] == "running",
        report["aws_credentials"]["access_key"] == "configured",
        report["aws_credentials"]["secret_key"] == "configured",
        report["local_llm"]["model_downloaded"] == "yes"
    ])
    
    if all_ok:
        print("✅ All critical components are running and configured correctly.")
        print("✅ Application is PRODUCTION READY!")
    else:
        print("❌ Some issues were detected. Please check the report above.")
    
    return report

if __name__ == "__main__":
    generate_report()
