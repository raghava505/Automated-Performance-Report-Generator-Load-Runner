import requests
import configparser
import uuid 
import json
import concurrent.futures
import time
import threading
import pickle
import zmq
import subprocess
import sys

import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suppress only InsecureRequestWarning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Your HTTPS request code goes here


import argparse

# Set up the argument parser
parser = argparse.ArgumentParser(description="Process input arguments for the script.")

# Add arguments for domain, secret, and data_assets
parser.add_argument("--domain", type=str, required=True, help="The domain name.")
parser.add_argument("--secret", type=str, required=True, help="The secret key.")
parser.add_argument("--data_assets", type=int, required=False, help="Data Assets.")
parser.add_argument("--controlplane_assets", type=int, required=False, help="Controlplane Assets.")

# Parse the arguments
args = parser.parse_args()

# Assign values to variables
domain = args.domain
secret = args.secret
data_assets = args.data_assets
controlplane_assets = args.controlplane_assets

# Print the values (optional, for verification)
print(f"Domain: {domain}")
print(f"Secret: {secret}")
print(f"Number of Data Assets: {data_assets}")
print(f"Number of ControlPlane Assets: {controlplane_assets}")

if data_assets and controlplane_assets :
    print("Wrong command : Do not pass both data_assets and controlplane_assets arguments in the same request. Exiting... ")
    sys.exit(1)

if data_assets is None and controlplane_assets is None:
    print("Wrong command : Pass any one of these arguments -> '--data_assets' or '--controlplane_assets' in the request. Exiting... ")
    sys.exit(1)


final_num_of_assets = data_assets if data_assets is not None else controlplane_assets
print(final_num_of_assets)

hostname = subprocess.run("hostname",shell=True,capture_output=True,text=True).stdout.strip()

port = 5555

# secret = "d897f2f2-6032-4fb0-acf9-d11bacde2397"
# Authorisation1= "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJISUhaUUNQTlpZSTJRVVNYTENFR0pIR05RMklCQ1VQWCIsImV4cCI6NDg4NjYzMzIwN30.3xuYZGy3ixUGdk3waFS5lzI5cGmK-X8IrlzXYvyaqXs"
domain_url = f"{domain}.uptycs.net"

enroll_url = f"https://{domain_url}/agent/enroll"
config_url = f"https://{domain_url}/agent/config"
log_url = f"https://{domain_url}/agent/log"
distributedread_url = f"https://{domain_url}/agent/distributed_read"
distributedwrite_url = f"https://{domain_url}/agent/distributed_write"

session = requests.Session()

headers = {
    # "Authorization": Authorisation1,
    "Content-Type": "application/json",
    "user-agent": "osquery/4.6.5.9-Uptycs-Protect"
}

def generate_enrol_body(customer_secret,asset_id):
    current_hostname = f"endpointsim-{domain}-{hostname}-{asset_id}"
    return {
        "enroll_secret": customer_secret,
        "host_identifier": asset_id,
        "platform_type": "darwin",
        "host_details": {
            "os_version": {
                "_id": "18.04",
                "arch": "x86_64",
                "codename": "bionic",
                "major": "18",
                "minor": "04",
                "name": "Ubuntu",
                "patch": "0",
                "platform": "alpine",
                "platform_like": "debian",
                "pretty_name": "Ubuntu 18.04.5 LTS",
                "system_id": asset_id,
                "system_type": "host",
                "version": "18.04.5 LTS (Bionic Beaver)"
            },
            "osquery_info": {
                "build_distro": "xenial",
                "build_platform": "ubuntu",
                "config_hash": "",
                "config_valid": "0",
                "extensions": "inactive",
                "instance_id": "d6ddc831-1425-4981-9ea3-2987a1289dba",
                "pid": "9088",
                "platform_mask": "9",
                "start_time": "1628628472",
                "uuid": "fc3548b6-34ea-11ea-80db-f875a48d30b4",
                "version": "4.6.5.9-Uptycs-Protect",
                "watcher": "9084"
            },
            "platform_info": {
                "address": "0xe000",
                "date": "11/23/2019",
                "extra": "",
                "revision": "1.35",
                "size": "10485760",
                "vendor": "LENOVO",
                "version": "BHCN35WW",
                "volume_size": "0"
            },
            "system_info": {
                "board_model": "LNVNB161216",
                "board_serial": "PF1X7R9N",
                "board_vendor": "LENOVO",
                "board_version": "SDK0Q55722 WIN",
                "computer_name": current_hostname,
                "cpu_brand": "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000",
                "cpu_logical_cores": "12",
                "cpu_microcode": "0xea",
                "cpu_physical_cores": "6",
                "cpu_subtype": "158",
                "cpu_type": "x86_64",
                "hardware_model": "81SX",
                "hardware_serial": "PF1X7R9N",
                "hardware_vendor": "LENOVO",
                "hardware_version": "Lenovo Legion Y540-15IRH",
                "hostname": current_hostname,
                "local_hostname": current_hostname,
                "physical_memory": "25093697536",
                "uuid": asset_id,
            }
        }
    }

def enroll_asset(asset_id, customer_secret, results_lock, hostid_nodekey_mapping):
    try:
        enrol_body = generate_enrol_body(customer_secret, asset_id)
        response = session.post(enroll_url, headers=headers, json=enrol_body, verify=False)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        node_key = json.loads(response.text)["node_key"]
        
        # Save the result in a thread-safe manner
        with results_lock:
            hostid_nodekey_mapping[asset_id] = node_key
    except Exception as e:
        print(f"Failed to enroll asset {asset_id}: {e}")

