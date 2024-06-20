from collections import defaultdict
from helper import execute_point_prometheus_query
import pandas as pd
# from config_vars import *
from helper import execute_command_in_node

#returns a nested dictionary containing dictionaries for :
# 1. ram capacity
# 2. cores
# 3. Root partition
# 3. kafka disk space configured
# 4. spark disk partition configured
# 5. dn1,dn2,dn3
# 6. pg partition
# 7. data partition

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

def extract_ram_cores_storage_details(stack_obj,start_timestamp):
    final_result=defaultdict(lambda:{})

    total_memory_capacity_query = "sum(uptycs_total_memory/(1024*1024)) by (node_type,host_name,cluster_id)"
    memory_result = execute_point_prometheus_query(stack_obj,start_timestamp,total_memory_capacity_query)
    for line in memory_result:
        print(line)
        node_name = line["metric"]["host_name"]
        final_result[node_name]['ram']=float(line["value"][1])
        try:
            final_result[node_name]['cluster_id']=line["metric"]["cluster_id"]
        except Exception as e:
            print(e)
        final_result[node_name]['node_type']=line["metric"]["node_type"]
    
    total_cpu_capacity_query = "sum(uptycs_loadavg_cpu_info) by (host_name,cpu_processor)"
    cpu_result = execute_point_prometheus_query(stack_obj,start_timestamp,total_cpu_capacity_query)
    for line in cpu_result:
        node_name = line["metric"]["host_name"]
        final_result[node_name]['cores']=float(line["metric"]["cpu_processor"]) + 1 

    kafka_disk_space_result=execute_point_prometheus_query(stack_obj,start_timestamp,f"sum(kafka_disk_volume_size/{1024**3}) by (host_name)")
    for line in kafka_disk_space_result:
        node_name = line["metric"]["host_name"]
        final_result[node_name]['kafka_disk_space_configured_in_TB']=float(line["value"][1])

    hdfs_disk_space_result=execute_point_prometheus_query(stack_obj,start_timestamp,f"sort(sum(uptycs_hdfs_node_config_capacity/{(1024**4)}) by (hdfsdatanode))")
    for line in hdfs_disk_space_result:
        node_name = line["metric"]["hdfsdatanode"]
        final_result[node_name]['hdfs_disk_space_configured_in_TB']=float(line["value"][1])

    nodes = list(final_result.keys())
    print("NODES : ", nodes)

    for node in nodes:
        for command_name,command in storage_commands:
            final_result[node][command_name] = execute_command_in_node(node,command)


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
    df = df.reset_index().rename(columns={'index': 'host_name'})
    df=df.sort_values(by=["node_type","host_name"])
    print(df)
    df.to_csv("stack.csv")

    

if __name__=='__main__':
    from settings import stack_configuration
    from datetime import datetime, timedelta
    import pytz
    format_data = "%Y-%m-%d %H:%M"
    
    start_time_str = "2024-04-01 00:00"
    hours=60

    start_time = datetime.strptime(start_time_str, format_data)
    end_time = start_time + timedelta(hours=hours)
    end_time_str = end_time.strftime(format_data)

    ist_timezone = pytz.timezone('Asia/Kolkata')
    utc_timezone = pytz.utc

    start_ist_time = ist_timezone.localize(datetime.strptime(start_time_str, '%Y-%m-%d %H:%M'))
    start_timestamp = int(start_ist_time.timestamp())
    start_utc_time = start_ist_time.astimezone(utc_timezone)
    start_utc_str = start_utc_time.strftime(format_data)

    end_ist_time = ist_timezone.localize(datetime.strptime(end_time_str, '%Y-%m-%d %H:%M'))
    end_timestamp = int(end_ist_time.timestamp())
    end_utc_time = end_ist_time.astimezone(utc_timezone)
    end_utc_str = end_utc_time.strftime(format_data)

    extract_ram_cores_storage_details(stack_configuration('longevity_nodes.json') , start_timestamp)
    