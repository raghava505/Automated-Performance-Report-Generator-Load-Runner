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
cols_to_compare=[average_column_name]
usage_threshold = 0.03

def get_exclude_pattern(lst):return '|'.join(lst)

exclude_applications=[".*osqLogger.*" , ".*redis-server.*" , ".*airflow.*"]
exclude_containers=[".*tls.*"]

def get_exclude_filter(exclude_nodetypes):
    print("Excluding nodetypes : ", exclude_nodetypes)
    nodetype_exclude_filter = 'node_type!~"^({})$"'.format(get_exclude_pattern(exclude_nodetypes))
    app_exclude_filter = 'app_name!~"^({})$"'.format(get_exclude_pattern(exclude_applications))
    cont_exclude_filter = 'container_name!~"^({})$"'.format(get_exclude_pattern(exclude_containers))

    exclude_filter="{{{},{},{}}}".format(nodetype_exclude_filter,app_exclude_filter,cont_exclude_filter)
    print("Exclude filter generated is : ", exclude_filter)
    return exclude_filter


class resource_usages:
    def __init__(self,prom_con_obj,start_timestamp,end_timestamp,hours,include_nodetypes=["process","data","pg","airflow"]):
        self.start_timestamp=start_timestamp
        self.end_timestamp=end_timestamp
        self.hours=hours
        self.prom_con_obj=prom_con_obj

        total_memory_capacity_query = "sum(uptycs_total_memory/(1024*1024)) by (node_type,host_name)"
        memory_result = execute_point_prometheus_query(self.prom_con_obj,self.start_timestamp,total_memory_capacity_query)
        self.node_ram_capacity = {}
        self.host_name_type_mapping={}
        self.all_node_types_mapping=defaultdict(lambda:[])
        for line in memory_result:
            node_name = line["metric"]["host_name"]
            capacity = float(line["value"][1])
            self.node_ram_capacity[node_name] = capacity
            self.host_name_type_mapping[node_name] = line["metric"]["node_type"]
            self.all_node_types_mapping[line["metric"]["node_type"]].append(node_name)
        
     
        total_cpu_capacity_query = "sum(uptycs_loadavg_cpu_info) by (host_name,cpu_processor)"
        cpu_result = execute_point_prometheus_query(self.prom_con_obj,self.start_timestamp,total_cpu_capacity_query)
        self.node_cores_capacity = {}
        for line in cpu_result:
            node_name = line["metric"]["host_name"]
            cpu_capacity = float(line["metric"]["cpu_processor"]) + 1 
            self.node_cores_capacity[node_name] = cpu_capacity
        
        self.all_node_types=list(self.all_node_types_mapping.keys())
        print("All nodetypes found are : " , self.all_node_types)
        
        print("Include nodetypes are : ",include_nodetypes)
        self.exclude_nodetypes = set(self.all_node_types).difference(set(include_nodetypes))
        self.exclude_filter = get_exclude_filter(self.exclude_nodetypes)

        print("Memory capacity : \n" , self.node_ram_capacity)
        print("CPU capacity : \n" , self.node_cores_capacity)

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

    
    def groupby_2_cols_and_return_dict(self,df,col1,col2,for_report,single_level_for_report=False):
        if col1=="host_name":
            cols_to_aggregate=[minimum_column_name,maximum_column_name,average_column_name]
            display_exact_table=True
        else:
            cols_to_aggregate = [average_column_name]
            display_exact_table=False
        grouped_df=df.groupby([col1,col2])[cols_to_aggregate].sum()       
        if for_report and single_level_for_report:
            all_dfs_dict={
                "schema":{
                    "merge_on_cols" : [col1,col2],
                    "compare_cols":cols_to_compare,
                    "display_exact_table":display_exact_table
                },
                "table":[]
            }
        else:all_dfs_dict={}

        for index, group_df in grouped_df.groupby(col1):
            group_df = group_df[group_df[average_column_name] >= usage_threshold]
            # if group_df.empty:continue

            if for_report:
                group_df = group_df.reset_index()
                if single_level_for_report:
                    all_dfs_dict["table"].extend(group_df.to_dict(orient="records"))
                else:
                    all_dfs_dict[index] = {
                                "schema":{
                                    "merge_on_cols" : [col1,col2],
                                    "compare_cols":cols_to_compare,
                                    "display_exact_table":False
                                },
                                "table":group_df.to_dict(orient="records")
                    }
            else:
                group_df = group_df.reset_index(level=col1,drop=True)
                all_dfs_dict[index] = group_df.to_dict(orient="index")
            # print(f"DataFrame for index {index}:\n{self.sum_and_sort_cols(group_df)}\n")
            # print(f"DataFrame for index {index}:\n{group_df}\n")

        return all_dfs_dict

    def groupby_a_col_and_return_dict(self,df,col,for_report):
        df=df.groupby(col)[cols_to_aggregate].sum()
        df = df[df[average_column_name] >= usage_threshold]
        print(self.sum_and_sort_cols(df.copy()))
        # print(df)
        if for_report:
            return {
                "schema":{
                    "merge_on_cols" : [col],
                    "compare_cols":cols_to_compare,
                    "display_exact_table":False
                },
                "table":df.reset_index().to_dict(orient="records")
            }
        else:
            return df.to_dict(orient="index")

    def preprocess_df(self,df,container_name_or_app_name,for_report):
        result={}
        if container_name_or_app_name:
            group_by_nodetype_and_app_or_cont=self.groupby_2_cols_and_return_dict(df,'node_type',container_name_or_app_name,for_report)
            group_by_hostname_and_app_or_cont=self.groupby_2_cols_and_return_dict(df,'host_name',container_name_or_app_name,for_report,single_level_for_report=True)
            group_by_app_or_cont=self.groupby_a_col_and_return_dict(df,container_name_or_app_name,for_report)

            result[f"{container_name_or_app_name}_level_usages"] = group_by_app_or_cont
            result[f"hostname_and_{container_name_or_app_name}_level_usages"] = group_by_hostname_and_app_or_cont
            result[f"nodetype_and_{container_name_or_app_name}_level_usages"] = group_by_nodetype_and_app_or_cont
        else:
            group_by_node_type=self.groupby_a_col_and_return_dict(df,'node_type',for_report)
            group_by_host_name=self.groupby_a_col_and_return_dict(df,'host_name',for_report)
            
            result["nodetype_level_usages"]=group_by_node_type
            result["hostname_level_usages"]=group_by_host_name
        return result


    def collect_total_memory_usages(self,for_report):
        result={}
        #---------------------------node level----------------------------
        node_level_memory_query = f"sum(uptycs_memory_used{self.exclude_filter} /(1024*1024)) by (node_type,host_name)"
        node_level_final_memory_result=[]
        node_level_memory_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,node_level_memory_query,self.hours)
        for line in node_level_memory_query_result:
            node_level_final_memory_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                minimum_column_name : line["values"]["minimum"],
                maximum_column_name : line["values"]["maximum"],
                average_column_name : line["values"]["average"]
            })
        node_level_memory = pd.DataFrame(node_level_final_memory_result)  
        result.update(self.preprocess_df(node_level_memory,None,for_report))

        #---------------------------app level----------------------------
        application_level_memory_query = f'sum(uptycs_app_memory{self.exclude_filter}) by (node_type,host_name,app_name)'
        application_level_final_memory_result=[]
        for line in execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,application_level_memory_query,self.hours):
            application_level_final_memory_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                "application":line["metric"]["app_name"],
                minimum_column_name : line["values"]["minimum"]*(self.node_ram_capacity[line["metric"]["host_name"]]/100),
                maximum_column_name : line["values"]["maximum"]*(self.node_ram_capacity[line["metric"]["host_name"]]/100),
                average_column_name : line["values"]["average"]*(self.node_ram_capacity[line["metric"]["host_name"]]/100)
            })

        for app in exclude_applications:
            for line in execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,f'sum(uptycs_app_memory{{app_name=~"{app}"}}) by (node_type,host_name)',self.hours):
                if line["metric"]["node_type"] in self.exclude_nodetypes:continue
                application_level_final_memory_result.append({
                    "node_type":line["metric"]["node_type"],
                    "host_name":line["metric"]["host_name"],
                    "application":app,
                    minimum_column_name : line["values"]["minimum"]*(self.node_ram_capacity[line["metric"]["host_name"]]/100),
                    maximum_column_name : line["values"]["maximum"]*(self.node_ram_capacity[line["metric"]["host_name"]]/100),
                    average_column_name : line["values"]["average"]*(self.node_ram_capacity[line["metric"]["host_name"]]/100)
                })
        app_level_memory = pd.DataFrame(application_level_final_memory_result)
        result.update(self.preprocess_df(app_level_memory,'application',for_report))

        # ---------------------------container level----------------------------
        container_level_memory_query='sum(uptycs_docker_mem_used{}/(1024*1024*1024)) by (container_name,host_name)'.format(self.exclude_filter)
        container_level_final_memory_result=[]
        for line in execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,container_level_memory_query,self.hours):
            if self.host_name_type_mapping[line["metric"]["host_name"]] in self.exclude_nodetypes:continue
            container_level_final_memory_result.append({
                "node_type":self.host_name_type_mapping[line["metric"]["host_name"]],
                "host_name":line["metric"]["host_name"],
                "container":line["metric"]["container_name"],
                minimum_column_name : line["values"]["minimum"],
                maximum_column_name : line["values"]["maximum"],
                average_column_name : line["values"]["average"]
            })

        for cont in exclude_containers:
            for line in execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,f'sum(uptycs_docker_mem_used{{container_name=~"{cont}"}}/(1024*1024*1024)) by (host_name)',self.hours):
                if self.host_name_type_mapping[line["metric"]["host_name"]] in self.exclude_nodetypes:continue
                container_level_final_memory_result.append({
                    "node_type":self.host_name_type_mapping[line["metric"]["host_name"]],
                    "host_name":line["metric"]["host_name"],
                    "container":cont,
                    minimum_column_name : line["values"]["minimum"],
                    maximum_column_name : line["values"]["maximum"],
                    average_column_name : line["values"]["average"]
                })

        container_level_memory = pd.DataFrame(container_level_final_memory_result)
        result.update(self.preprocess_df(container_level_memory,'container',for_report))
        return result
       
    def collect_total_cpu_usages(self,for_report):
        result={}
        #---------------------------node level----------------------------
        node_level_cpu_query = f"sum(100-uptycs_idle_cpu{self.exclude_filter}) by (node_type,host_name)"
        node_level_final_cpu_result=[]
        node_level_cpu_query_result=execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,node_level_cpu_query,self.hours)
        for line in node_level_cpu_query_result:
            node_level_final_cpu_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                minimum_column_name : line["values"]["minimum"]*float(self.node_cores_capacity[line["metric"]["host_name"]])/100,
                maximum_column_name : line["values"]["maximum"]*float(self.node_cores_capacity[line["metric"]["host_name"]])/100,
                average_column_name : line["values"]["average"]*float(self.node_cores_capacity[line["metric"]["host_name"]])/100
            })
        node_level_cpu = pd.DataFrame(node_level_final_cpu_result)   
        result.update(self.preprocess_df(node_level_cpu,None,for_report))

        #---------------------------app level----------------------------
        application_level_cpu_query = f'sum(uptycs_app_cpu{self.exclude_filter}) by (node_type,host_name,app_name)/100'
        application_level_final_cpu_result=[]
        for line in execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,application_level_cpu_query,self.hours):
            application_level_final_cpu_result.append({
                "node_type":line["metric"]["node_type"],
                "host_name":line["metric"]["host_name"],
                "application":line["metric"]["app_name"],
                minimum_column_name : line["values"]["minimum"],
                maximum_column_name : line["values"]["maximum"],
                average_column_name : line["values"]["average"]
            })

        for app in exclude_applications:
            for line in execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,f'sum(uptycs_app_cpu{{app_name=~"{app}"}}) by (node_type,host_name)/100',self.hours):
                if line["metric"]["node_type"] in self.exclude_nodetypes:continue
                application_level_final_cpu_result.append({
                    "node_type":line["metric"]["node_type"],
                    "host_name":line["metric"]["host_name"],
                    "application":app,
                    minimum_column_name : line["values"]["minimum"],
                    maximum_column_name : line["values"]["maximum"],
                    average_column_name : line["values"]["average"]
                })

        app_level_cpu = pd.DataFrame(application_level_final_cpu_result)
        result.update(self.preprocess_df(app_level_cpu,'application',for_report))

        #----------------------------container level-----------------------------
        container_level_cpu_query='sum(uptycs_docker_cpu_stats{}) by (container_name,host_name)/100'.format(self.exclude_filter)
        container_level_final_cpu_result=[]
        for line in execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,container_level_cpu_query,self.hours):
            if self.host_name_type_mapping[line["metric"]["host_name"]] in self.exclude_nodetypes:continue
            container_level_final_cpu_result.append({
                "node_type":self.host_name_type_mapping[line["metric"]["host_name"]],
                "host_name":line["metric"]["host_name"],
                "container":line["metric"]["container_name"],
                minimum_column_name : line["values"]["minimum"],
                maximum_column_name : line["values"]["maximum"],
                average_column_name : line["values"]["average"]
            })

        for cont in exclude_containers:
            for line in execute_prometheus_query(self.prom_con_obj,self.start_timestamp,self.end_timestamp,f'sum(uptycs_docker_cpu_stats{{container_name=~"{cont}"}}) by (host_name)/100',self.hours):
                if self.host_name_type_mapping[line["metric"]["host_name"]] in self.exclude_nodetypes:continue
                container_level_final_cpu_result.append({
                    "node_type":self.host_name_type_mapping[line["metric"]["host_name"]],
                    "host_name":line["metric"]["host_name"],
                    "container":cont,
                    minimum_column_name : line["values"]["minimum"],
                    maximum_column_name : line["values"]["maximum"],
                    average_column_name : line["values"]["average"]
                })
            
        container_level_cpu = pd.DataFrame(container_level_final_cpu_result)
        result.update(self.preprocess_df(container_level_cpu,'container',for_report))
        return result
    
    def collect_total_usages(self,for_report):
        return_dict = {
            "memory_usages" : self.collect_total_memory_usages(for_report),
            "cpu_usages" : self.collect_total_cpu_usages(for_report)
        }
        nodetype_and_application_level_memory_usage=return_dict["memory_usages"]["nodetype_and_application_level_usages"]
        del return_dict["memory_usages"]["nodetype_and_application_level_usages"]
        nodetype_and_container_level_memory_usage=return_dict["memory_usages"]["nodetype_and_container_level_usages"]
        del return_dict["memory_usages"]["nodetype_and_container_level_usages"]
        # for nodetype in exclude_nodetypes:
        #     try:del nodetype_and_container_level_memory_usage[nodetype]
        #     except:pass
        #     try:del nodetype_and_application_level_memory_usage[nodetype]
        #     except:pass

        return_dict.update({"memory_usages_analysis" : {
            "nodetype_and_application_level_memory_usages":nodetype_and_application_level_memory_usage,
            "nodetype_and_container_level_memory_usages":nodetype_and_container_level_memory_usage
        }})

        nodetype_and_application_level_cpu_usage=return_dict["cpu_usages"]["nodetype_and_application_level_usages"]
        del return_dict["cpu_usages"]["nodetype_and_application_level_usages"]
        nodetype_and_container_level_cpu_usage=return_dict["cpu_usages"]["nodetype_and_container_level_usages"]
        del return_dict["cpu_usages"]["nodetype_and_container_level_usages"]
        # for nodetype in exclude_nodetypes:
        #     try:del nodetype_and_container_level_cpu_usage[nodetype]
        #     except:pass
        #     try:del nodetype_and_application_level_cpu_usage[nodetype]
        #     except:pass

        return_dict.update({"cpu_usages_analysis" : {
            "nodetype_and_application_level_cpu_usages":nodetype_and_application_level_cpu_usage,
            "nodetype_and_container_level_cpu_usages":nodetype_and_container_level_cpu_usage
        }})

        return return_dict
    
    def get_complete_result(self):
        total_result_for_report=self.collect_total_usages(for_report=True)
        total_result_for_querying=self.collect_total_usages(for_report=False)
        return {
            "resource_utilization_for_report":total_result_for_report,
            "resource_utilization_for_querying":total_result_for_querying
        }


if __name__=='__main__':
    print("Testing active connections by app...")
    from settings import configuration
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

    active_obj = resource_usages(configuration('longevity_nodes.json') , start_timestamp,end_timestamp,hours=hours)
    # total_result_for_querying = active_obj.collect_total_usages(for_report=False)
    total_result_for_report = active_obj.collect_total_usages(for_report=True)

    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Osquery_LoadTests']
    collection = db['Testing'] 

    data_to_insert={}
    data_to_insert["start_str_ist"] = start_time_str
    data_to_insert["hours"] = hours

    data_to_insert["resource_utilization_for_report"] = total_result_for_report
    # data_to_insert["resource_utilization"] = total_result_for_querying
    collection.insert_one(data_to_insert)