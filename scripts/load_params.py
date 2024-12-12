import concurrent.futures as cf
from helper import execute_trino_query , measure_time
import json


class Config():
    def __init__(self, table_name, column="", match_pattern="%", condition="") -> None:
        self.table_name = table_name
        self.column = column
        self.match_pattern = match_pattern
        self.condition = condition
        

configurations = {
    "k8s_params_upt" : {
        "k8s_clusters" : Config(table_name="upt_kubernetes_clusters", column="cluster_name"),
        "k8s_nodes" : Config(table_name="upt_kubernetes_nodes_current", column="cluster_name"),
        "k8s_namespaces" : Config(table_name="upt_kubernetes_namespaces_current", column="cluster_name"),
        "k8s_pods" : Config(table_name="upt_kubernetes_pods_current", column="cluster_name"),
        "k8s_containers" : Config(table_name="upt_kubernetes_pods_containers_current", column="cluster_name")
    },
    "k8s_params" : {
        "total_k8s_containers_created" : Config(table_name="kubernetes_pod_containers", condition="upt_added = True"),
        "total_k8s_containers_deleted" : Config(table_name="kubernetes_pod_containers", condition="upt_added = False"),
    },
    "sm_params_upt" : {
        "selfmanaged_assets" : Config(table_name="upt_assets", column="host_name", match_pattern="self%"),
        "selfmanaged_containers" : Config(table_name="upt_containers_current", column="hostname", match_pattern="self%"),
    }
}


def execute_on_trino_middleware(key,target_node,query,stack_obj,domain) -> dict:
    res = {}
    res[key] = ""
    # print(f"Executing for {key}")
    # command = f"sudo -u monkey TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --insecure --server https://localhost:5665 --domain upt_{domain} --user uptycs --catalog uptycs --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/etc/presto/presto.jks --execute \"{query}\""
    try:
        value = execute_trino_query(node=target_node,query=query,stack_obj=stack_obj,domain=domain)
        # print(value)
        
        value = value.replace('"', ' ')
        value = int(value)
        res[key] = value
        
        return res
    except Exception as err:
        stack_obj.log.error(f"error occured in load_params execute_on_trino_middleware {key} => {err}")
        return res

class Load_Params:
    def __init__(self, stack_obj,domain) -> None:
        start_time=stack_obj.start_time_UTC

        if domain ==  "longevity":
            self.domain = "longevity1"
        else:
            self.domain = domain

        self.stack_obj = stack_obj
        self.upt_day="".join(str(start_time.strftime("%Y-%m-%d")).split('-'))
        self.target_node = self.stack_obj.first_pnode
        
        
    @measure_time
    def get_load_params(self, load_name) -> dict:   
        
        total_params = {
            "k8s_clusters": 0,
            "k8s_nodes": 0,
            "k8s_namespaces": 0,
            "k8s_pods": 0,
            "k8s_containers": 0,
            "total_k8s_containers_created": 0,
            "total_k8s_containers_deleted": 0,
            "selfmanaged_assets": 0,
            "selfmanaged_containers": 0,
        }
        
        with cf.ThreadPoolExecutor(max_workers=10,thread_name_prefix="param") as executor:
            futures = []
            if "KubeQuery" in load_name:
                for key, value in configurations["k8s_params_upt"].items():
                    query = f"select count(*) from {value.table_name} where {value.column} like '{value.match_pattern}';"
                    futures.append(executor.submit(execute_on_trino_middleware,key,self.target_node,query,self.stack_obj,self.domain))
            
                for key, value in configurations["k8s_params"].items():
                    query = f"select count(*) from {value.table_name} where upt_day>={self.upt_day} and {value.condition};"
                    futures.append(executor.submit(execute_on_trino_middleware,key,self.target_node,query,self.stack_obj,self.domain))
                    
            if "SelfManaged" in load_name:
                for key, value in configurations["sm_params_upt"].items():
                    query = f"select count(*) from {value.table_name}  where {value.column} like '{value.match_pattern}';"
                    futures.append(executor.submit(execute_on_trino_middleware,key,self.target_node,query,self.stack_obj,self.domain))
            
            for future in cf.as_completed(futures):
                result = future.result()
                total_params = total_params | result
        
        return total_params
                            
            
