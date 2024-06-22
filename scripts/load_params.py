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


def execute_on_trino_middleware(key,target_node,query,conn_object,schema) -> dict:
    res = {}
    res[key] = ""
    # print(f"Executing for {key}")
    # command = f"sudo -u monkey TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --insecure --server https://localhost:5665 --schema upt_{schema} --user uptycs --catalog uptycs --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/etc/presto/presto.jks --execute \"{query}\""
    try:
        value = execute_trino_query(node=target_node,query=query,schema=schema)
        # print(value)
        
        value = value.replace('"', ' ')
        value = int(value)
        res[key] = value
        
        return res
    except Exception as err:
        print(f"ERR: load_params execute_on_trino_middleware {key} => {err}")
        return res

class Load_Params:
    def __init__(self, connection_object) -> None:
        start_time=connection_object.start_time_UTC
        test_env_file_path=connection_object.test_env_file_path
        with open(test_env_file_path,"r") as file:
            data = json.load(file)
        
        self.schema = data["domain"]
        if self.schema ==  "longevity":
            self.schema = "longevity1"
        del data
        
        self.conn_object = connection_object
        self.start_time = start_time
        self.upt_day="".join(str(start_time.strftime("%Y-%m-%d")).split('-'))
        self.conn_object.ssh_port = 22
        self.conn_object.abacus_username = "abacus"
        self.conn_object.abacus_password = "abacus"
        self.target_node = self.conn_object.execute_trino_queries_in
        
        
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
                    futures.append(executor.submit(execute_on_trino_middleware,key,self.target_node,query,self.conn_object,self.schema))
            
                for key, value in configurations["k8s_params"].items():
                    query = f"select count(*) from {value.table_name} where upt_day>={self.upt_day} and {value.condition};"
                    futures.append(executor.submit(execute_on_trino_middleware,key,self.target_node,query,self.conn_object,self.schema))
                    
            if "SelfManaged" in load_name:
                for key, value in configurations["sm_params_upt"].items():
                    query = f"select count(*) from {value.table_name}  where {value.column} like '{value.match_pattern}';"
                    futures.append(executor.submit(execute_on_trino_middleware,key,self.target_node,query,self.conn_object,self.schema))
            
            for future in cf.as_completed(futures):
                result = future.result()
                total_params = total_params | result
        
        return total_params
                            
            