print_lock = threading.Lock()
def send_config(asset_params):
    asset_id,node_key = asset_params
    try:
        config_payload = {"node_key": node_key}
        response = session.post(config_url, headers=headers, json=config_payload, verify=False,  timeout=1000)
        with print_lock:
            print(f"Asset {asset_id} sent config: {response.status_code}")
    except Exception as e:
        with print_lock:
            print(f"Asset {asset_id} failed config call: {e}")

d = {}
def send_log(asset_id, node_key, message, unix_timestamp, max_retries=5, retry_delay=5):
    message["node_key"] = node_key
    updated_data_key = [
        {**msg, "hostIdentifier": asset_id, "unixTime": str(unix_timestamp)}
        for msg in message["data"]
    ]
    message["data"] = updated_data_key

    attempt = 0
    while True:
        try:
            response = session.post(log_url, headers=headers, json=message, verify=False, timeout=1000)
            if response.status_code == 200:
                if attempt!=0:
                    print(f"Asset {asset_id} sent data successfully in attemt{attempt}. Response: {response.status_code}")
                break
            else:
                print(f"Asset {asset_id} received non-200 status: {response.status_code}. Retrying...")
        except Exception as e:
            print(f"Asset {asset_id} failed to send message: {e}. Retrying...")

        attempt += 1
        if max_retries is not None and attempt >= max_retries:
            print(f"Asset {asset_id} failed after {max_retries} retries. Aborting.")
            break
        time.sleep(retry_delay)


def start_consumer():
    context = zmq.Context()
    while True:
        try:
            socket = context.socket(zmq.SUB)
            socket.connect(f"tcp://127.0.0.1:{port}")
            socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

            print(f"Consumer started.")

            while True:
                try:
                    # Receive message
                    message = socket.recv_json(flags=zmq.NOBLOCK)  # Use non-blocking mode
                    unix_timestamp = message[:10]
                    message = json.loads(message[10:])
                    def wrapped_send_log(params):
                        asset_id, node_key = params
                        send_log(asset_id, node_key, message, unix_timestamp)
                    with concurrent.futures.ThreadPoolExecutor(max_workers=min(final_num_of_assets, 20)) as executor:
                        executor.map(wrapped_send_log, hostid_nodekey_mapping.items())

                except zmq.Again:
                    # No message received; retry
                    time.sleep(1)
                except Exception as e:
                    print(f"Consumer encountered an error: {e}")
                    break  # Exit loop to recreate the socket
                # time.sleep(2)
        except Exception as e:
            print(f"Consumer failed to connect: {e}")
            time.sleep(1)  # Retry after a short delay


def schedule_tasks(hostid_nodekey_mapping):
    def config_task():
        print("Starting config API calls...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(final_num_of_assets, 5)) as executor:
            executor.map(send_config, hostid_nodekey_mapping.items())
        print("Config API calls completed.")

    if data_assets:
        threading.Thread(target=start_consumer).start()
    time.sleep(1)
    while True:
        threading.Thread(target=config_task).start()
        time.sleep(300)
    session.close()

if True:
    hostid_nodekey_mapping = {}
    results_lock = threading.Lock()  # Lock to ensure thread-safe access to the dictionary

    # Create and start threads for enrolling assets
    threads = []
    for i in range(final_num_of_assets):
        asset_id = str(uuid.uuid4())
        enroll_asset(asset_id, secret, results_lock, hostid_nodekey_mapping)
        # thread = threading.Thread(target=enroll_asset, args=(asset_id, secret, results_lock, hostid_nodekey_mapping))
    #     threads.append(thread)
    #     thread.start()

    # for thread in threads:     # Wait for all threads to finish
    #     thread.join()
else :
    with open(f"{domain}.pkl", 'rb') as file:
        loaded_dict = pickle.load(file)
        connection_params = loaded_dict["connection_params"]
        hostid_nodekey_mapping = loaded_dict["hostid_nodekey_mapping"]
    print(f"Dictionary loaded from {domain}.pkl")

# hostid_nodekey_mapping={'f4600f7a-d70e-4a57-ad67-a594dc8417f3': '4cfa8006-fcf2-49dc-8f8e-96087785c6c9:f4600f7a-d70e-4a57-ad67-a594dc8417f3:asset:asset:jupiter100'}
# print(hostid_nodekey_mapping)
# send_log(next(iter(hostid_nodekey_mapping.items())))


connection_params = {
    "domain":domain,
    "domain_url":domain_url,
    "secret":secret,
    # "Authorisation1":Authorisation1,
    "data_assets":data_assets,
    "controlplane_assets":controlplane_assets,
    "headers":headers
}

print("connection_params : ",connection_params)

# with open(f"{domain}.pkl", 'wb') as file:
#     pickle.dump({"connection_params":connection_params,"hostid_nodekey_mapping":hostid_nodekey_mapping}, file)
# print(f"Dictionary saved to {domain}.pkl")

schedule_tasks(hostid_nodekey_mapping)

# nohup /usr/bin/python3 /Users/masabathulararao/Documents/jmeter-tool/scripts/enroll.py > raghava.out 2>&1 &