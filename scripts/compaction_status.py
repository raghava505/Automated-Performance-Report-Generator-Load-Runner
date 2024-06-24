from elasticsearch import Elasticsearch
import datetime
from datetime import datetime


class CompactionStatus:
    def __init__(self,stack_obj,elastic_ip):
        self.stack_obj = stack_obj
        try:            
            self.elasticsearch_host = f"http://{elastic_ip}:9200"
            self.elastic_client = Elasticsearch(hosts=[self.elasticsearch_host], timeout=240)

            dt_object = datetime.utcfromtimestamp(stack_obj.start_timestamp)
            self.formatted_starttime = dt_object.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            dt_object = datetime.utcfromtimestamp(stack_obj.end_timestamp)
            self.formatted_endtime = dt_object.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

            self.index_name = "uptycs-*"
        except Exception as e:
             self.stack_obj.log.error(f"An error occurred during initialization: {e}")

    def build_query(self):
        try:
            query_body = {
                "aggs": {
                    "0": {
                    "date_histogram": {
                        "field": "event.tags.upt_day.date_value",
                        "calendar_interval": "1d",
                        "time_zone": "Asia/Calcutta",
                    },
                    "aggs": {
                        "Files Ingested": {
                        "sum": {
                            "field": "event.metrics.files_per_batch.int_value"
                        }
                        },
                        "Files Compacted": {
                        "sum": {
                            "field": "event.metrics.uncompacted_file_count.int_value"
                        }
                        },
                        "Files Skipped": {
                        "sum": {
                            "field": "event.metrics.skip_compaction_file_cnt.int_value"
                        }
                        },
                        "Files Ready for Archival": {
                        "sum": {
                            "field": "event.metrics.l1_compacted_file_count.int_value"
                        }
                        },
                        "Files Archived": {
                        "sum": {
                            "field": "event.metrics.total_archived_count.int_value"
                        }
                        }
                    }
                    }
                },
                "size": 0,
                "fields": [
                    {
                    "field": "@timestamp",
                    "format": "date_time"
                    },
                    {
                    "field": "event.tags.upt_day.date_value",
                    "format": "date_time"
                    },
                    {
                    "field": "event.timestamp",
                    "format": "date_time"
                    }
                ],
                "query": {
                    "bool": {
                    "filter": [
                        {
                        "range": {
                            "event.tags.upt_day.date_value": {
                            "format": "strict_date_optional_time",
                            "gte": self.formatted_starttime,
                            "lte": self.formatted_endtime
                            }
                        }
                        }
                    ],
                    }
                }
                }

            return query_body
        except Exception as e:
             self.stack_obj.log.error(f"An error occurred while constructing the query: {e}")

    def execute_query(self):
        try:
            query = self.build_query()
            result = self.elastic_client.search(index=self.index_name, body=query)
            aggregations = result.get('aggregations', {})
            result_dict = {}

            for bucket in aggregations.get('0', {}).get('buckets', []):
               
                date_string = bucket.get('key_as_string', '')
                date_part = date_string.split('T')[0]
                files_archived = bucket.get('Files Archived', {}).get('value', 0)
                files_skipped = bucket.get('Files Skipped', {}).get('value', 0)
                files_ingested = bucket.get('Files Ingested', {}).get('value', 0)
                files_ready_for_archival = bucket.get('Files Ready for Archival', {}).get('value', 0)
                files_compacted = bucket.get('Files Compacted', {}).get('value', 0)

                self.stack_obj.log.info(f"Compaction Status for the Date: {date_part}")
                self.stack_obj.log.info(f"Files Archived: {files_archived}")
                self.stack_obj.log.info(f"Files Skipped: {files_skipped}")
                self.stack_obj.log.info(f"Files Ingested: {files_ingested}")
                self.stack_obj.log.info(f"Files Ready for Archival: {files_ready_for_archival}")
                self.stack_obj.log.info(f"Files Compacted: {files_compacted}")
                print()

                result_dict[date_part]["Files Archived"] = files_archived
                result_dict[date_part]["Files Skipped"] = files_skipped
                result_dict[date_part]["Files Ingested"] = files_ingested
                result_dict[date_part]["Files Ready for Archival"] = files_ready_for_archival
                result_dict[date_part]["Files Compacted"] = files_compacted

                return result_dict
        except Exception as e:
            self.stack_obj.log.error(f"An error occurred while executing the query: {e}")

# # Example usage:
# if __name__ == "__main__":
#     obj = CompactionStatus()
#     result = obj.execute_query()

