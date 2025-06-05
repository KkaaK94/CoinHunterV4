import os
import json
import psutil
from datetime import datetime

def write_healthcheck(file_path="runtime/healthcheck.json"):
    try:
        process = psutil.Process(os.getpid())
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(interval=1),
            "memory_info": process.memory_info()._asdict()
        }
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(health_status, f, indent=4)
    except Exception as e:
        print(f"Healthcheck Error: {e}")
