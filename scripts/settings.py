import json
from datetime import datetime,timedelta
import pytz
from config_vars import *

class stack_configuration:
    def __init__(self,test_env_file_name,start_time_str_ist,load_duration_in_hrs):
        self.test_env_file_path = f"{STACK_JSONS_PATH}/{test_env_file_name}"

        with open(self.test_env_file_path , 'r') as file:
            stack_details = json.load(file)
            
        self.monitoring_ip=  stack_details["monitoring_node_ip"]
        self.prometheus_path = f"http://{self.monitoring_ip}:{prometheus_port}"
        self.kube_prometheus_path = f"http://{self.monitoring_ip}:{kube_prometheus_port}"

        self.execute_kafka_topics_script_in = stack_details["execute_kafka_topics_script_in"]      
        self.execute_trino_queries_in = stack_details["execute_trino_queries_in"]

        try:
            self.elastic_ip=stack_details['elastic']
        except Exception as e:
            print("Elastic node ip not found for your stack " , e)
    
            
        format_data = "%Y-%m-%d %H:%M"
        ist_timezone = pytz.timezone('Asia/Kolkata')
        utc_timezone = pytz.utc

        start_time_IST = ist_timezone.localize(datetime.strptime(start_time_str_ist, '%Y-%m-%d %H:%M'))
        self.start_time_UTC = start_time_IST.astimezone(utc_timezone)

        self.end_time_str_ist=(start_time_IST + timedelta(hours=load_duration_in_hrs)).strftime(format_data)
        end_time_IST = ist_timezone.localize(datetime.strptime(self.end_time_str_ist, '%Y-%m-%d %H:%M'))
        self.end_time_UTC = end_time_IST.astimezone(utc_timezone)

        self.start_timestamp = int(start_time_IST.timestamp())
        self.start_time_str_utc = self.start_time_UTC.strftime(format_data)

        self.end_timestamp = int(end_time_IST.timestamp())
        self.end_time_str_utc = self.end_time_UTC.strftime(format_data)

        self.hours=load_duration_in_hrs

        print("------ starttime and endtime strings in IST are : ", start_time_str_ist , self.end_time_str_ist)
        print("------ starttime and endtime datetime objects in IST are : ", start_time_IST , end_time_IST)
        print("------ starttime and endtime strings in UTC are : ", self.start_time_str_utc , self.end_time_str_utc)
        print("------ starttime and endtime datetime objects in UTC are : ", self.start_time_UTC , self.end_time_UTC)
        print("------ starttime and endtime unix time stamps based on ist time are : ", self.start_timestamp , self.end_timestamp)