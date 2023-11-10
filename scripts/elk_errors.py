import requests
from elasticsearch import Elasticsearch
import datetime
import os
import sys
from datetime import datetime
import json
import paramiko
import pytz

class Elk_erros:
    def __init__(self,start_timestamp,end_timestamp,prom_con_obj,):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp

        self.test_env_file_path=prom_con_obj.test_env_file_path
        self.PROMETHEUS = prom_con_obj.prometheus_path
        self.API_PATH = prom_con_obj.prom_point_api_path
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password
        with open(self.test_env_file_path, 'r') as file:
            self.stack_details = json.load(file)


        self.contents = ["ruleengine","tls","ngnix","configbd","metastoredb","pgbouncer","osqueryIngestion","redis","spark","archival","compaction"]


        self.elasticsearch_host = f"http://{self.stack_details['elk_url']}:9200"

        self.elastic_client = Elasticsearch(hosts=[self.elasticsearch_host],timeout=1800)

        dt_object = datetime.utcfromtimestamp(start_timestamp)
        self.formatted_starttime = dt_object.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        dt_object = datetime.utcfromtimestamp(end_timestamp)
        self.formatted_endtime = dt_object.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        self.index_name="uptycs-*"

    def body(self,log_type):
        body_error= {
            "query": {
            "bool" : {
            "must" : [
                            { "match": { "log_type.keyword": { "query": log_type} } },
                            { "match": { "message": { "query": "error"} } },

                {
                "range": {
            "@timestamp": {
                "time_zone": "+01:00",
            "gte": self.formatted_starttime,
            "lte": self.formatted_endtime,
            }
            }
                }
            ]
        }
        },
        "aggs": {
            "categories": {
            "categorize_text": {
                "field": "message"
            }
            }
        }
        }

        return [body_error]


    def elk(self):
        result_dict = {}
        for log_type in self.contents:
            body_array = self.body(log_type)
            result_error = self.elastic_client.search(index=self.index_name, body=body_array[0], size=0)
            error_bucket = result_error["aggregations"]["categories"]["buckets"]
            result_dict[log_type] = error_bucket
        return result_dict

    def fetch_errors(self):
        result = self.elk()
        save_dict = {}
        for log_type, items in result.items():
            save_dict[log_type] = []
            for item in items:
                error_message = item['key']
                count = item['doc_count']
                save_dict[log_type].append({"Error Message": error_message, "Count": count})
        print(save_dict)
        return save_dict

