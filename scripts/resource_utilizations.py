from helper import execute_prometheus_query, execute_point_prometheus_query
import pandas as pd
from collections import defaultdict
# Set the display options to show all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

average_column_name="avg"
minimum_column_name="min"
maximum_column_name="max"
cols_to_aggregate = [average_column_name]

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

    # def sum_all_integer_cols(self,df):
    #     numeric_columns = df.select_dtypes(include=['int', 'float']).columns
    #     string_columns = df.select_dtypes(include='object').columns
    #     new_row=dict([(int_col,df[int_col].sum()) for int_col in numeric_columns])
    #     new_row.update(dict([(str_col,"SUM") for str_col in string_columns]))
    #     df = df._append(new_row, ignore_index=True)
    #     return df
        
    def sum_and_sort_cols(self,df):
        new_row=dict([(int_col,df[int_col].sum()) for int_col in cols_to_aggregate])
        df.loc["SUM"] = new_row
        df=df.sort_values(by=average_column_name)
        return df

    
    def groupby_2_cols_and_return_dict(self,df,col1,col2):
        grouped_df=df.groupby([col1,col2])[cols_to_aggregate].sum()
        # all_dfs = {}
        all_dfs_dict={}

        for index, group_df in grouped_df.groupby(col1):
            group_df = group_df[group_df[average_column_name] >= 0.01]
            group_df = group_df.reset_index(level=col1)
            group_df.drop(col1, axis=1, inplace=True)
            # all_dfs[index] = group_df
            all_dfs_dict[index] = group_df.to_dict(orient="index")
            # print(f"DataFrame for index {index}:\n{self.sum_and_sort_cols(group_df)}\n")
            print(f"DataFrame for index {index}:\n{group_df}\n")

        return all_dfs_dict

    def groupby_a_col_and_return_dict(self,df,col):
        df=df.groupby(col)[cols_to_aggregate].sum()
        df = df[df[average_column_name] >= 0.01]
        # print(self.sum_and_sort_cols(df))
        print(df)

        return df.to_dict(orient="index")

    def preprocess_df(self,df,container_name_or_app_name):
        group_by_node_type=self.groupby_a_col_and_return_dict(df,'node_type')
        group_by_host_name=self.groupby_a_col_and_return_dict(df,'host_name')

        result={
                "nodetype_level_usage":group_by_node_type,
                "hostname_level_usage":group_by_host_name
            }
      
        if container_name_or_app_name:
            groupby_nodetype_and_app_or_cont=self.groupby_2_cols_and_return_dict(df,'node_type',container_name_or_app_name)
            group_by_hostname_and_app_or_cont=self.groupby_2_cols_and_return_dict(df,container_name_or_app_name,'host_name')
            group_by_app_or_cont=self.groupby_a_col_and_return_dict(df,container_name_or_app_name)

            result[f"{container_name_or_app_name}_level_usage"] = group_by_app_or_cont
            result[f"{container_name_or_app_name}_and_hostname_level_usage"] = group_by_hostname_and_app_or_cont
            result[f"nodetype_and_{container_name_or_app_name}_level_usage"] = groupby_nodetype_and_app_or_cont
        return result


    def collect_total_memory_usages(self):
        result={}
        #---------------------------node level----------------------------
        node_level_memory_query = "sum(uptycs_memory_used /(1024*1024)) by (node_type,host_name)"
        node_level_final_memory_result=[]
        node_level_memory_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,node_level_memory_query,self.hours)
        for line in node_level_memory_query_result:
            node_level_final_memory_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                average_column_name : line["values"]["average"]
            })
        node_level_memory = pd.DataFrame(node_level_final_memory_result)  
        result["host_usages_analysis"]=self.preprocess_df(node_level_memory,None)
        #---------------------------app level----------------------------
        application_level_memory_query = 'sum(uptycs_app_memory) by (node_type,host_name,app_name)'
        application_level_final_memory_result=[]
        application_level_memory_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,application_level_memory_query,self.hours)
        for line in application_level_memory_query_result:

            application_level_final_memory_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                "application":line["metric"]["app_name"],
                average_column_name : line["values"]["average"]*(self.node_ram_capacity[line["metric"]["host_name"]]/100)
            })

        app_level_memory = pd.DataFrame(application_level_final_memory_result)
        result["application_usages_analysis"]=self.preprocess_df(app_level_memory,'application')
        # ---------------------------container level----------------------------
        container_level_memory_query='sum(uptycs_docker_mem_used{}/(1024*1024*1024)) by (container_name,host_name)'
        container_level_final_memory_result=[]
        container_level_memory_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,container_level_memory_query,self.hours)
        for line in container_level_memory_query_result:

            container_level_final_memory_result.append({
                "node_type":self.host_name_type_mapping[line["metric"]["host_name"]],
                "host_name":line["metric"]["host_name"],
                "container":line["metric"]["container_name"],
                average_column_name : line["values"]["average"]
            })

        container_level_memory = pd.DataFrame(container_level_final_memory_result)
        result["container_usages_analysis"]=self.preprocess_df(container_level_memory,'container')
        return result
       
    def collect_total_cpu_usages(self):
        result={}
        #---------------------------node level----------------------------
        node_level_cpu_query = "sum(100-uptycs_idle_cpu) by (node_type,host_name)"
        node_level_final_cpu_result=[]
        node_level_cpu_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,node_level_cpu_query,self.hours)
        for line in node_level_cpu_query_result:
            node_level_final_cpu_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                average_column_name : line["values"]["average"]*float(self.node_cores_capacity[line["metric"]["host_name"]])/100
            })
        node_level_cpu = pd.DataFrame(node_level_final_cpu_result)   
        result["host_usages_analysis"]=self.preprocess_df(node_level_cpu,None)
        #---------------------------app level----------------------------
        application_level_cpu_query = 'sum(uptycs_app_cpu) by (node_type,host_name,app_name)/100'
        application_level_final_cpu_result=[]
        application_level_cpu_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,application_level_cpu_query,self.hours)
        for line in application_level_cpu_query_result:
            application_level_final_cpu_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                "application":line["metric"]["app_name"],
                average_column_name : line["values"]["average"]
            })

        app_level_cpu = pd.DataFrame(application_level_final_cpu_result)
        result["application_usages_analysis"]=self.preprocess_df(app_level_cpu,'application')
        #----------------------------container level-----------------------------
        container_level_cpu_query='sum(uptycs_docker_cpu_stats{}) by (container_name,host_name)/100'
        container_level_final_cpu_result=[]
        container_level_cpu_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,container_level_cpu_query,self.hours)
        for line in container_level_cpu_query_result:

            container_level_final_cpu_result.append({
                "node_type":self.host_name_type_mapping[line["metric"]["host_name"]],
                "host_name":line["metric"]["host_name"],
                "container":line["metric"]["container_name"],
                average_column_name : line["values"]["average"]
            })

        container_level_cpu = pd.DataFrame(container_level_final_cpu_result)
        result["container_usages_analysis"]=self.preprocess_df(container_level_cpu,'container')
        return result

if __name__=='__main__':
    print("Testing active connections by app...")
    from settings import configuration
    from datetime import datetime, timedelta
    from parent_load_details import parent
    import pytz
    format_data = "%Y-%m-%d %H:%M"
    
    start_time_str = "2024-01-31 05:53"
    hours=12

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
    mem_result = active_obj.collect_total_memory_usages()
    cpu_result = active_obj.collect_total_cpu_usages()

    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Osquery_LoadTests']  # Replace 'your_database_name' with your actual database name
    collection = db['Testing']  # Replace 'your_collection_name' with your actual collection name
    collection.insert_one({"memory_usages":mem_result,
                           "cpu_usages":cpu_result})