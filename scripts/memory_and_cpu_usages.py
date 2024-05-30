from collections import defaultdict
from helper import execute_prometheus_query,execute_point_prometheus_query
import json

HOST = 'Host'
memory_tag = "Memory"
cpu_tag = "CPU"
memory_unit = "GB"
cpu_unit = "cores"
threshold = 0.03
class MC_comparisions:
    def __init__(self,prom_con_obj,start_timestamp,end_timestamp,hours,include_nodetypes):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp
        self.prom_con_obj=prom_con_obj
        self.hours=hours
        self.include_nodetypes=include_nodetypes

        total_memory_capacity_query = "sum(uptycs_total_memory/(1024*1024)) by (node_type,host_name)"
        memory_result = execute_point_prometheus_query(self.prom_con_obj,self.curr_ist_start_time,total_memory_capacity_query)
        self.node_ram_capacity = {}
        self.all_node_types_mapping=defaultdict(lambda:[])

        for line in memory_result:
            node_name = line["metric"]["host_name"]
            capacity = float(line["value"][1])
            self.node_ram_capacity[node_name] = capacity  
            self.all_node_types_mapping[line["metric"]["node_type"]].append(node_name)
     
        total_cpu_capacity_query = "sum(uptycs_loadavg_cpu_info) by (host_name,cpu_processor)"
        cpu_result = execute_point_prometheus_query(self.prom_con_obj,self.curr_ist_start_time,total_cpu_capacity_query)
        self.node_cores_capacity = {}
        for line in cpu_result:
            node_name = line["metric"]["host_name"]
            cpu_capacity = float(line["metric"]["cpu_processor"]) + 1 
            self.node_cores_capacity[node_name] = cpu_capacity
        
        self.all_node_types=list(self.all_node_types_mapping.keys())
        print("All nodetypes found are : " , self.all_node_types)
        print("Memory capacity : \n" , json.dumps(self.node_ram_capacity,indent=4))
        print("CPU capacity : \n" , json.dumps(self.node_cores_capacity,indent=4))

    def extract_data(self,queries,tag,unit):
        final=dict()
        return_overall = dict()

        for query in queries:
            final[query] = {}
            print(f"-------processing {tag} for {query} (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time})")
            for res in execute_prometheus_query(self.prom_con_obj,self.curr_ist_start_time,self.curr_ist_end_time,queries[query],self.hours):
                hostname = res['metric']['host_name'] 
                avg = res["values"]["average"]
                minimum = res["values"]["minimum"]
                maximum = res["values"]["maximum"]
                final[query][hostname] = {"percentage":{"average":avg , "minimum":minimum , "maximum":maximum}}
                final[query][hostname][unit]={}
                if tag == memory_tag:
                    try:
                        current_host_ram=self.node_ram_capacity[hostname]                
                        final[query][hostname][unit]={
                            'average':avg * float(current_host_ram) / 100,
                            'minimum':minimum * float(current_host_ram) / 100,
                            'maximum':maximum * float(current_host_ram) / 100
                        }
                    except Exception as e:
                        print(f"*****************ERROR: Coudn't find host {hostname} in ram-capacity dictionary. Exception occured while calculating app memory usage for query:{query}. {e}")

                else:
                    if query == HOST:
                        try:
                            current_host_cores=self.node_cores_capacity[hostname]             
                            final[query][hostname][unit]={
                                'average':avg * float(current_host_cores) / 100,
                                'minimum':minimum * float(current_host_cores) / 100,
                                'maximum':maximum * float(current_host_cores) / 100
                            }
                        except Exception as e:
                            print(f"*****************ERROR: Coudn't find host {hostname} in cores-capacity dictionary. Exception occured while calculating app cpu usage for query:{query}. {e}")

                    else:
                        final[query][hostname][unit]={
                            'average':avg/100,
                            'minimum': minimum/100,
                            'maximum': maximum/100
                        }
                
        #calculate overall pnodes,dnodes,pgnodes usage
        new_data = final[HOST]
        for node_type in self.include_nodetypes:
            print(f"Calculating overall {tag} usages for node-type : {node_type}")
            new_sum=0
            flag=0
            for node in self.all_node_types_mapping[node_type]:
                flag=1
                try:
                    new_sum+=new_data[node][unit]["average"]
                except KeyError as e:
                    print(f"ERROR : key {node} not found in : {new_data}")
                    raise RuntimeError(f"ERROR : key {node} is present in {node_type} but not found in host groups from prometheus: {new_data}")
            if flag==1:
                return_overall[node_type] = {f"{unit}":new_sum}
            print(f"{node_type} : {new_sum} {unit}")
        return final,return_overall

    def extract_container_data(self,queries,tag,unit):
        final=dict()
        for query in queries:
            final[query] = {}
            print(f"----------processing {tag} for {query} (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time})")
            for res in execute_prometheus_query(self.prom_con_obj,self.curr_ist_start_time,self.curr_ist_end_time,queries[query],self.hours):
                container_name = res['metric']['container_name']
                avg = res["values"]["average"]
                if avg <= threshold:continue
                minimum = res["values"]["minimum"]
                maximum = res["values"]["maximum"]
                final[query][container_name] = {f"{unit}":{"average":avg , "minimum":minimum , "maximum":maximum}}
        return final 
    def extract_app_data(self,queries,tag,unit):
        final=dict()
        print(f"----------processing application level {tag} usages for (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time})")
        for query in queries:
            print(f"processing {tag} usage for {query} application (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time})")
            result=execute_prometheus_query(self.prom_con_obj,self.curr_ist_start_time,self.curr_ist_end_time,queries[query],self.hours)
            if len(result)==0:
                print(f"WARNING : No data found for : {query}, the query executed is : {queries[query]}")
                continue
            avg = result[0]["values"]["average"]
            minimum = result[0]["values"]["minimum"]
            maximum = result[0]["values"]["maximum"]
            try:
                print(str(query)==str(result[0]['metric']['app_name']))
            except Exception as e:
                print("Warning : ", e)
            final[query] = {"percentage":{"average":avg , "minimum":minimum , "maximum":maximum}}
        return final 
    
    def extract_pod_data(self,queries,tag,unit):
        final=dict()
        print(f"----------processing pod level {tag} usages for (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time})")
        for query in queries:
            print(f"processing {tag} usage for {query} pod (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time})")
            result=execute_prometheus_query(self.prom_con_obj,self.curr_ist_start_time,self.curr_ist_end_time,queries[query],self.hours)
            if len(result)==0:
                print(f"WARNING : No data found for : {query}, the query executed is : {queries[query]}")
                continue
            avg = result[0]["values"]["average"]
            minimum = result[0]["values"]["minimum"]
            maximum = result[0]["values"]["maximum"]
            # try:
            #     print(str(query)==str(result[0]['metric']['node_name']))
            # except Exception as e:
            #     print("Warning : ", e)
            final[query] = {f"{unit}":{"average":avg , "minimum":minimum , "maximum":maximum}}
        return final 

    def make_comparisions(self,app_names,pod_names):
        print("All usage queries to be executed are : ")

        memory_queries = {f"{HOST}" : 'avg((uptycs_memory_used/uptycs_total_memory) * 100)  by (host_name)',}
        memory_queries.update(dict([(app,f"{key}(uptycs_app_memory{{app_name=~'{app}'}}) by (host_name)") for key,app_list in app_names.items() for app in app_list]))

        cpu_queries = {f"{HOST}" : 'avg(100-uptycs_idle_cpu) by (host_name)',}
        cpu_queries.update(dict([(app,f"{key}(uptycs_app_cpu{{app_name=~'{app}'}}) by (host_name)") for key,app_list in app_names.items() for app in app_list]))

        container_memory_queries = {'container' : "sum(uptycs_docker_mem_used{}/(1000*1000*1000)) by (container_name)",}
        container_cpu_queries = {'container' : "sum(uptycs_docker_cpu_stats{}/100) by (container_name)",}

        app_level_memory_queries = dict([(app,f"sum({key}(uptycs_app_memory{{app_name=~'{app}'}}) by (app_name))") for key,app_list in app_names.items() for app in app_list])
        app_level_cpu_queries = dict([(app,f"sum({key}(uptycs_app_cpu{{app_name=~'{app}'}}) by (app_name))") for key,app_list in app_names.items() for app in app_list])

        pod_level_memory_queries = dict([(pod,f'sum(uptycs_kubernetes_memory_stats{{pod=~"{pod}"}}) / (1024*1024*1024)') for pod in pod_names])
        pod_level_cpu_queries = dict([(pod,f'sum(uptycs_kubernetes_cpu_stats{{pod=~"{pod}"}}) / 100') for pod in pod_names])

        app_level_memory_queries["gprofiler perf-record pns"]="sum(uptycs_app_memory{node_type='process',app_name='/app/gprofiler/resources/perf-record--F'}) by (app_name)"
        app_level_memory_queries["gprofiler perf-script pns"]="sum(uptycs_app_memory{node_type='process',app_name='/app/gprofiler/resources/perf-script--F'}) by (app_name)"
        app_level_memory_queries["gprofiler perf-record dns"]="sum(uptycs_app_memory{node_type='data',app_name='/app/gprofiler/resources/perf-record--F'}) by (app_name)"
        app_level_memory_queries["gprofiler perf-script dns"]="sum(uptycs_app_memory{node_type='data',app_name='/app/gprofiler/resources/perf-script--F'}) by (app_name)"
        app_level_cpu_queries["gprofiler perf-record pns"]="sum(uptycs_app_cpu{node_type='process',app_name='/app/gprofiler/resources/perf-record--F'}) by (app_name)"
        app_level_cpu_queries["gprofiler perf-script pns"]="sum(uptycs_app_cpu{node_type='process',app_name='/app/gprofiler/resources/perf-script--F'}) by (app_name)"
        app_level_cpu_queries["gprofiler perf-record dns"]="sum(uptycs_app_cpu{node_type='data',app_name='/app/gprofiler/resources/perf-record--F'}) by (app_name)"
        app_level_cpu_queries["gprofiler perf-script dns"]="sum(uptycs_app_cpu{node_type='data',app_name='/app/gprofiler/resources/perf-script--F'}) by (app_name)"

        all_queries_to_execute={
            "memory_queries":memory_queries,
            "cpu_queries":cpu_queries,
            "container_memory_queries":container_memory_queries,
            "container_cpu_queries":container_cpu_queries,
            "application_level_memory_queries":app_level_memory_queries,
            "application_level_cpu_queries":app_level_cpu_queries,
        }

        # print(json.dumps(all_queries_to_execute, indent=4))

        memory_data,overall_memory_data = self.extract_data(memory_queries,memory_tag,memory_unit)
        cpu_data,overall_cpu_data = self.extract_data(cpu_queries,cpu_tag,cpu_unit)
        container_memory_data =  self.extract_container_data(container_memory_queries,memory_tag,memory_unit)
        container_cpu_data =  self.extract_container_data(container_cpu_queries,cpu_tag,cpu_unit)
        app_memory_data =  self.extract_app_data(app_level_memory_queries,memory_tag,memory_unit)
        app_cpu_data =  self.extract_app_data(app_level_cpu_queries,cpu_tag,cpu_unit)
        
        pod_memory_data =  self.extract_pod_data(pod_level_memory_queries,memory_tag,memory_unit)
        pod_cpu_data =  self.extract_pod_data(pod_level_cpu_queries,cpu_tag,cpu_unit)
        
        current_build_data={
            "node_level_resource_utilization": {
                "memory":memory_data,
                "cpu" : cpu_data,
            },
            "container_level_resource_utilization":{
                "memory":container_memory_data,
                "cpu" : container_cpu_data,
            },
            "application_level_resource_utilization":{
                "memory":app_memory_data,
                "cpu" : app_cpu_data,
            },
            "pod_level_resource_utilization":{
                "memory":pod_memory_data,
                "cpu" : pod_cpu_data,
            }
        }
        return current_build_data,{ "node_level_total_average_resource_utilization":{
                                        "memory":overall_memory_data,
                                        "cpu":overall_cpu_data
                                    }}