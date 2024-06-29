from elasticsearch import Elasticsearch
import datetime
from datetime import datetime
import concurrent.futures
from config_vars import ELASTICSEARCH_PORT
import pandas as pd

class elk_errors_class:
    def __init__(self,stack_obj,elastic_ip):
        self.stack_obj = stack_obj
        try:
            self.contents = ["ruleengine", "tls", "nginx", "metastoredb", "pgbouncer", "osqueryIngestion", "redis",
                             "spark", "data-archival", "compaction", "hdfsWrapper", "loginserver", "maintenance",
                             "postgresql", "cloudqueryConsumer", "ruleenginecc", "cloudcompliancemanager",
                             "cloudGraphSynchronizer", "dbsyncscheduler"]

            self.elasticsearch_host = f"http://{elastic_ip}:{ELASTICSEARCH_PORT}"
            self.elastic_client = Elasticsearch(hosts=[self.elasticsearch_host], timeout=240)

            dt_object = datetime.utcfromtimestamp(stack_obj.start_timestamp)
            self.formatted_starttime = dt_object.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            dt_object = datetime.utcfromtimestamp(stack_obj.end_timestamp)
            self.formatted_endtime = dt_object.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

            self.index_name = "uptycs-*"
        except Exception as e:
            self.stack_obj.log.error(f"An error occurred during initialization: {e}")

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
            self.stack_obj.log.error(f"An ERROR occurred while constructing the body: {e}")
            return []

    def elk_batch(self, log_type):
        try:
            body_array = self.body(log_type)
            self.stack_obj.log.info(f"Fetching elk errors for log_type: {log_type}...")
            result_error = self.elastic_client.search(index=self.index_name, body=body_array[0], size=0)
            error_buckets = result_error["aggregations"]["categories"]["buckets"]
            self.stack_obj.log.info(f"Completed fetching errors for log_type: {log_type}")
            return log_type, error_buckets
        except Exception as e:
            self.stack_obj.log.error(f"An ERROR occurred during fetching elk errors for log_type {log_type}: {e}")
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
                        df = pd.DataFrame(save_dict)
                        self.stack_obj.log.info(df)
                        return_dict ={
                                "schema":{
                                    "merge_on_cols" : ["Error Message"],
                                    "compare_cols":["Count"]
                                },
                                "table":df.to_dict(orient="records")
                            }
                        result_dict[log_type] = return_dict
                    except Exception as e:
                        self.stack_obj.log.error(f"An error occurred while processing result for log_type {log_type}: {e}")

            self.stack_obj.log.info(result_dict)
            return result_dict
        except Exception as e:
            self.stack_obj.log.error(f"An error occurred during fetch_errors: {e}")
            return {}


