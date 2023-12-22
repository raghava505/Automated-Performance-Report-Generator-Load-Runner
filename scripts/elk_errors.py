import requests
from elasticsearch import Elasticsearch
import datetime
import os
import sys
from datetime import datetime
import json
import paramiko
import pytz
import concurrent.futures

class Elk_erros:
    def __init__(self, start_timestamp, end_timestamp, prom_con_obj):
        try:
            self.curr_ist_start_time = start_timestamp
            self.curr_ist_end_time = end_timestamp

            self.test_env_file_path = prom_con_obj.test_env_file_path
            self.PROMETHEUS = prom_con_obj.prometheus_path
            self.API_PATH = prom_con_obj.prom_point_api_path
            self.port = prom_con_obj.ssh_port
            self.username = prom_con_obj.abacus_username
            self.password = prom_con_obj.abacus_password
            with open(self.test_env_file_path, 'r') as file:
                self.stack_details = json.load(file)

            self.contents = ["ruleengine", "tls", "nginx", "metastoredb", "pgbouncer", "osqueryIngestion", "redis",
                             "spark", "data-archival", "compaction", "hdfsWrapper", "loginserver", "maintenance",
                             "postgresql", "cloudqueryConsumer", "ruleenginecc", "cloudcompliancemanager",
                             "cloudGraphSynchronizer", "dbsyncscheduler"]

            self.elasticsearch_host = f"http://{self.stack_details['elastic']}:9200"
            self.elastic_client = Elasticsearch(hosts=[self.elasticsearch_host], timeout=240)

            dt_object = datetime.utcfromtimestamp(start_timestamp)
            self.formatted_starttime = dt_object.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            dt_object = datetime.utcfromtimestamp(end_timestamp)
            self.formatted_endtime = dt_object.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

            self.index_name = "uptycs-*"
        except Exception as e:
            print(f"An error occurred during initialization: {e}")

    def body(self, log_type):
        try:
            body_error = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"log_type.keyword": {"query": log_type}}},
                            {"match": {"message": {"query": "error"}}},
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
        except Exception as e:
            print(f"An ERROR occurred while constructing the body: {e}")
            return []

    def elk_batch(self, log_type):
        try:
            body_array = self.body(log_type)
            print(f"Fetching elk errors for log_type: {log_type}...")
            result_error = self.elastic_client.search(index=self.index_name, body=body_array[0], size=0)
            error_buckets = result_error["aggregations"]["categories"]["buckets"]
            print(f"Completed fetching errors for log_type: {log_type}")
            return log_type, error_buckets
        except Exception as e:
            print(f"An ERROR occurred during fetching elk errors for log_type {log_type}: {e}")
            return log_type, []

    def fetch_errors(self):
        try:
            result_dict = {}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.elk_batch, log_type) for log_type in self.contents]

                for future in concurrent.futures.as_completed(futures):
                    try:
                        log_type, items = future.result()
                        save_dict = []
                        for item in items:
                            error_message = item.get('key', 'Unknown Error')
                            count = item.get('doc_count', 0)
                            save_dict.append({"Error Message": error_message, "Count": count})
                        result_dict[log_type] = save_dict
                    except Exception as e:
                        print(f"An error occurred while processing result for log_type {log_type}: {e}")

            print(result_dict)
            return result_dict
        except Exception as e:
            print(f"An error occurred during fetch_errors: {e}")
            return {}


