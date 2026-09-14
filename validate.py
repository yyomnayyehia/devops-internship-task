#!/usr/bin/env python3
import urllib.request
import urllib.error
import json
import time
import socket
import sys

def print_pass(msg):
    print(f"[PASS] {msg}")

def print_fail(msg):
    print(f"[FAIL] {msg}")
    sys.exit(1)

print("Starting validation...")


max_retries = 15
ready = False
print("Waiting for environment to become ready...")
for _ in range(max_retries):
    try:
        urllib.request.urlopen("http://127.0.0.1:8090/health", timeout=2)
        ready = True
        break
    except Exception:
        time.sleep(2)

if not ready:
    print_fail("Environment did not become healthy in time.")

print_pass("Environment is up and responding.")

endpoints = ["/", "/health", "/ready", "/records", "/counter", "/instance"]
for ep in endpoints:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:8090{ep}", timeout=2)
        print_pass(f"Endpoint {ep} is accessible.")
    except Exception as e:
        print_fail(f"Endpoint {ep} failed: {e}")


seen = set()
for _ in range(10):
    try:
        resp = urllib.request.urlopen("http://127.0.0.1:8090/instance", timeout=2)
        data = json.loads(resp.read().decode())
        if "instance_id" in data:
            seen.add(data["instance_id"])
    except Exception:
        pass

if "app-01" in seen and "app-02" in seen:
    print_pass("Both app-01 and app-02 are successfully receiving traffic.")
else:
    print_fail(f"Load balancing failed. Only saw: {seen}")


print("Testing PostgreSQL write via /records...")
try:
    req = urllib.request.Request(
        "http://127.0.0.1:8090/records",
        data=json.dumps({"title": "validate-script-record"}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req, timeout=2)
    data = json.loads(resp.read().decode())
    if "record" in data:
        print_pass("PostgreSQL write successful.")
    else:
        print_fail(f"PostgreSQL write returned unexpected body: {data}")
except Exception as e:
    print_fail(f"PostgreSQL write failed: {e}")


print("Testing Redis write via /counter...")
try:
    resp = urllib.request.urlopen("http://127.0.0.1:8090/counter", timeout=2)
    data = json.loads(resp.read().decode())
    if "counter" in data:
        print_pass("Redis write successful.")
    else:
        print_fail(f"Redis write returned unexpected body: {data}")
except Exception as e:
    print_fail(f"Redis write failed: {e}")

print("Testing /ready reflects real dependency status...")
try:
    resp = urllib.request.urlopen("http://127.0.0.1:8090/ready", timeout=2)
    data = json.loads(resp.read().decode())

    expected = {
        "status": "ready",
        "dependencies": {
            "postgres": "ready",
            "redis": "ready",
        },
    }

    if data.get("status") != expected["status"]:
        print_fail(f"/ready reported unhealthy status: {data}")

    dependencies = data.get("dependencies", {})
    for name, required_status in expected["dependencies"].items():
        if dependencies.get(name) != required_status:
            print_fail(f"/ready reported {name} as unhealthy: {data}")

    print_pass(f"/ready confirmed PostgreSQL and Redis are ready: {data}")
except urllib.error.HTTPError as e:
    print_fail(f"/ready returned {e.code} — dependencies not healthy: {e.read().decode()}")
except Exception as e:
    print_fail(f"/ready check failed: {e}")


print("Testing network isolation...")
def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

for port, name in [(5432, "postgres"), (15432, "postgres (legacy)"),
                    (6379, "redis"), (16379, "redis (legacy)")]:
    if is_port_open(port):
        print_fail(f"{name} port {port} is exposed to the host!")

print_pass("Database ports are safely isolated.")

print("-" * 40)
print_pass("ALL TESTS PASSED SUCCESSFULLY!")
sys.exit(0)