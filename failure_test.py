#!/usr/bin/env python3
import urllib.request
import subprocess
import json
import time
import sys

PROJECT = "barq-assessment"

# Must be longer than nginx's own worst-case retry time:
# proxy_connect_timeout (2s) + proxy_read_timeout (3s) could be hit once per
# upstream tried, and proxy_next_upstream_tries allows up to 2 attempts.
# A 1s client timeout was cutting requests off before nginx's retry to the
# healthy backend could complete, showing up as false "errors" instead of
# successful failovers.
CLIENT_TIMEOUT = 5

def print_step(msg):
    print(f"\n--- {msg} ---")

def send_traffic(requests=50):
    stats = {"app-01": 0, "app-02": 0, "errors": 0}
    for _ in range(requests):
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:8090/instance", timeout=CLIENT_TIMEOUT)
            data = json.loads(resp.read().decode())
            instance = data.get("instance_id")
            if instance in stats:
                stats[instance] += 1
        except Exception:
            stats["errors"] += 1
        time.sleep(0.05)
    return stats

print_step("Phase 1: Initial Baseline")
baseline = send_traffic(20)
print(f"Traffic distribution: {baseline}")
if baseline["app-01"] == 0 or baseline["app-02"] == 0:
    print("[WARN] Load balancing seems uneven, but continuing...")

print_step("Phase 2: Inducing Failure (Stopping app-01)")
subprocess.run(["docker", "compose", "-p", PROJECT, "stop", "app-01"], check=True)
print("app-01 stopped. Waiting 3 seconds for NGINX to detect failure...")
time.sleep(3)

print_step("Phase 3: Measuring Availability During Failure")
failure_stats = send_traffic(50)
print(f"Traffic distribution: {failure_stats}")
if failure_stats["app-01"] > 0:
    print("[FAIL] app-01 is still receiving traffic? Test invalid.")
    sys.exit(1)
if failure_stats["app-02"] == 0:
    print("[FAIL] app-02 did not receive any traffic!")
    sys.exit(1)
print(f"[PASS] app-02 successfully handled {failure_stats['app-02']} requests.")
if failure_stats["errors"] > 0:
    print(f"[WARN] There were {failure_stats['errors']} errors during failover.")
else:
    print("[PASS] 0 errors during failure! High availability confirmed.")

print_step("Phase 4: Restoring Service (Starting app-01)")
subprocess.run(["docker", "compose", "-p", PROJECT, "start", "app-01"], check=True)
print("app-01 started. Polling until it receives traffic again...")

recovered = False
for _ in range(30):
    try:
        resp = urllib.request.urlopen("http://127.0.0.1:8090/instance", timeout=CLIENT_TIMEOUT)
        data = json.loads(resp.read().decode())
        if data.get("instance_id") == "app-01":
            recovered = True
            break
    except Exception:
        pass
    time.sleep(1)

if recovered:
    print("[PASS] app-01 has rejoined the load balancer pool successfully!")
    print("\n[PASS] FAILURE RECOVERY TEST COMPLETED SUCCESSFULLY!")
    sys.exit(0)
else:
    print("[FAIL] app-01 did not recover in time.")
    sys.exit(1)