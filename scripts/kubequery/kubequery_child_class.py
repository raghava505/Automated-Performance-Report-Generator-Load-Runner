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
    
    