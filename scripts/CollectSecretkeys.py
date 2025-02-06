from config_vars import SECRETS_JSONS_PATH
import json, os
from helper import execute_configdb_query

def collect_secretkeys(configdb_node, base_domain):
    query = f"select domain,secret from customers"
    output = execute_configdb_query(configdb_node, query)
    # Step 1: Process the lines
    lines = output.splitlines()

    # Step 2: Filter out the lines that don't contain data
    data_lines = [line for line in lines if '|' in line and not line.startswith('-')]
    # Step 3: Extract key-value pairs
    data_dict = {}
    for line in data_lines:
        if "|" in line:
            try:
                domain, secret = map(str.strip, line.split('|'))
                data_dict[domain] = secret
            except ValueError as ve:
                print(f"Error parsing line: {line} -> {ve}")

    # Step 4: Save the dictionary to a JSON file
    try:
        filepath = f"{SECRETS_JSONS_PATH}/{base_domain}.json"
        os.makedirs(SECRETS_JSONS_PATH, exist_ok=True)
        print(f"Saving to: {filepath}")
        with open(filepath, 'w') as f:
            json.dump(data_dict, f, indent=4)
        print("Data saved to JSON file:", filepath)
    except Exception as e:
        print(f"Error writing to JSON file: {e}")
    return data_dict

   