from parent_load_details import parent
import copy
from collections import defaultdict

class osquery_child(parent):
    load_specific_details={
            "MultiCustomer" : {
                "total_number_of_customers": "120",
                "number_of_customers_with_auto_exception_enabled": "0",
                "test_title": "Multiple Customer Rule Engine and Control Plane Load",
                "total_assets": "30K Control Plane + 10K Multi customer",
                "assets_per_cust":"84",
                "records_sent_per_hour_per_customer": "5.44 million", 
                "records_sent_per_hour" : "653 million", 
                "input_file": "rhel7-6tab_12rec.log",
                "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events"
            },
            "SingleCustomer":{
                "total_number_of_customers": 1,
                "number_of_customers_with_auto_exception_enabled": 1,
                "test_title": "Single Customer Rule Engine Load",
                "total_assets": "24576",
                "assets_per_cust":"24576",
                "records_sent_per_hour": "1.592 B",
                "input_file": "rhel7-6tab_12rec.log",
                "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events"
            },
            "ControlPlane":{
                "total_number_of_customers": "1",
                "test_title": "Single Customer Control Plane Load",
                "total_assets": "120K",
                "redis_switchover_case_time_ist":""
            },
            "Testing" : {
                "total_number_of_customers": "120",
                "number_of_customers_with_auto_exception_enabled": "0",
                "test_title": "Multiple Customer Rule Engine and Control Plane Load",
                "total_assets": "30K Control Plane + 10K Multi customer",
                "assets_per_cust":"84",
                "records_sent_per_hour_per_customer": "5.44 million", 
                "records_sent_per_hour" : "653 million", 
                "input_file": "rhel7-6tab_12rec.log",
                "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events"
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