import sys
#sys.path.append('cloudquery/') 
from .api_func import *
from .configs import *
from . import configs
from .get_logs import LOGScriptRunner
from pathlib import Path
from datetime import datetime, timedelta, timezone
import os
import json
import jwt
import requests
import urllib3
import multiprocessing
import pandas as pd
import concurrent


PROJECT_ROOT = Path(__file__).resolve().parent

class cloud_accuracy:

    def __init__(self,stack_obj,variables):
        # self.stack_obj=stack_obj
        format_data = "%Y-%m-%d %H:%M"
        start_time = stack_obj.start_time_UTC - timedelta(minutes=10)
        self.load_start = start_time.strftime(format_data)
        end_time = stack_obj.end_time_UTC + timedelta(minutes=10)
        self.load_end = end_time.strftime(format_data)

        self.load_name = variables['load_name']
        self.load_type = variables['load_type']

        self.api_path=None
        self.total_counts = 'total_counts_'

        self.upt_day="".join(str(stack_obj.start_time_UTC.strftime("%Y-%m-%d")).split('-'))

    def global_query(self,data,table):
        
        print(f"Fetching records for table: {table} from customer: {data['customerId']}")
        stack_keys = open_js_safely(self.api_path)
        mglobal_query_api = query_api.format(data['domain'],data['domainSuffix'],data['customerId'])
        pl=payload["query"].format(table,self.upt_day,self.load_start,self.load_end)
        payload["query"]=pl
        output2 = post_api(data,mglobal_query_api,payload)
        job_id= output2['id']
        n_result_api =result_api.format(data['domain'], data['domainSuffix'], data['customerId'],job_id)
        payload["query"]="select upt_added,count(*) from {} where upt_day >= {} and upt_time >= timestamp '{}' and upt_time < timestamp '{}' group by upt_added;"

        if output2['status']=="FINISHED":
            response=get_api(data,n_result_api)
            print(response['items'][0]['rowData']['_col0'])
        else:
            while output2['status'] not in ['FINISHED', 'ERROR']:
                time.sleep(5)
                n_api=mglobal_query_api+'/'+job_id
                output2=get_api(data,n_api)
            if output2['status'] == 'ERROR':
                print('global query failed' )
                print(f"An ERROR occurred: {output2['error']['detail']['message']}")
            else :
                response=get_api(data,n_result_api)
                return response
                

    def expected(self):
        
        for filename in os.listdir(json_directory):
            if filename.endswith(".json"):
                print(os.path.join(json_directory, filename))
                with open(os.path.join(json_directory, filename), "r") as file1:
                    data = json.load(file1)
                
                
                for table_name, table_values in data.items():
                    if table_name in self.total_counts:
                        for operation, count in table_values.items():
                            self.total_counts[table_name][operation] += count


    def execute_query(self,table,customer, event_count, upt_added_true, upt_added_false):
        
        resp = self.global_query(customer,table)
        
        if resp!=None:
            if "aws_cloudtrail_events" in query_api or "gcp_cloud_log_events" in query_api:
                with event_count.get_lock():
                    event_count.value += resp["items"][0]["rowData"]["_col0"]
            else:
                for item in resp["items"]:
                    upt_added = item["rowData"]["upt_added"]
                    count = item["rowData"]["_col1"]
                    if upt_added:
                        with upt_added_true.get_lock():
                            upt_added_true.value += count
                    else:
                        with upt_added_false.get_lock():
                            upt_added_false.value += count



    def table_accuracy(self,data, table, actual_true_count,actual_false_count,expected_true_count,expected_false_count):
        accuracy_true = round(((actual_true_count +1) / (expected_true_count+1)) * 100, 2)
        accuracy_false= round(((actual_false_count+1) / (expected_false_count+1)) * 100, 2)
        data[table] = {"Actual inserted records":actual_true_count, "Actual deleted records": actual_false_count, "Expected inserted records":expected_true_count, "Expected deleted records": expected_false_count,  "Accuracy for inserted records": accuracy_true, "Accuracy for deleted records":accuracy_false}
        print(data[table])

    def multi_accuracy(self, data, file):
        manager = multiprocessing.Manager()
        result_dict = manager.dict()

        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = []

            for table in self.total_counts:
                futures.append(executor.submit(self.process_table, table, data, file, result_dict))

            for future in concurrent.futures.as_completed(futures):
                future.result()

        return dict(result_dict)

    def process_table(self, table, data, file, result_dict):
        manager = multiprocessing.Manager()
        table_result_dict = manager.dict()

        upt_added_true = multiprocessing.Value('i', 0)
        upt_added_false = multiprocessing.Value('i', 0)
        event_count = multiprocessing.Value('i', 0)
        processes = []

        for customer in json.loads(file):
            p = multiprocessing.Process(target=self.execute_query, args=(table, customer, event_count, upt_added_true, upt_added_false))
            p.start()
            processes.append(p)

        for p in processes:
            p.join(timeout=20)

        expected_true_count = self.total_counts[table].get("added", self.total_counts[table].get("created", 1))
        expected_false_count = self.total_counts[table].get("removed", 1)

        table_result_dict[table] = {
            "Actual inserted records": upt_added_true.value,
            "Actual deleted records": upt_added_false.value,
            "Expected inserted records": expected_true_count,
            "Expected deleted records": expected_false_count,
            "Accuracy for inserted records": round(((upt_added_true.value + 1) / (expected_true_count + 1)) * 100, 2),
            "Accuracy for deleted records": round(((upt_added_false.value + 1) / (expected_false_count + 1)) * 100, 2)
        }

        result_dict.update(table_result_dict)
        print(table_result_dict)

    def multi_tables_accuracy(self, file):
        expected_data = {}
        self.expected()
        expected_data = self.multi_accuracy(expected_data, file)
        df = pd.DataFrame(expected_data)
        df=df.T
        df = df.reset_index().rename(columns={'index': 'table'})
        self.stack_obj.log.info(df)
        return_dict ={
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[]
                },
                "table":df.to_dict(orient="records")
            }
        return return_dict
        

    def calculate_accuracy(self):
        save_dict={}
        obj = LOGScriptRunner()
        print(self.load_name)
        if(self.load_name=="AWS_MultiCustomer" or self.load_name == "GCP_MultiCustomer"):
            print(1)
            obj.get_log(obj.simulators1,self.load_name)
            self.api_path=api_path_multi_mercury
            self.total_counts = getattr(configs, f'total_counts_{self.load_name.split("_")[0]}', None)
            fs = open(self.api_path)
            file = fs.read()
            save_dict[self.load_name.split("_")[0]]=self.multi_tables_accuracy(file)

        elif(self.load_name == "Azure_MultiCustomer"):
            print("Azure_MultiCustomer")
            obj.get_log(obj.azure_s18sims,self.load_name)
            self.api_path=api_path_multi_virgo
            self.total_counts = getattr(configs, f'total_counts_Azure', None)
            fs = open(self.api_path)
            file = fs.read()
            save_dict["Azure"]=self.multi_tables_accuracy(file)

        elif(self.load_name == "AWS_SingleCustomer"):
            print(2)
            obj.get_log(obj.simulators1,self.load_name)
            self.api_path=api_path_single_mercury
            self.total_counts = getattr(configs, f'total_counts_AWS', None)
            fs = open(self.api_path)
            file = fs.read()
            save_dict["AWS"]=self.multi_tables_accuracy(file)
        
        elif(self.load_type == 'osquery_cloudquery_combined'):
            print(3)
            obj.get_log(obj.simulators2,"AWS_MultiCustomer")
            self.api_path=api_path_multi_longevity
            self.total_counts = getattr(configs, f'total_counts_AWS', None)
            fs = open(self.api_path)
            file = fs.read()
            save_dict["AWS"]=self.multi_tables_accuracy(file)

            obj.get_log(obj.simulators3,"GCP_MultiCustomer")
            self.total_counts = getattr(configs, f'total_counts_GCP', None)
            save_dict["GCP"]=self.multi_tables_accuracy(file)

        elif(self.load_type == 'all_loads_combined'):
            print(3)
            obj.get_log(obj.simulators2,"AWS_MultiCustomer")
            self.api_path=api_path_multi_longevity
            self.total_counts = getattr(configs, f'total_counts_AWS', None)
            fs = open(self.api_path)
            file = fs.read()
            save_dict["AWS"]=self.multi_tables_accuracy(file)
            
            obj.get_log(obj.azure_simulators,"Azure_MultiCustomer")
            self.total_counts = getattr(configs, f'total_counts_Azure', None)
            save_dict["Azure"]=self.multi_tables_accuracy(file)

            obj.get_log(obj.simulators3,"GCP_MultiCustomer")
            self.total_counts = getattr(configs, f'total_counts_GCP', None)
            save_dict["GCP"]=self.multi_tables_accuracy(file)

        return save_dict


