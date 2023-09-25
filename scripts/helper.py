import json
import socket,paramiko
import concurrent.futures

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
                    else:
                        print(f"Unable to determine {label} value for {hostname}")
                
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
                    else:
                        print(f"Unable to determine {label} value for {hostname}")

            except Exception as e:
                print(f'ERROR : Unable connect to {hostname}' , e)
            finally:
                client.close()
        except socket.gaierror:
            print(f"ERROR : Could not resolve {hostname}")
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
        completed_futures, _ = concurrent.futures.wait([future1, future2, future3, future4 , future5])
    pnodes = future1.result()
    dnodes = future2.result()
    pgnodes = future3.result()
    monitoring_node = future4.result()
    other_nodes = future5.result()

    data.update(pnodes)
    data.update(dnodes)
    data.update(pgnodes)
    data.update(monitoring_node)
    data.update(other_nodes)
    with open(nodes_file_path,'w') as file:
        json.dump(data,file,indent=4)