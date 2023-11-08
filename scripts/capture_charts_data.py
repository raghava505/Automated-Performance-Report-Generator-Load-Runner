import requests
import copy
import json

# common_app_names={
#             "sum":["orc-compaction" ,"uptycs-configdb",  ".*osqLogger.*", "kafka","spark-worker",".*ruleEngine.*",
#                 "data-archival",".*redis-server.*","/opt/uptycs/cloud/go/bin/complianceSummaryConsumer","tls",".*airflow.*",
#                  "trino" , "osqueryIngestion"],
#             "avg":[]
#         }

# memory_app_names=copy.deepcopy(common_app_names)
# cpu_app_names=copy.deepcopy(common_app_names)
# cpu_app_names['avg'].extend([])
# cpu_app_names['sum'].extend(["pgbouncer","spark-master","/usr/local/bin/pushgateway"])

# basic_chart_queries = {"Live Assets Count":("sum(uptycs_live_count)" , []),
#                        "Kafka group Lag for all groups(Osquery) ": ("uptycs_kafka_group_lag{group!~\".*cloud.*|.*kube.*\"}" , ["group","cluster_id"]),
#                        "Mon Spark Lag for all groups(Osquery)":("uptycs_mon_spark_lag{topic!~\".*cloud.*|.*kube.*\"}" , ["topic","cluster_id"])
#                        }

# node_level_RAM_used_percentage_queries = dict([(f"{node} node RAM used percentage",(f"((uptycs_memory_used{{node_type='{node}'}}/uptycs_total_memory{{node_type='{node}'}})*100)" , ["host_name"]) ) for node in ['process','data','pg']])
# app_level_RAM_used_percentage_queries= dict([(f"Memory Used by {app}",(f"{key}(uptycs_app_memory{{app_name=~'{app}'}}) by (host_name)" , ["host_name"]) ) for key,app_list in memory_app_names.items() for app in app_list])
# more_memory_queries={
#     "Kafka Disk Used Percentage":("uptycs_percentage_used{partition=~'/data/kafka'}" , ["host_name"]),
#     "Debezium memory usage":("uptycs_docker_mem_used{container_name='debezium'}" , ["host_name"]),
# }

# # memory_chart_queries={}
# # memory_chart_queries.update(node_level_RAM_used_percentage_queries)
# # memory_chart_queries.update(app_level_RAM_used_percentage_queries)
# # memory_chart_queries.update(more_memory_queries)

# app_level_RAM_used_percentage_queries.update(more_memory_queries)

# node_level_CPU_busy_percentage_queries=dict([(f"{node} node CPU busy percentage",(f"100-uptycs_idle_cpu{{node_type='{node}'}}",["host_name"]) ) for node in ['process','data','pg']])
# app_level_CPU_used_cores_queries=dict([(f"CPU Used by {app}", (f"{key}(uptycs_app_cpu{{app_name=~'{app}'}}) by (host_name)" , ["host_name"]) ) for key,app_list in cpu_app_names.items() for app in app_list])
# more_cpu_queries={
#     "Debezium CPU usage":("uptycs_docker_cpu_stats{container_name='debezium'}" , ["host_name"]),
# }

# # cpu_chart_queries={}
# # cpu_chart_queries.update(node_level_CPU_busy_percentage_queries)
# # cpu_chart_queries.update(app_level_CPU_used_cores_queries)
# # cpu_chart_queries.update(more_cpu_queries)

# app_level_CPU_used_cores_queries.update(more_cpu_queries)

# inject_drain_rate_and_lag_chart_queries={
#     "Spark Inject Rate for agent Osquery":("uptycs_mon_spark_inject_rate{topic='agentosquery'}",["__name__","cluster_id","topic"]),
#     "Spark Drain Rate for agent Osquery":("uptycs_mon_spark_drain_rate{topic='agentosquery'}" , ["__name__","cluster_id","topic"]),
#     "Spark Lag for Agent Osquery":("uptycs_mon_spark_lag{topic='agentosquery'}",["__name__","cluster_id","topic"]),

#     "Spark Inject Rate for Events":("uptycs_mon_spark_inject_rate{topic='event'}",["__name__","cluster_id","topic"]),
#     "Spark Drain Rate for Events":("uptycs_mon_spark_drain_rate{topic='event'}",["__name__","cluster_id","topic"]),
#     "Spark lag for events":("uptycs_mon_spark_lag{topic='event'}",["__name__","cluster_id","topic"]),

#     "Inject Rate for Db-Alerts group":("uptycs_kafka_group_inject_rate{group='db-alerts'}",["__name__","cluster_id","group"]),
#     "Drain Rate for Db-Alerts group":("uptycs_kafka_group_drain_rate{group='db-alerts'}",["__name__","cluster_id","group"]),
#     "kafka lag for Db-alerts group":("uptycs_kafka_group_lag{group='db-alerts'}",["__name__","cluster_id","group"]),

#     "Inject rate for ruleengine group":("uptycs_kafka_group_inject_rate{group='ruleengine'}",["__name__","cluster_id","group"]),
#     "Drain rate for ruleengine group":("uptycs_kafka_group_drain_rate{group='ruleengine'}",["__name__","cluster_id","group"]),
#     "Kafka lag for ruleengine group":("uptycs_kafka_group_lag{group='ruleengine'}",["__name__","cluster_id","group"]),

