from parent_load_details import parent
import copy
from collections import defaultdict

class kubequery_child(parent):
    load_specific_details={
                "KubeQuery_SingleCustomer":{
                "total_number_of_customers": 1,
                "test_title": "Kubequery and K8sosquery Load",
                "total_assets": 500,
                "total_number_of_clusters": 10
            },
                "SelfManaged_SingleCustomer":{
                "total_number_of_customers": 1,
                "test_title": "SelfManaged Containers Load",
                "total_assets": 200,
            }, 
                "KubeQuery_and_SelfManaged_Combined": {
                "test_title": "KubeQuery_and_SelfManaged_Combined",
                "total_number_of_customers_for_Kubequery": 1,
                "total_number_of_clusters": 20,
                "total_assets_for_Kubequery": 800,
                "total_namespaces_for_Kubequery": 2000,
                "total_pods_for_Kubequery": 40000,
                "total_number_of_customers_for_SelfManaged": 1,
                "total_assets_for_SelfManaged": 200,
            }
    }

    @classmethod
    @property
    def common_app_names(cls):
        temp = copy.deepcopy(parent.common_app_names)
        temp['sum'].extend(["genericStateManagerExecutor"])
        return temp
    
    @classmethod
    @property
    def mon_spark_topic_names(cls):
        temp = copy.deepcopy(parent.mon_spark_topic_names)
        temp.extend(["state","agentkubequery"])
        return temp
    
    @classmethod
    @property
    def kafka_group_names(cls):
        temp = copy.deepcopy(parent.kafka_group_names)
        temp.extend(["kubeStateManagerGroup"])
        return temp
    
    @classmethod
    def get_app_level_RAM_used_percentage_queries(cls):
        temp = copy.deepcopy(parent.get_app_level_RAM_used_percentage_queries())
        more_memory_queries={
            "Kubernetes State Manager memory usage":("sum(uptycs_docker_mem_used{container_name=\"kubernetes-state-manager\"}) by (host_name)" , ["host_name"],'bytes'),
        }
        temp.update(more_memory_queries)
        return temp
    
    @classmethod
    def get_app_level_CPU_used_cores_queries(cls):
        temp = copy.deepcopy(parent.get_app_level_CPU_used_cores_queries())
        more_cpu_queries={
            "Kubernetes State Manager CPU usage":("sum(uptycs_docker_cpu_stats{container_name=\"kubernetes-state-manager\"}) by (host_name)" , ["host_name"],'%'),
        }
        temp.update(more_cpu_queries)
        return temp
    