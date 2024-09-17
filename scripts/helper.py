# import json
import socket,paramiko
# import concurrent.futures
import requests
import time
from collections import defaultdict
from config_vars import *
import pandas as pd
import numpy as np

def measure_time(func):
    """Decorator to measure the execution time of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        print(f"\nFunction '{func.__name__}' took {elapsed:.6f} seconds to complete. \n")
        return result
    return wrapper

def execute_command_in_node(node,command,stack_obj):
    try:
        stack_obj.log.info(f"Executing the command in node : {node}")
        client = paramiko.SSHClient()
        client.load_system_host_keys() 
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(node, SSH_PORT, ABACUS_USERNAME, ABACUS_PASSWORD)
            stdin, stdout, stderr = client.exec_command(command)
            out = stdout.read().decode('utf-8').strip()
            errors = stderr.read().decode('utf-8')
            if errors:
                stack_obj.log.error("Errors:")
                stack_obj.log.info(errors)
            return out
                
        except Exception as e:
            stack_obj.log.exception(e)
            raise RuntimeError(f"ERROR : Unable to connect to {node} , {e}") from e
        finally:
            client.close()
    except socket.gaierror as e:
        stack_obj.log.exception(e)
        raise RuntimeError(f"ERROR : Unable to connect to {node} , {e}") from e

def execute_trino_query(node,query,stack_obj,schema="system"):
    trino_command = f"sudo -u monkey docker exec trino-monitoring /opt/uptycs/cloud/utilities/trino-cli.sh --user uptycs --password prestossl --catalog uptycs --schema upt_{schema} --execute  \"{query}\""
    return execute_command_in_node(node,trino_command,stack_obj)

def execute_configdb_query(node,query,stack_obj):
    configdb_command = f'sudo docker exec postgres-configdb bash -c "PGPASSWORD=pguptycs psql -U postgres configdb -c \\"{query}\\""'
    stack_obj.log.info(configdb_command)
    return execute_command_in_node(node,configdb_command,stack_obj)

def execute_point_prometheus_query(stack_obj,timestamp,query): 
    PROMETHEUS = stack_obj.prometheus_path
    for metric in KUBE_METRICS:
        if metric in query:
            PROMETHEUS = stack_obj.kube_prometheus_path 
            stack_obj.log.info("pod level metric found.. using prometheous path : " , PROMETHEUS)
  
    PARAMS = {
        'query': query,
        'time' : timestamp
    }
    stack_obj.log.info(f"Executing {query} at {stack_obj.monitoring_ip} at a single timestamp {timestamp}...")
    try:
        response = requests.get(PROMETHEUS + PROM_POINT_API_PATH, params=PARAMS)
        if response.status_code != 200:
            raise RuntimeError(f"API request failed with status code {response.status_code}")
        result = response.json()['data']['result']
        if len(result)==0:
            stack_obj.log.warning(f"WARNING : No data found for : {query}")
        return result

    except requests.RequestException as e:
        raise RuntimeError(f"API request failed with an exception {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")

def execute_prometheus_query(stack_obj,query,preprocess=True,step_factor=None,for_charts=None):
    PROMETHEUS = stack_obj.prometheus_path
    for metric in KUBE_METRICS:
        if metric in query:
            PROMETHEUS = stack_obj.kube_prometheus_path
            stack_obj.log.info("pod level metric found.. using prometheous path : " , PROMETHEUS)
    hours = stack_obj.hours
    if not step_factor:
        step_factor=hours/10 if hours>10 else 1
    step=60*step_factor
    points_per_min = 60/step
    points_per_hour = points_per_min*60
    estimated_points=(points_per_hour*hours) + 1

    if for_charts:
        start_timestamp = for_charts[0]
        end_timestamp = for_charts[1]
    else:
        start_timestamp=stack_obj.start_timestamp
        end_timestamp = stack_obj.end_timestamp
    PARAMS = {
        'query': query,
        'start': start_timestamp,
        'end': end_timestamp,
        'step':step
    }

    try:
        response = requests.get(PROMETHEUS + PROM_API_PATH, params=PARAMS)
        if response.status_code != 200:
            raise RuntimeError(f"API request failed with status code {response.status_code}")
        result = response.json()['data']['result']
        if len(result)==0:
            stack_obj.log.warning(f"No data found for : {query}")

        if preprocess==True:
            for line in result:
                temp = line["metric"]
                line["metric"] = defaultdict(lambda: None)
                line["metric"].update(temp)
                values = [float(i[1]) for i in line['values']]
                average = sum(values) / (estimated_points)
                minimum = 0 if len(values) < estimated_points else min(values)
                maximum = max(values)
                
                line['values']={"average":average,"minimum":minimum,"maximum":maximum}
        return result

    except requests.RequestException as e:
        raise RuntimeError(f"API request failed with an exception {e}")

    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")

# def extract_node_detail(data,node_type):
#     return_dict={}
#     for hostname in data[node_type]:
#         return_dict[hostname] = {}
#         return_dict[hostname]['storage'] = {}
#         try:
#             client = paramiko.SSHClient()
#             client.load_system_host_keys() 
#             client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#             try:
#                 client.connect(hostname, SSH_PORT, ABACUS_USERNAME, ABACUS_PASSWORD)
#                 commands = {"ram" : "free -g | awk '/Mem:/ {print $2}'" , "cores":"lscpu | awk '/^CPU\(s\):/ {print $2}'"}
#                 for label,command in commands.items():
#                     stdin, stdout, stderr = client.exec_command(command)
#                     out = stdout.read().decode('utf-8').strip()
#                     if out and out!='':
#                         return_dict[hostname][label] = out
#                         print(f"Fetched '{label}' value for {hostname} : {out}")
#                     else:
#                         raise RuntimeError(f"ERROR : Unable to determine {label} value for {hostname} , {e}")
                
#                 storage_commands = {'root_partition':"df -h | awk '$6 == \"/\" {print $2}'",
#                                     'kafka' : "df -h | awk '$6 == \"/data/kafka\" {print $2}'",
#                                     'spark' : "df -h | awk '$6 == \"/data/spark\" {print $2}'",
#                                     'dn1' : "df -h | awk '$6 == \"/data/dn1\" {print $2}'",
#                                     'dn2' : "df -h | awk '$6 == \"/data/dn2\" {print $2}'",
#                                     'dn3' : "df -h | awk '$6 == \"/data/dn3\" {print $2}'",
#                                     'pg' : "df -h | awk '$6 == \"/pg\" {print $2}'",
#                                     'data' : "df -h | awk '$6 == \"/data\" {print $2}'",
#                                     'data_prometheus' : "df -h | awk '$6 == \"/data/prometheus\" {print $2}'",
#                                     }

#                 for label,command in storage_commands.items():
#                     stdin, stdout, stderr = client.exec_command(command)
#                     out = stdout.read().decode('utf-8').strip()
#                     if out and out!='':
#                         return_dict[hostname]['storage'][label] = out
#                         print(f"Fetched '{label}' value for {hostname} : {out}")
#                     else:pass
#                         # print(f"WARNING : Unable to determine '{label}' value for {hostname}")

#             except Exception as e:
#                 if node_type=="other_nodes":
#                     print(f"WARNING : Unable connect to {hostname} (other_node category), {e}")
#                 else:
#                     raise RuntimeError(f"ERROR : Unable connect to {hostname} , {e}") from e
#             finally:
#                 client.close()
#         except socket.gaierror as e:
#             if node_type=="other_nodes":
#                 print(f"WARNING : Could not resolve {hostname} , {e}")
#             else:
#                 raise RuntimeError(f"ERROR : Could not resolve {hostname} , {e}") from e
#         if 'c2' in hostname:return_dict[hostname]['clst'] = "2"
#         else:return_dict[hostname]['clst'] = "1"
#     return return_dict

# def extract_stack_details(nodes_file_path):
#     with open(nodes_file_path,'r') as file:
#         data = json.load(file)
#     def extract_node_detail_wrapper(data, node_type):
#         return extract_node_detail(data, node_type)
#     with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
#         future1 = executor.submit(extract_node_detail_wrapper, data, 'pnodes')
#         future2 = executor.submit(extract_node_detail_wrapper, data, 'dnodes')
#         future3 = executor.submit(extract_node_detail_wrapper, data, 'pgnodes')
#         future4 = executor.submit(extract_node_detail_wrapper, data, 'monitoring_node')
#         future5 = executor.submit(extract_node_detail_wrapper, data, 'other_nodes')
#         future6 = executor.submit(extract_node_detail_wrapper, data, 'stsnodes')
#         completed_futures, _ = concurrent.futures.wait([future1, future2, future3, future4 , future5,future6])
#     pnodes = future1.result()
#     dnodes = future2.result()
#     pgnodes = future3.result()
#     monitoring_node = future4.result()
#     other_nodes = future5.result()
#     sts_nodes = future6.result()

#     data.update(pnodes)
#     data.update(dnodes)
#     data.update(pgnodes)
#     data.update(monitoring_node)
#     data.update(sts_nodes)
#     data.update(other_nodes)
#     with open(nodes_file_path,'w') as file:
#         json.dump(data,file,indent=4)

def save_html_page(url,file_path,check,stack_obj):
    response = requests.get(url)
    if response.status_code == 200:
        if check: return True
        page_content = response.content
        with open(file_path, "wb") as file:
            file.write(page_content)

        stack_obj.log.info(f"Webpage {url} saved successfully to {file_path}")
        return True
    else:
        stack_obj.log.error("Failed to download webpage")
        return False
    


def fetch_and_extract_csv(remote_csv_path,reports_node_ip,stack_obj):
    if remote_csv_path == None or remote_csv_path == "":
        return None
    
    current_directory = os.path.dirname(os.path.abspath(__file__))
    relative_path = "api_load.csv"
    local_csv_path = os.path.join(current_directory, relative_path)
    
    try:
        # Use SCP to copy the file from the remote host to the local machine
        with paramiko.Transport((reports_node_ip, 22)) as transport:
            transport.connect(username=ABACUS_USERNAME, password=ABACUS_PASSWORD)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.get(remote_csv_path, local_csv_path)
            stack_obj.log.info(f"Fetched csv file successfully: {remote_csv_path}")
            sftp.close()

        df = pd.read_csv(local_csv_path)
        load_dict = df.to_dict(orient='records')
        stack_obj.log.info("Extracting csv file...")
        return load_dict 
    
    except Exception as e:
        stack_obj.log.error(e)
        return None

def fetch_and_save_pdf(remote_pdf_path,reports_node_ip , local_pdf_path,stack_obj):
    if remote_pdf_path == None or remote_pdf_path == "":
        return None
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Use SCP to copy the file from the remote host to the local machine
        with paramiko.Transport((reports_node_ip, 22)) as transport:
            transport.connect(username=ABACUS_USERNAME, password=ABACUS_PASSWORD)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.get(remote_pdf_path, local_pdf_path)
            stack_obj.log.info(f"Fetched PDF file successfully: {remote_pdf_path}")
            sftp.close()
    
    except Exception as e:
        stack_obj.log.error(f"Error while fetching the pdf : {e}")


def clean_and_preprocess_df(df):
    #filling null values if any
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
    fill_values = {}
    fill_values.update({col: 0 for col in numeric_cols})
    fill_values.update({col: "NaN" for col in non_numeric_cols})
    df = df.fillna(fill_values)

    #trim down rows if huge
    df = df.head(168)

    #round off all values
    df = df.round(2)

    return df