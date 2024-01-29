import json
import socket,paramiko
import concurrent.futures
import re
import requests
from collections import defaultdict

def execute_command_in_node(node,command,prom_con_obj):
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys() 
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(node, prom_con_obj.ssh_port, prom_con_obj.abacus_username, prom_con_obj.abacus_password)
            stdin, stdout, stderr = client.exec_command(command)
            out = stdout.read().decode('utf-8').strip()
            errors = stderr.read().decode('utf-8')
            if errors:
                print("Errors:")
                print(errors)
            if out and out!='':
                print(f"Fetched '{command}' output for {node} : {out}")
                return out
            else:
                raise RuntimeError(f"ERROR : Unable to run command : '{command}'  in {node} , {e}")
                
        except Exception as e:
            raise RuntimeError(f"ERROR : Unable to connect to {node} , {e}") from e
        finally:
            client.close()
    except socket.gaierror as e:
        raise RuntimeError(f"ERROR : Unable to connect to {node} , {e}") from e

def execute_trino_query(node,query,prom_con_obj):
    trino_command = f"sudo -u monkey TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --insecure --server https://localhost:5665 --schema upt_system --user uptycs --catalog uptycs --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/etc/presto/presto.jks --execute \"{query}\""
    return execute_command_in_node(node,trino_command,prom_con_obj)

def execute_configdb_query(node,query,prom_con_obj):
    configdb_command = f'sudo docker exec postgres-configdb bash -c "PGPASSWORD=pguptycs psql -U postgres configdb -c \"{query}\""'
    return execute_command_in_node(node,configdb_command,prom_con_obj)

def execute_point_prometheus_query(prom_con_obj,timestamp,query):    
    PARAMS = {
        'query': query,
        'time' : timestamp
    }
    print(f"Executing {query} at {prom_con_obj.monitoring_ip} at a single timestamp {timestamp}...")
    try:
        response = requests.get(prom_con_obj.prometheus_path + prom_con_obj.prom_point_api_path, params=PARAMS)
        if response.status_code != 200:
            raise RuntimeError(f"API request failed with status code {response.status_code}")
        result = response.json()['data']['result']
        if len(result)==0:
            print(f"WARNING : No data found for : {query}")
            return None
        return result

    except requests.RequestException as e:
        raise RuntimeError(f"API request failed with an exception {e}")

