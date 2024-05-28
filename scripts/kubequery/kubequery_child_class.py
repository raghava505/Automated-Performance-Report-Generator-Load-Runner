from parent_load_details import parent
import copy
from collections import defaultdict

class kubequery_child(parent):
    load_specific_details={
                "KubeQuery_SingleCustomer":{
                    "test_title": "Kubequery and K8sosquery Load",
                },
                "SelfManaged_SingleCustomer":{
                    "test_title": "SelfManaged Containers Load"
                }, 
                "KubeQuery_and_SelfManaged_Combined": {
                    "test_title": "KubeQuery and SelfManaged Combined",
                }
    }

    @classmethod
    @property
    def common_app_names(cls):
        temp = copy.deepcopy(parent.common_app_names)
        # temp['sum'].extend(["genericStateManagerExecutor"])
        final = {'sum':["genericStateManagerExecutor"] + temp['sum'] , "avg":[]}
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
        final = ["osquery-state-manager-deployment.*", "kubernetes-schedule-runner-deployment.*"] + temp
        return final
    
    @classmethod
    @property
    def list_of_observations_to_make(cls):
        return [
                    "Check for agentkubequery Topic Lag",
                    "Check for containers Topic Lag",
                    "Check for kubestatemanagerGroup Lag",
                    "Check for containersGroup Lag",
                    'Check for Ingestion lag',
                    'Check for Rule engine Lag',
                    'Check for db-events Lag',
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