from parent_load_details import parent
import copy
from collections import defaultdict

class osquery_child(parent):
    load_specific_details={
            "MultiCustomer" : {
                "test_title": "Multiple Customer Rule Engine and Control Plane Load",
                "RuleEngine and ControlPlane Load Details" : {
                    "total_number_of_customers": "100",
                    "number_of_customers_with_auto_exception_enabled": "0",
                    "total_assets": "10K Control Plane + 10K Multi customer",
                    "assets_per_cust":"100",
                    "records_sent_per_hour_per_customer": "6.48 million", #"5.44 million", 
                    "records_sent_per_hour" : "648 million", # "653 million", 
                    "input_file": "rhel7-6tab_12rec.log",
                    "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events"
                }
            },
            "SingleCustomer":{
                "test_title": "Single Customer Rule Engine Load",
                "RuleEngine and ControlPlane Load Details" : {
                    "total_number_of_customers": 1,
                    "number_of_customers_with_auto_exception_enabled": 1,
                    "total_assets": "10368",
                    "assets_per_cust":"10368",
                    "records_sent_per_hour": "671 million",
                    "input_file": "rhel7-6tab_12rec.log",
                    "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events",
                }
            },
            "ControlPlane":{
                "total_number_of_customers": "1",
                "test_title": "Control Plane Load",
                "total_assets": "60K",
                "redis_switchover_case_time_ist":""
            },
            "Testing" : {
                "total_number_of_customers": "120",
                "number_of_customers_with_auto_exception_enabled": "0",
                "test_title": "Multiple Customer Rule Engine and Control Plane Load",
                "RuleEngine and ControlPlane Load Details" : {
                    "total_assets": "30K Control Plane + 10K Multi customer",
                    "assets_per_cust":"84",
                    "records_sent_per_hour_per_customer": "5.44 million", 
                    "records_sent_per_hour" : "653 million", 
                    "input_file": "rhel7-6tab_12rec.log",
                    "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events"
                }
           },
    }
    load_specific_details = defaultdict(lambda: None, load_specific_details)

    @classmethod
    @property
    def mon_spark_topic_names(cls):
        temp = copy.deepcopy(parent.mon_spark_topic_names)
        temp.extend(["agentosquery"])
        return temp
    
    @classmethod
    @property
    def common_app_names(cls):
        temp = copy.deepcopy(parent.common_app_names)
        temp['sum'].extend(["/opt/uptycs/cloud/go/bin/ruleEngine-production-ruleengine"])
        return temp
    
    @classmethod
    @property
    def kafka_group_names(cls):
        temp = copy.deepcopy(parent.kafka_group_names)
        temp.extend(["op"])
        return temp