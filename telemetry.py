import random
import time
from datetime import datetime


def generate_telemetry():
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": round(random.uniform(20, 35), 2),
        "battery": round(random.uniform(60, 100), 2),
        "altitude": round(random.uniform(500, 550), 2),
        "signal": round(random.uniform(-90, -60), 2),
        "voltage": round(random.uniform(11, 14), 2),
    }


if __name__ == "__main__":
    while True:
        telemetry = generate_telemetry()

        print("\n========== SATELLITE TELEMETRY ==========")
        print(f"Time:        {telemetry['timestamp']}")
        print(f"Temperature: {telemetry['temperature']} °C")
        print(f"Battery:     {telemetry['battery']} %")
        print(f"Altitude:    {telemetry['altitude']} km")
        print(f"Signal:      {telemetry['signal']} dBm")
        print(f"Voltage:     {telemetry['voltage']} V")
        print("==========================================")

        time.sleep(2)