def execute_prometheus_query(prom_con_obj,start_timestamp,end_timestamp,query,hours):
    PROMETHEUS = prom_con_obj.prometheus_path
    API_PATH = prom_con_obj.prom_api_path
    step=60
    points_per_min = 60/step
    points_per_hour = points_per_min*60
    PARAMS = {
        'query': query,
        'start': start_timestamp,
        'end': end_timestamp,
        'step':step
    }
    print(f"Executing {query} at {prom_con_obj.monitoring_ip} ...")

    try:
        response = requests.get(PROMETHEUS + API_PATH, params=PARAMS)
        if response.status_code != 200:
            print(f"API request failed with status code {response.status_code}")
            return None
        result = response.json()['data']['result']
        if len(result)==0:
            print(f"WARNING : No data found for : {query}")
            return None
        for line in result:
            temp = line["metric"]
            line["metric"] = defaultdict(lambda: None)
            line["metric"].update(temp)
            values = [float(i[1]) for i in line['values']]
            average = sum(values) / (points_per_hour*hours)
            minimum = min(values)
            maximum = max(values)
            
            line['values']={"average":average,"minimum":minimum,"maximum":maximum}
        return result

    except requests.RequestException as e:
        print(f"API request failed with an exception: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None

def extract_node_detail(data,node_type,prom_con_obj):
    port=prom_con_obj.ssh_port
    username = prom_con_obj.abacus_username
    password  = prom_con_obj.abacus_password
    return_dict={}
    for hostname in data[node_type]:
        return_dict[hostname] = {}
        return_dict[hostname]['storage'] = {}
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys() 
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(hostname, port, username, password)
                commands = {"ram" : "free -g | awk '/Mem:/ {print $2}'" , "cores":"lscpu | awk '/^CPU\(s\):/ {print $2}'"}
                for label,command in commands.items():
                    stdin, stdout, stderr = client.exec_command(command)
                    out = stdout.read().decode('utf-8').strip()
                    if out and out!='':
                        return_dict[hostname][label] = out
                        print(f"Fetched '{label}' value for {hostname} : {out}")
                    else:
                        raise RuntimeError(f"ERROR : Unable to determine {label} value for {hostname} , {e}")
                
                storage_commands = {'root_partition':"df -h | awk '$6 == \"/\" {print $2}'",
                                    'kafka' : "df -h | awk '$6 == \"/data/kafka\" {print $2}'",
                                    'spark' : "df -h | awk '$6 == \"/data/spark\" {print $2}'",
                                    'dn1' : "df -h | awk '$6 == \"/data/dn1\" {print $2}'",
                                    'dn2' : "df -h | awk '$6 == \"/data/dn2\" {print $2}'",
                                    'dn3' : "df -h | awk '$6 == \"/data/dn3\" {print $2}'",
                                    'pg' : "df -h | awk '$6 == \"/pg\" {print $2}'",
                                    'data' : "df -h | awk '$6 == \"/data\" {print $2}'",
                                    'data_prometheus' : "df -h | awk '$6 == \"/data/prometheus\" {print $2}'",
                                    }

                for label,command in storage_commands.items():
                    stdin, stdout, stderr = client.exec_command(command)
                    out = stdout.read().decode('utf-8').strip()
                    if out and out!='':
                        return_dict[hostname]['storage'][label] = out
                        print(f"Fetched '{label}' value for {hostname} : {out}")
                    else:pass
                        # print(f"WARNING : Unable to determine '{label}' value for {hostname}")

            except Exception as e:
                if node_type=="other_nodes":
                    print(f"WARNING : Unable connect to {hostname} (other_node category), {e}")
                else:
                    raise RuntimeError(f"ERROR : Unable connect to {hostname} , {e}") from e
            finally:
                client.close()
        except socket.gaierror as e:
            if node_type=="other_nodes":
                print(f"WARNING : Could not resolve {hostname} , {e}")
            else:
                raise RuntimeError(f"ERROR : Could not resolve {hostname} , {e}") from e
        if 'c2' in hostname:return_dict[hostname]['clst'] = "2"
        else:return_dict[hostname]['clst'] = "1"
    return return_dict

def extract_stack_details(nodes_file_path,prom_con_obj):
    with open(nodes_file_path,'r') as file:
        data = json.load(file)
    def extract_node_detail_wrapper(data, node_type, prom_con_obj):
        return extract_node_detail(data, node_type, prom_con_obj)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future1 = executor.submit(extract_node_detail_wrapper, data, 'pnodes', prom_con_obj)
        future2 = executor.submit(extract_node_detail_wrapper, data, 'dnodes', prom_con_obj)
        future3 = executor.submit(extract_node_detail_wrapper, data, 'pgnodes', prom_con_obj)
        future4 = executor.submit(extract_node_detail_wrapper, data, 'monitoring_node', prom_con_obj)
        future5 = executor.submit(extract_node_detail_wrapper, data, 'other_nodes', prom_con_obj)
        future6 = executor.submit(extract_node_detail_wrapper, data, 'stsnodes', prom_con_obj)
        completed_futures, _ = concurrent.futures.wait([future1, future2, future3, future4 , future5,future6])
    pnodes = future1.result()
    dnodes = future2.result()
    pgnodes = future3.result()
    monitoring_node = future4.result()
    other_nodes = future5.result()
    sts_nodes = future6.result()

    data.update(pnodes)
    data.update(dnodes)
    data.update(pgnodes)
    data.update(monitoring_node)
    data.update(sts_nodes)
    data.update(other_nodes)
    with open(nodes_file_path,'w') as file:
        json.dump(data,file,indent=4)