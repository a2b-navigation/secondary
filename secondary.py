import subprocess
import actuation
import threading
import requests
import time
import sys

# Runs a command on the terminal and returns the output
def run_command(command):
    return subprocess.check_output(command, shell=True).decode("utf-8").split("\n")[:-1]

# Makes a request to the primary device
def get(url):
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp
        else:
            print(f"[Requests] Recieved HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"[Requests] Got back error: {e}")
        return None

# The mac address of the primary device
mac = "ae:d2:85:b5:52:ff"
hard_code = "06:70:4d:43:ac:54"

# Try and locate it and get the IP address of the primary device
while True:
    print("[Server Locator] Attempting to find primary device")
    neighbours = run_command("ip neigh")

    ip = None

    for n in neighbours:
        pieces = n.split(" ")
        if pieces[4] == mac or (pieces[4] == hard_code and pieces[0].startswith("192")):
            ip = pieces[0]

    if ip is None:
        print(f"[Server Locator] Unable to find primary device on network!\n")
        neighbour_command = "\n".join(neighbours)
        print(f"Output of 'ip neigh':\n{neighbour_command}")
        sys.exit(1)
    try:
        status = requests.get(f"http://{ip}:5000/other").status_code
    except Exception as e:
        print(f"[Server Locator] Connection errored: {e}")
        time.sleep(1)
        continue

    if status == 200:
        ip += ":5000"
        print(f"[Server Locator] Primary device located and connection established")
        break
    else:
        print(f"[Server Locator] Primary device malfunctioning! Recieved HTTP {status}")
        time.sleep(1)
        continue

pattern = "none"
lock = False

def update_pattern():
    global pattern
    global lock
    lock = True
    request = get(f"http://{ip}/other")
    if request is not None:
        pattern = request.text.strip()
        print(f"[Actuation] Received pattern {pattern}")
    lock = False

# Continually check for actuation pattern and perform it
while True:
    if not lock:
        t = threading.Thread(target=update_pattern, daemon=True)
        t.start()
    match pattern:
        case "none": time.sleep(1)
        case "very_far": actuation.very_far()
        case "far": actuation.far()
        case "near": actuation.near()
        case "very_near": actuation.very_near()
    else:
        print("[Actuation] Cycle failed, retrying...")
        time.sleep(1)
