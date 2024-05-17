import json,os
from helper import extract_stack_details



class configuration:
    def __init__(self,test_env_file_name=None , fetch_node_parameters_before_generating_report=False):
        self.prometheus_port = "9090"
        self.kube_prometheus_port = "31090"
        self.prom_api_path = "/api/v1/query_range"
        self.prom_point_api_path = "/api/v1/query"
        self.ssh_port = 22  # SSH port (default is 22)
        self.abacus_username = 'abacus'  
        self.abacus_password = 'abacus' 
        self.ROOT_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.base_stack_config_path = f"{self.ROOT_PATH}/config"
        self.mongo_connection_string = "mongodb://localhost:27017"
        self.api_loads_folder_path = "/home/abacus/apache-jmeter-5.6.2/bin/reports/"
        self.presto_loads_folder_path = "/home/abacus/benchto_reports/"
        self.kube_metrics = ["container_memory_working_set_bytes","container_cpu_usage_seconds_total"]
        self.perf_prod_dashboard = "192.168.146.69"

        if test_env_file_name:
            self.test_env_file_path = f"{self.base_stack_config_path}/{test_env_file_name}"
            #extract all the stack details
            if fetch_node_parameters_before_generating_report == True:
                extract_stack_details(self.test_env_file_path,self)
            with open(self.test_env_file_path , 'r') as file:
                stack_details = json.load(file)
                
            self.monitoring_ip=  stack_details["monitoring_node"][0]
            self.prometheus_path = f"http://{self.monitoring_ip}:{self.prometheus_port}"
            self.kube_prometheus_path = f"http://{self.monitoring_ip}:{self.kube_prometheus_port}"
            self.execute_kafka_topics_script_in = stack_details['pnodes'][0]       
            self.execute_trino_queries_in = stack_details['dnodes'][0]
            try:
                self.elastic_ip=stack_details['elastic']
            except Exception as e:
                print("Elastic node ip not found for your stack " , e)