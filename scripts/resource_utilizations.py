from helper import execute_prometheus_query, execute_point_prometheus_query
import pandas as pd
from collections import defaultdict
# Set the display options to show all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

class resource_usages:
    def __init__(self,prom_con_obj,start_timestamp,end_timestamp,hours):
        self.start_timestamp=start_timestamp
        self.end_timestamp=end_timestamp
        self.hours=hours
        self.prom_con_obj=prom_con_obj

        total_memory_capacity_query = "sum(uptycs_total_memory/(1024*1024)) by (node_type,host_name)"
        result = execute_point_prometheus_query(self.prom_con_obj,self.start_timestamp,total_memory_capacity_query)
        self.node_ram_capacity = {}
        self.host_name_type_mapping={}
        self.all_node_types=defaultdict(lambda:[])
        for line in result:
            node_name = line["metric"]["host_name"]
            capacity = float(line["value"][1])
            self.node_ram_capacity[node_name] = capacity
            self.host_name_type_mapping[node_name] = line["metric"]["node_type"]
            self.all_node_types[line["metric"]["node_type"]].append(node_name)

        print(self.node_ram_capacity)
     
        total_cpu_capacity_query = "sum(uptycs_loadavg_cpu_info) by (host_name,cpu_processor)"
        cpu_result = execute_point_prometheus_query(self.prom_con_obj,self.start_timestamp,total_cpu_capacity_query)
        self.node_cores_capacity = {}
        for line in cpu_result:
            node_name = line["metric"]["host_name"]
            cpu_capacity = float(line["metric"]["cpu_processor"]) + 1 
            self.node_cores_capacity[node_name] = cpu_capacity
        print(self.node_cores_capacity)

    def sum_all_integer_cols(self,df):
        numeric_columns = df.select_dtypes(include=['int', 'float']).columns
        string_columns = df.select_dtypes(include='object').columns
        new_row=dict([(int_col,df[int_col].sum()) for int_col in numeric_columns])
        new_row.update(dict([(str_col,"SUM") for str_col in string_columns]))
        df = df._append(new_row, ignore_index=True)
        return df

    def preprocess_df(self,df,container_name_or_app_name,last_column_name):

        group_by_node_type=self.sum_all_integer_cols(df.groupby('node_type')[[last_column_name]].sum().reset_index())
        group_by_host_name=self.sum_all_integer_cols(df.groupby(['node_type','host_name'])[[last_column_name]].sum().reset_index())
        print(group_by_node_type)
        print(group_by_host_name)

        if container_name_or_app_name:
            grouped_df=df.groupby(['node_type',container_name_or_app_name])[[last_column_name]].sum()
            node_type_dfs = {}

            for node_type_value, group_df in grouped_df.groupby('node_type'):
                node_type_dfs[node_type_value] = self.sum_all_integer_cols(group_df.reset_index().sort_values(by=last_column_name, ascending=False))
            for node_type_value, node_type_df in node_type_dfs.items():
                print(f"DataFrame for node_type {node_type_value}:\n{node_type_df}\n")

            group_by_host_and_app_or_cont=self.sum_all_integer_cols(df.groupby(['host_name',container_name_or_app_name])[[last_column_name]].sum().reset_index().sort_values(by=last_column_name, ascending=False))
            group_by_app_or_cont=self.sum_all_integer_cols(df.groupby(container_name_or_app_name)[[last_column_name]].sum().reset_index().sort_values(by=last_column_name, ascending=False))
            print(group_by_host_and_app_or_cont)
            print(group_by_app_or_cont)

    def collect_total_memory_usages(self):
        last_column_name="Average memory used in GB"
        #---------------------------node level----------------------------
        node_level_memory_query = "sum(uptycs_memory_used /(1024*1024)) by (node_type,host_name)"
        node_level_final_memory_result=[]
        node_level_memory_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,node_level_memory_query,self.hours)
        for line in node_level_memory_query_result:
            node_level_final_memory_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                f"{last_column_name}" : line["values"]["average"]
            })
        node_level_memory = pd.DataFrame(node_level_final_memory_result)  
        self.preprocess_df(node_level_memory,None,last_column_name)
        #---------------------------app level----------------------------
        application_level_memory_query = 'sum(uptycs_app_memory) by (node_type,host_name,app_name)'
        application_level_final_memory_result=[]
        application_level_memory_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,application_level_memory_query,self.hours)
        for line in application_level_memory_query_result:

            application_level_final_memory_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                "app_name":line["metric"]["app_name"],
                last_column_name : line["values"]["average"]*(self.node_ram_capacity[line["metric"]["host_name"]]/100)
            })

        app_level_memory = pd.DataFrame(application_level_final_memory_result)
        self.preprocess_df(app_level_memory,'app_name',last_column_name)
        # ---------------------------container level----------------------------
        container_level_memory_query='sum(uptycs_docker_mem_used{}/(1024*1024*1024)) by (container_name,host_name)'
        container_level_final_memory_result=[]
        container_level_memory_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,container_level_memory_query,self.hours)
        for line in container_level_memory_query_result:

            container_level_final_memory_result.append({
                "node_type":self.host_name_type_mapping[line["metric"]["host_name"]],
                "host_name":line["metric"]["host_name"],
                "container_name":line["metric"]["container_name"],
                last_column_name : line["values"]["average"]
            })

        container_level_memory = pd.DataFrame(container_level_final_memory_result)
        container_level_memory = container_level_memory[container_level_memory[last_column_name] >= 0.001]
        self.preprocess_df(container_level_memory,'container_name',last_column_name)
       
    def collect_total_cpu_usages(self):
        last_column_name="Average CPU used in cores"
        #---------------------------node level----------------------------
        node_level_cpu_query = "sum(100-uptycs_idle_cpu) by (node_type,host_name)"
        node_level_final_cpu_result=[]
        node_level_cpu_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,node_level_cpu_query,self.hours)
        for line in node_level_cpu_query_result:
            node_level_final_cpu_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                last_column_name : line["values"]["average"]*float(self.node_cores_capacity[line["metric"]["host_name"]])/100
            })
        node_level_cpu = pd.DataFrame(node_level_final_cpu_result)   
        self.preprocess_df(node_level_cpu,None,last_column_name)
        #---------------------------app level----------------------------
        application_level_cpu_query = 'sum(uptycs_app_cpu) by (node_type,host_name,app_name)/100'
        application_level_final_cpu_result=[]
        application_level_cpu_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,application_level_cpu_query,self.hours)
        for line in application_level_cpu_query_result:
            application_level_final_cpu_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                "app_name":line["metric"]["app_name"],
                last_column_name : line["values"]["average"]
            })

        app_level_cpu = pd.DataFrame(application_level_final_cpu_result)
        self.preprocess_df(app_level_cpu,'app_name',last_column_name)
        #----------------------------container level-----------------------------
        container_level_cpu_query='sum(uptycs_docker_cpu_stats{}) by (container_name,host_name)/100'
        container_level_final_cpu_result=[]
        container_level_cpu_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,container_level_cpu_query,self.hours)
        for line in container_level_cpu_query_result:

            container_level_final_cpu_result.append({
                "node_type":self.host_name_type_mapping[line["metric"]["host_name"]],
                "host_name":line["metric"]["host_name"],
                "container_name":line["metric"]["container_name"],
                last_column_name : line["values"]["average"]
            })

        container_level_cpu = pd.DataFrame(container_level_final_cpu_result)
        container_level_cpu = container_level_cpu[container_level_cpu[last_column_name] >= 0.01]
        self.preprocess_df(container_level_cpu,'container_name',last_column_name)

if __name__=='__main__':
    print("Testing active connections by app...")
    from settings import configuration
    from datetime import datetime, timedelta
    from parent_load_details import parent
    import pytz
    format_data = "%Y-%m-%d %H:%M"
    
    start_time_str = "2024-01-26 01:25"
    hours=16

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
    active_obj = resource_usages(configuration('longevity_nodes.json') , start_timestamp,end_timestamp,hours=hours)
    result = active_obj.collect_total_memory_usages()
    # result = active_obj.collect_total_cpu_usages()