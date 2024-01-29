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

def get_query_output_from_configdb(query,prom_con_obj,host):
    output=None
    port=prom_con_obj.ssh_port
    username = prom_con_obj.abacus_username
    password  = prom_con_obj.abacus_password

    full_query=f'sudo docker exec postgres-configdb bash -c "PGPASSWORD=pguptycs psql -U postgres configdb -c \\"{query}\\""'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Executing query in host {host}")
        ssh.connect(host, port, username, password)
        stdin, stdout, stderr = ssh.exec_command(full_query)
        exit_status = stdout.channel.recv_exit_status()

        if exit_status == 0:
            # Command executed successfully
            output = stdout.read().decode()
            print("Output:")
            print(output)
        else:
            # Command failed
            print("Command failed with exit status:", exit_status)
            print("Error:")
            print(stderr.read().decode())

    except Exception as e:
        print(f"Error while executing {query} in {host}:", str(e))
    finally:
        ssh.close()
        return output
#---------

def get_top_n_pg_tables(n,prom_con_obj):
    final_output={}
    query=f"""
        select schemaname as table_schema,
        relname as table_name,
        pg_size_pretty(pg_total_relation_size(relid)) as total_size,
        pg_size_pretty(pg_relation_size(relid)) as data_size,
        pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid))
            as external_size
        from pg_catalog.pg_statio_user_tables
        order by pg_total_relation_size(relid) desc,
                pg_relation_size(relid) desc
        limit {n};
    """
    test_env_file_path=prom_con_obj.test_env_file_path
    with open(test_env_file_path, 'r') as file:
        stack_details = json.load(file)

    for hostname in stack_details['pgnodes']:
        query_output = get_query_output_from_configdb(query,prom_con_obj,hostname)
        lines = query_output.strip().split('\n')
        result = []
        for line in lines:
            if not line.startswith('-') and not line.startswith('('):
                row_data = re.split(r'\s\s+|\|', line)
                row_data = [item.strip() for item in row_data if item.strip()]
                if len(row_data) == 5:
                    schema, table_name, total_size, data_size, external_size = row_data
                    table_info = {
                        'table_schema': schema,
                        'table_name': table_name,
                        'total_size': total_size,
                        'data_size': data_size,
                        'external_size': external_size
                    }
                    result.append(table_info)
        
        for table_info in result:
            print(table_info)
        final_output[hostname] = result
    return final_output


    # data = """
    # table_schema |       table_name       | total_size | data_size | external_size 
    # --------------+------------------------+------------+-----------+---------------
    # public       | alerts                 | 88 GB      | 65 GB     | 23 GB
    # public       | incidents              | 34 GB      | 30 GB     | 3876 MB
    # public       | alert_responses        | 11 GB      | 5493 MB   | 5747 MB
    # public       | incident_alerts        | 7867 MB    | 3438 MB   | 4429 MB
    # public       | detection_responses    | 6899 MB    | 3899 MB   | 3000 MB
    # public       | assets                 | 3161 MB    | 675 MB    | 2485 MB
    # public       | threat_indicators      | 2965 MB    | 1915 MB   | 1050 MB
    # public       | asset_capabilities     | 969 MB     | 494 MB    | 475 MB
    # public       | java_artifacts_c       | 892 MB     | 561 MB    | 332 MB
    # public       | java_artifacts_o       | 850 MB     | 537 MB    | 313 MB
    # public       | agent_last_activity_at | 684 MB     | 269 MB    | 415 MB
    # public       | compliance_summary     | 644 MB     | 453 MB    | 191 MB
    # public       | asset_tags             | 531 MB     | 265 MB    | 266 MB
    # public       | java_artifacts_i       | 330 MB     | 206 MB    | 124 MB
    # public       | asset_infos            | 221 MB     | 150 MB    | 71 MB
    # public       | epss_score             | 166 MB     | 75 MB     | 91 MB
    # public       | java_artifacts_s       | 123 MB     | 77 MB     | 46 MB
    # public       | superseded_packages    | 113 MB     | 66 MB     | 47 MB
    # public       | java_artifacts_d       | 111 MB     | 62 MB     | 49 MB
    # public       | audit_entities         | 90 MB      | 67 MB     | 23 MB
    # (20 rows)
    # """