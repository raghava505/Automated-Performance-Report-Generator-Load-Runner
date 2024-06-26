import json
from datetime import datetime,timedelta
import pytz
from config_vars import *
import logging

class stack_configuration:
    def __init__(self,variables):

        start_time_str_ist = variables["start_time_str_ist"]
        self.hours=variables["load_duration_in_hrs"]
        self.test_env_file_path = f'{STACK_JSONS_PATH}/{variables["test_env_file_name"]}'

        with open(self.test_env_file_path , 'r') as file:
            stack_details = json.load(file)
            
        self.monitoring_ip=  stack_details["monitoring_node_ip"]
        self.prometheus_path = f"http://{self.monitoring_ip}:{PROMETHEUS_PORT}"
        self.kube_prometheus_path = f"http://{self.monitoring_ip}:{KUBE_PROMETHEUS_PORT}"

        self.execute_kafka_topics_script_in = stack_details["execute_kafka_topics_script_in"]      
        self.execute_trino_queries_in = stack_details["execute_trino_queries_in"]
            
        format_data = "%Y-%m-%d %H:%M"
        ist_timezone = pytz.timezone('Asia/Kolkata')
        utc_timezone = pytz.utc

        start_time_IST = ist_timezone.localize(datetime.strptime(start_time_str_ist, '%Y-%m-%d %H:%M'))
        self.start_time_UTC = start_time_IST.astimezone(utc_timezone)

        self.end_time_str_ist=(start_time_IST + timedelta(hours=self.hours)).strftime(format_data)
        end_time_IST = ist_timezone.localize(datetime.strptime(self.end_time_str_ist, '%Y-%m-%d %H:%M'))
        self.end_time_UTC = end_time_IST.astimezone(utc_timezone)

        self.start_timestamp = int(start_time_IST.timestamp())
        self.start_time_str_utc = self.start_time_UTC.strftime(format_data)

        self.end_timestamp = int(end_time_IST.timestamp())
        self.end_time_str_utc = self.end_time_UTC.strftime(format_data)

        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            log_file_name = f'{variables["load_type"]}_{variables["load_name"]}_{variables["build"]}_{stack_details["stack"]}_{formatted_time}.log'
        except Exception as e:
            log_file_name = f"{formatted_time}.log"
        os.makedirs(BASE_LOGS_PATH,exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=f"{BASE_LOGS_PATH}/{log_file_name}",  # Log messages to a file (optional)
            filemode='w'  # Overwrite the log file each time (use 'a' for appending)
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger('').addHandler(console_handler)

        self.log = logging

        self.log.info(f" starttime and endtime strings in IST are : {start_time_str_ist }, {self.end_time_str_ist}")
        self.log.info(f" starttime and endtime datetime objects in IST are : {start_time_IST} , {end_time_IST}")
        self.log.info(f" starttime and endtime strings in UTC are : {self.start_time_str_utc} , {self.end_time_str_utc}")
        self.log.info(f" starttime and endtime datetime objects in UTC are : {self.start_time_UTC} , {self.end_time_UTC}")
        self.log.info(f" starttime and endtime unix time stamps based on ist time are : {self.start_timestamp} , {self.end_timestamp}")
        self.log.info(f" user inputs : {json.dumps(variables, indent=4)}")