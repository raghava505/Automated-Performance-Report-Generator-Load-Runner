from parent_load_details import parent
import copy
from collections import defaultdict

class kubequery_child(parent):
    load_specific_details={
                "KubeQuery_SingleCustomer":{
                    "total_number_of_customers": 1,
                    "test_title": "Kubequery and K8sosquery Load",
                    "total_number_of_clusters": 20,
                    "total_assets_for_Kubequery": 800,
                    "total_namespaces_for_Kubequery": 2000,
                    "total_pods_for_Kubequery": 40000,
                },
                "SelfManaged_SingleCustomer":{
                    "total_number_of_customers": 1,
                    "test_title": "SelfManaged Containers Load",
                    "total_assets": 200,
                }, 
                "KubeQuery_and_SelfManaged_Combined": {
                    "test_title": "KubeQuery_and_SelfManaged_Combined",

                    "Test Parameters":{
                        "total_number_of_customers_for_Kubequery": 1,
                        "total_number_of_clusters": 20,
                        "total_assets_for_Kubequery": 800,
                        "total_namespaces_for_Kubequery": 2000,
                        "total_pods_for_Kubequery": 40000,

                        "Containers created":0,
                        "Containers deleted":0,
                        
                        "total_number_of_customers_for_SelfManaged": 1,
                        "total_assets_for_SelfManaged": 200,
                    },
                }
    }

    @classmethod
    @property
    def common_app_names(cls):
        temp = copy.deepcopy(parent.common_app_names)
        # temp['sum'].extend(["genericStateManagerExecutor"])
        final = {'sum':["genericStateManagerExecutor"] + temp['sum']}
        return final
    
    @classmethod
    @property
    def common_container_names(cls):
        temp = copy.deepcopy(parent.common_container_names)
        final = ["kubernetes-state-manager","kubernetes-network-manager","kubernetes-schedule-runner"] + temp
        return final
    
    @classmethod
    @property
    def mon_spark_topic_names(cls):
        temp = copy.deepcopy(parent.mon_spark_topic_names)
        # temp.extend(["state","agentkubequery"])
        final = ["agentkubequery","state","containers","decorators"] + temp
        return final
    
    @classmethod
    @property
    def kafka_group_names(cls):
        temp = copy.deepcopy(parent.kafka_group_names)
        # temp.extend(["kubeStateManagerGroup","containersGroup"])
        final = ["kubeStateManagerGroup","containersGroup"] + temp
        return final
    
    @classmethod
    @property
    def common_pod_names(cls):
        temp = copy.deepcopy(parent.common_pod_names)
        # temp.extend(["osquery-state-manager-deployment.*"])
        final = ["osquery-state-manager-deployment.*"] + temp
        return final
    
    @classmethod
    @property
    def list_of_observations_to_make(cls):
        return [
                    'Check for Ingestion lag',
                    'Check for Rule engine Lag',
                    'Check for db-events Lag',
                    "Check for agentkubequery Topic Lag",
                    "Check for containers Topic Lag",
                    "Check for state topic Lag"
                    'Data loss check for raw tables like processes, process_env etc (accuracy)',
                    'Data loss check for processed data like events, alerts and incidents etc (accuracy)',
                    "Check if CPU/memory utilisation in line with previous sprints. If not, are the differences expected?",
                    'Check for variations in the Count of queries executed on presto',
                    'Triage bugs and check for blockers',
                    'Check if PG master is in sync with replica',
                    'Check for memory leaks',
                    'Check for variation in HDFS disk usage',
                    'Check for variation in PG disk usage',
                    'Check for variation in Kafka disk usage',
                ]