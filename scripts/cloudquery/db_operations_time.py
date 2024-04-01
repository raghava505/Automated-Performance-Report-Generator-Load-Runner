import sys 
import time
import pymongo
from datetime import datetime, timedelta
import json
from datetime import datetime
import requests
import json
import pytz
import os



class DB_OPERATIONS_TIME:
    def __init__(self,start_timestamp,end_timestamp,prom_con_obj):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp
        self.PROMETHEUS = prom_con_obj.prometheus_path
        self.API_PATH = prom_con_obj.prom_point_api_path
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password

                
        self.query = "sort_desc(sum(curr_state_db_op_sec_bucket) by(le))"
        #self.query2 = "sort_desc(rate(curr_state_db_op_sec_sum{ job="cloudquery"}[5m])/rate(curr_state_db_op_sec_count{ job="cloudquery"}[5m])) > 0.1"

    def extract_data(self,query,timestamp):
        final=dict()
        final={}
        PARAMS = {
            'query': query,
            'time' : timestamp
        }
        response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
        print(f"Excecuting query : {query} at timestamp {timestamp} , Status code : {response.status_code}")
        if response.status_code != 200:print("ERROR : Request failed")
        result = response.json()['data']['result']
        

        return result
    
        
    def db_operations(self):
        result = self.extract_data(self.query,self.curr_ist_start_time)
        save_dict={}
        for item in result:
            le_value = item['metric']['le']
            value = int(item['value'][1])
            save_dict[str(item['metric'])] = value
        print(save_dict)
        return save_dict
    
    
