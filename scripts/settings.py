import json
from helper import extract_stack_details
from config_vars import *

class stack_configuration:
    def __init__(self,test_env_file_name):
        self.test_env_file_path = f"{base_stack_config_path}/{test_env_file_name}"

        with open(self.test_env_file_path , 'r') as file:
            stack_details = json.load(file)
            
        self.monitoring_ip=  stack_details["monitoring_node"][0]
        self.prometheus_path = f"http://{self.monitoring_ip}:{prometheus_port}"
        self.kube_prometheus_path = f"http://{self.monitoring_ip}:{kube_prometheus_port}"

        self.execute_kafka_topics_script_in = stack_details["execute_kafka_topics_script_in"]      
        self.execute_trino_queries_in = stack_details["execute_trino_queries_in"]

        try:
            self.elastic_ip=stack_details['elastic']
        except Exception as e:
            print("Elastic node ip not found for your stack " , e)
    
        extract_stack_details(self.test_env_file_path)        #extract all the stack details
