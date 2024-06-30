from collections import defaultdict
from helper import execute_point_prometheus_query
import pandas as pd
# from config_vars import *
from helper import execute_command_in_node
import concurrent.futures

#returns a nested dictionary containing dictionaries for :
# 1. ram capacity
# 2. cores
# 3. Root partition
# 3. kafka disk space configured
# 4. spark disk partition configured
# 5. dn1,dn2,dn3
# 6. pg partition
# 7. data partition

storage_commands = {'root':"df -h | awk '$6 == \"/\" {print $2}'",
                    # '/data/kafka' : "df -h | awk '$6 == \"/data/kafka\" {print $2}'",
                    '/data/spark' : "df -h | awk '$6 == \"/data/spark\" {print $2}'",
                    '/data/dn1' : "df -h | awk '$6 == \"/data/dn1\" {print $2}'",
                    '/data/dn2' : "df -h | awk '$6 == \"/data/dn2\" {print $2}'",
                    '/data/dn3' : "df -h | awk '$6 == \"/data/dn3\" {print $2}'",
                    '/pg' : "df -h | awk '$6 == \"/pg\" {print $2}'",
                    '/data' : "df -h | awk '$6 == \"/data\" {print $2}'",
                    '/data/prometheus' : "df -h | awk '$6 == \"/data/prometheus\" {print $2}'",
                    }

def extract_ram_cores_storage_details(stack_obj):
    start_timestamp=stack_obj.start_timestamp
    final_result=defaultdict(lambda:{})

    total_memory_capacity_query = "sum(uptycs_total_memory/(1024*1024)) by (node_type,host_name,cluster_id)"
    memory_result = execute_point_prometheus_query(stack_obj,start_timestamp,total_memory_capacity_query)
    for line in memory_result:
        # print(line)
        node_name = line["metric"]["host_name"]
        final_result[node_name]['nodetype']=line["metric"]["node_type"]
        try:
            final_result[node_name]['clst']=line["metric"]["cluster_id"]
        except Exception as e:
            stack_obj.log.error(e)
        final_result[node_name]['ram(GB)']=round(float(line["value"][1]),1)
        

    total_cpu_capacity_query = "sum(uptycs_loadavg_cpu_info) by (host_name,cpu_processor)"
    cpu_result = execute_point_prometheus_query(stack_obj,start_timestamp,total_cpu_capacity_query)
    for line in cpu_result:
        node_name = line["metric"]["host_name"]
        final_result[node_name]['cores']=int(line["metric"]["cpu_processor"]) + 1 

    kafka_disk_space_result=execute_point_prometheus_query(stack_obj,start_timestamp,f"sum(kafka_disk_volume_size/{1024**3}) by (host_name)")
    for line in kafka_disk_space_result:
        node_name = line["metric"]["host_name"]
        final_result[node_name]['/data/kafka(TB)']=round(float(line["value"][1]),2)

    # hdfs_disk_space_result=execute_point_prometheus_query(stack_obj,start_timestamp,f"sort(sum(uptycs_hdfs_node_config_capacity/{(1024**4)}) by (hdfsdatanode))")
    # for line in hdfs_disk_space_result:
    #     node_name = line["metric"]["hdfsdatanode"]
    #     final_result[node_name]['hdfs(TB)']=round(float(line["value"][1]),2)

    nodes = list(final_result.keys())
    stack_obj.log.info(f"All nodes in the stack : {nodes}")

    # for node in nodes:
    #     for command_name,command in storage_commands.items():
    #         final_result[node][command_name] = execute_command_in_node(node,command)

    def execute_commands_on_node(node):
        results = {}
        for command_name, command in storage_commands.items():
            try:
                results[command_name] = execute_command_in_node(node, command,stack_obj)
            except Exception as e:
                stack_obj.log.error(f"Unable to execute {command_name} command in {node}. error : {e}")
        return node, results

    # Use ThreadPoolExecutor to run the commands in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_node = {executor.submit(execute_commands_on_node, node): node for node in nodes}
        for future in concurrent.futures.as_completed(future_to_node):
            node, results = future.result()
            final_result[node].update(results)

    # print("Final result: ", final_result)


    #Calculating total partition size
    # bytes_used_dict = defaultdict(lambda:{})
    # percentage_used_dict = defaultdict(lambda:{})

    # partition_bytes_used=execute_point_prometheus_query(stack_obj,start_timestamp,f"sum(uptycs_used_disk_bytes) by (host_name,partition)")
    # for line in partition_bytes_used:
    #     node_name = line["metric"]["host_name"]
    #     bytes_used_dict[node_name][line["metric"]["partition"]]=float(line["value"][1])

    # partition_percentage_used=execute_point_prometheus_query(stack_obj,start_timestamp,f"sum(uptycs_percentage_used) by (host_name,partition)")
    # for line in partition_percentage_used:
    #     node_name = line["metric"]["host_name"]
    #     percentage_used_dict[node_name][line["metric"]["partition"]]=float(line["value"][1])

    # print(json.dumps(bytes_used_dict,indent=4))
    # print(json.dumps(percentage_used_dict,indent=4))

    # for node in percentage_used_dict.keys():
    #     for partition,percentage in percentage_used_dict[node].items():
    #         bytes = bytes_used_dict[node][partition]
    #         total_space = (bytes*100)/percentage
    #         total_space_in_TB = total_space/(1024**4)
    #         final_result[node][partition]=total_space_in_TB

    df = pd.DataFrame(final_result)    
    df=df.T
    df = df.reset_index().rename(columns={'index': 'hostname'})
    df=df.sort_values(by=["nodetype","hostname"])
    df=df.fillna("")
    df = df.astype(str)
    stack_obj.log.info(f"\n {df}")
    # df.to_csv("stack.csv")

    return {    "format":"table","collapse":True,
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                    "page":"Summary"
                },
                "data":df.to_dict(orient="records")
            }

    

if __name__=='__main__':
    from settings import stack_configuration

    variables = {
        "start_time_str_ist":"2024-06-24 00:00",
        "load_duration_in_hrs":4,
        "test_env_file_name":'s1_nodes.json'
    }
    stack_obj = stack_configuration(variables)

    result=extract_ram_cores_storage_details(stack_obj)

    # print(result)
    