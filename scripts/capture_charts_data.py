import requests
import copy
import json

common_app_names={
            "sum":["orc-compaction" ,"uptycs-configdb",  ".*osqLogger.*", "kafka","spark-worker",".*ruleEngine.*",
                "data-archival",".*redis-server.*","/opt/uptycs/cloud/go/bin/complianceSummaryConsumer","tls",".*airflow.*",
                "eventsDbIngestion"  , "trino" , "osqueryIngestion"],
            "avg":[]
        }

memory_app_names=copy.deepcopy(common_app_names)
cpu_app_names=copy.deepcopy(common_app_names)
cpu_app_names['avg'].extend([])
cpu_app_names['sum'].extend(["pgbouncer","spark-master","/usr/local/bin/pushgateway"])

live_asset_count_query = {"live assets count":"sum(uptycs_live_count)"}

node_level_RAM_used_percentage_queries = dict([(f"{node} Node RAM used percentage",f"((uptycs_memory_used{{node_type='{node}'}}/uptycs_total_memory{{node_type='{node}'}})*100)") for node in ['process','data','pg']])
app_level_RAM_used_percentage_queries= dict([(f"Memory Used by {app}",f"{key}(uptycs_app_memory{{app_name=~'{app}'}}) by (host_name)") for key,app_list in memory_app_names.items() for app in app_list])
more_memory_queries={
    "Kafka Disk Used Percentage":"uptycs_percentage_used{partition=~'/data/kafka'}",
    "Debezium memory usage":"uptycs_docker_mem_used{container_name='debezium'}",
}

memory_chart_queries={}
memory_chart_queries.update(node_level_RAM_used_percentage_queries)
memory_chart_queries.update(app_level_RAM_used_percentage_queries)
memory_chart_queries.update(more_memory_queries)

node_level_CPU_busy_percentage_queries=dict([(f"{node} Node CPU busy percentage",f"100-uptycs_idle_cpu{{node_type='{node}'}}") for node in ['process','data','pg']])
app_level_CPU_used_cores_queries=dict([(f"CPU used by {app}",f"{key}(uptycs_app_cpu{{app_name=~'{app}'}}) by (host_name)") for key,app_list in cpu_app_names.items() for app in app_list])
more_cpu_queries={
    "Debezium cpu usage":"uptycs_docker_cpu_stats{container_name='debezium'}",
}

cpu_chart_queries={}
cpu_chart_queries.update(node_level_CPU_busy_percentage_queries)
cpu_chart_queries.update(app_level_CPU_used_cores_queries)
cpu_chart_queries.update(more_cpu_queries)

inject_drain_rate_and_lag_chart_queries={
    "Spark Inject Rate for agent Osquery":"uptycs_mon_spark_inject_rate{topic='agentosquery'}",
    "Spark Drain Rate for agent Osquery":"uptycs_mon_spark_drain_rate{topic='agentosquery'}",
    "Spark Lag for Agent Osquery":"uptycs_mon_spark_lag{topic='agentosquery'}",

    "Spark Inject Rate for Events":"uptycs_mon_spark_inject_rate{topic='event'}",
    "Spark Drain Rate for Events":"uptycs_mon_spark_drain_rate{topic='event'}",
    "Spark lag for events":"uptycs_mon_spark_lag{topic='event'}",

    "Inject Rate for Db-Alerts group":"uptycs_kafka_group_inject_rate{group='db-alerts'}",
    "Drain Rate for Db-Alerts group":"uptycs_kafka_group_drain_rate{group='db-alerts'}",
    "kafka lag for Db-alerts group":"uptycs_kafka_group_lag{group='db-alerts'}",

    "Inject rate for ruleengine group":"uptycs_kafka_group_inject_rate{group='ruleengine'}",
    "Drain rate for ruleengine group":"uptycs_kafka_group_drain_rate{group='ruleengine'}",
    "Kafka lag for ruleengine group":"uptycs_kafka_group_lag{group='ruleengine'}",

    "Kafka Inject rate for debezium group":"uptycs_kafka_group_inject_rate{group='debeziumconsumer'}",
    "Kafka Drain rate for debezium group":"uptycs_kafka_group_drain_rate{group='debeziumconsumer'}",
    "Debezium Aggregate Lag":"uptycs_kafka_group_lag{group='debeziumconsumer'}",
}

other_chart_queries={"Active Client Connections":"uptycs_pgb_cl_active","Average records in pg bouncer":"uptycs_pbouncer_stats{col=~'avg.*', col!~'.*time'}",
                     "Average time spent by pg bouncer":"uptycs_pbouncer_stats{col=~'avg.*time'}",
                     "Redis client connections for tls":"sum(uptycs_app_redis_clients{app_name='/opt/uptycs/cloud/tls/tls.js'}) by (host_name)",
                     "Configdb Pg wal folder size":"configdb_wal_folder","Configdb number of wal files":"configdb_wal_file{}",
                     "Top 10 redis client connections by app":"sort(topk(9,sum(uptycs_app_redis_clients{}) by (app_name)))",
                     "Configdb folder size":"configdb_size"
                     }

all_chart_queries={
    "live_asset_count":live_asset_count_query,
    "memory_charts":memory_chart_queries,
    "cpu_charts":cpu_chart_queries,
    "inject_drain_rate_and_lag_charts":inject_drain_rate_and_lag_chart_queries,
    "other_charts":other_chart_queries
}

class Charts:
    def __init__(self,prom_con_obj,start_timestamp,end_timestamp,add_extra_time_for_charts_at_end_in_min,fs):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp
        self.prom_con_obj=prom_con_obj
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path
        self.add_extra_time_for_charts_at_end_in_min=add_extra_time_for_charts_at_end_in_min
        self.add_extra_time_for_charts_at_start_in_min=10
        self.fs=fs

    def extract_charts_data(self,queries):
        final=dict()
        file_ids=[]
        ste = self.curr_ist_start_time - (self.add_extra_time_for_charts_at_start_in_min * (60))
        ete = self.curr_ist_end_time + (self.add_extra_time_for_charts_at_end_in_min * (60))

        for query in queries:
            PARAMS = {
                'query': queries[query],
                'start': ste,
                'end': ete,
                'step':15
            }
            response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
            print(f"processing {query} chart data (timestamp : {ste} to {ete}), Status code : {response.status_code}")
            if response.status_code != 200:print("ERROR : Request failed")
            result = response.json()['data']['result']
            for host in result:
                file_id = self.fs.put(str(host["values"]).encode('utf-8'), filename='array.json')
                host["values"] = file_id
                file_ids.append(file_id)
            final[query] = result
        return final,file_ids
            
    def capture_charts_and_save(self): 
        print("All chart queries to be executed are:")
        print(json.dumps(all_chart_queries, indent=4))

        all_gridfs_fileids = []
        final_dict={}
        for key,value in all_chart_queries.items():
            print(f"-----------Processing {key} queries-----------")
            final_dict[key],file_ids = self.extract_charts_data(value)
            all_gridfs_fileids.extend(file_ids)
        return final_dict,all_gridfs_fileids