#     "Kafka Inject rate for debezium group":("uptycs_kafka_group_inject_rate{group='debeziumconsumer'}" , ["__name__","cluster_id","group"]),
#     "Kafka Drain rate for debezium group":("uptycs_kafka_group_drain_rate{group='debeziumconsumer'}",["__name__","cluster_id","group"]),
#     "Debezium Aggregate Lag":("uptycs_kafka_group_lag{group='debeziumconsumer'}",["__name__","cluster_id","group"]),
# }

# other_chart_queries={"Active Client Connections":("uptycs_pgb_cl_active" , ["host_name","db","db_user"]),
#                      "Redis client connections for tls":("sum(uptycs_app_redis_clients{app_name='/opt/uptycs/cloud/tls/tls.js'}) by (host_name)" , ["host_name"]),
#                      "Configdb Pg wal folder size":("configdb_wal_folder",["host_name"]),
#                      "Configdb number of wal files":("configdb_wal_file{}" , ["host_name"]),
#                      "Top 10 redis client connections by app":("sort(topk(9,sum(uptycs_app_redis_clients{}) by (app_name)))" , ["app_name"]),
#                      "Configdb folder size":("configdb_size" , ["host_name"]),
#                      "Average records in pg bouncer":("uptycs_pbouncer_stats{col=~'avg.*', col!~'.*time'}" , ["col"]),
#                      "Average time spent by pg bouncer":("uptycs_pbouncer_stats{col=~'avg.*time'}" , ["col"]),
#                      "iowait time":("uptycs_iowait{}" , ["host_name"]),
#                      "iowait util%":("uptycs_iowait_util_percent{}" , ["host_name" , "device"]),
#                      "Waiting Client Connections":("uptycs_pgb_cl_waiting", ["db" , "db_user"]),
#                      "Disk read wait time":("uptycs_r_await{}" , ["host_name" , "device"]),
#                      "Disk write wait time":("uptycs_w_await{}", ["host_name" , "device"]),
#                      "Idle server connections":("uptycs_pgb_sv_idle", ["db" , "db_user"]),
#                      "Active Server Connections":("uptycs_pgb_sv_active", ["db" , "db_user"]),
#                      "Disk blocks in configdb":("uptycs_configdb_stats{col =~ \"blks.*\"}",["col"]),
#                      "Transaction count in configdb":("uptycs_configdb_stats{col =~ \"xact.*\"}",["col"]),
#                      "Row count in configdb":("uptycs_configdb_stats{col =~ \"tup.*\"}",["col"]),
#                      "Assets table stats":("uptycs_psql_table_stats",["col"]),
#                      "PG and data partition disk usage in configdb" : ("uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/data\"} or uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/pg\"}" , ["partition","host_name"])
#                      }

# all_chart_queries={
#     "Live Assets and Lag for all groups":basic_chart_queries,
#     "Node-level Memory Charts":node_level_RAM_used_percentage_queries,
#     "Node-level CPU Charts":node_level_CPU_busy_percentage_queries,
#     "Application-level Memory Charts":app_level_RAM_used_percentage_queries,
#     "Application-level CPU Charts":app_level_CPU_used_cores_queries,
#     # "memory_charts":memory_chart_queries,
#     # "cpu_charts":cpu_chart_queries,
#     "Inject-Drain rate and Lag Charts":inject_drain_rate_and_lag_chart_queries,
#     "Other Charts":other_chart_queries
# }

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
            try:
                PARAMS = {
                    'query': queries[query][0],
                    'start': ste,
                    'end': ete,
                    'step':60
                }
                legend_list = queries[query][1]
                try:unit = queries[query][2]
                except:unit=""
                response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
                print(f"processing {query} chart data (timestamp : {ste} to {ete}), Status code : {response.status_code}")
                if response.status_code != 200:print("ERROR : Request failed")
                else:
                    result = response.json()['data']['result']
                    for host in result:
                        file_id = self.fs.put(str(host["values"]).encode('utf-8'), filename=f'{query}.json')
                        host["values"] = file_id
                        file_ids.append(file_id)
                        try:
                            legend_text=str(host['metric'][legend_list[0]])
                        except:
                            print("error: list index out of range error while trying to access 1st element of the legend list")
                            legend_text=""
                        for key in legend_list[1:]:
                            try:
                                legend_text += f"-{host['metric'][key]}"
                            except:
                                print(f"Warning : Key '{key}' not present in {host['metric']}. please check the provided legend attribute")
                        host["legend"]=legend_text
                        host["unit"]=unit
                    final[query] = result
            except Exception as e:
                print(f"Error occured while processing data for '{query}' , {str(e)}")
        return final,file_ids
            
    def capture_charts_and_save(self,all_chart_queries): 
        print("All chart queries to be executed are:")
        print(json.dumps(all_chart_queries, indent=4))

        all_gridfs_fileids = []
        final_dict={}
        for key,value in all_chart_queries.items():
            print(f"-----------Processing {key} queries-----------")
            final_dict[key],file_ids = self.extract_charts_data(value)
            all_gridfs_fileids.extend(file_ids)
        return final_dict,all_gridfs_fileids