import copy
from collections import defaultdict
from time_taken_by_all_queries import get_full_query,time_ranges

class parent:
    @classmethod
    @property
    def common_app_names(cls):
        return  {"sum":["orc-compaction" ,"uptycs-configdb",  ".*osqLogger.*", "kafka","spark-worker",".*ruleEngine.*",
                        "data-archival",".*redis-server.*","/opt/uptycs/cloud/go/bin/complianceSummaryConsumer","tls",
                        ".*airflow.*","trino","pgbouncer","spark-master","/usr/local/bin/pushgateway" ,"osqueryIngestion",
                        "uptycs-metastoredb","apiserver"],
                "avg":[]
                }
    
    @classmethod
    @property
    def common_container_names(cls):
        return ["debezium"]
    
    @classmethod
    @property
    def common_pod_names(cls):
        return ["configdb-deployment.*","deadletter-consumer-deployment.*","debezium-consumer-deployment.*","compliance-check-runner-deployment.*","compliance-summary-consumer-deployment.*","latest-snapshot-consumer-deployment.*","decorators-consumer-deployment.*","checksum-validator-deployment.*","apiscraper-consumer-deployment.*"]

    @classmethod
    @property
    def hostname_types(cls):
        return ["process","data","pg","airflow","redis"]
    
    @classmethod
    @property
    def mon_spark_topic_names(cls):
        return ['event','audit','prestoquerylogs']
    
    @classmethod
    @property
    def kafka_group_names(cls):
        return ['db-alerts','ruleengine','debeziumconsumer','db-incidents','apiScraperSecPosConsumerGroup','decorators']
    
    @classmethod
    @property
    def list_of_observations_to_make(cls):
        return [
                    'Check for Ingestion lag',
                    'Check for Rule engine Lag',
                    'Check for db-events Lag',
                    'Data loss check for raw tables like processes, process_env etc (accuracy)',
                    'Data loss check for processed data like events, alerts and incidents etc (accuracy)',
                    "Check if CPU/memory utilisation in line with previous sprints. If not, are the differences expected?",
                    'Check for variations in the Count of queries executed on presto',
                    'Triage bugs and check for blockers',
                    'Check if PG master is in sync with replica',
                    'Check for memory leaks',
                    'Check for variation in HDFS disk usage',
                    'Check for variation in PG disk usage',
                    'Check for variation in Kafka disk usage',
                    'Check for new kafka topics',
                    'Check for steady state of live assets count'
                ]
    

    @staticmethod
    def get_basic_chart_queries():
        return {"Live Assets Count":("sum(uptycs_live_count)" , []),
                "Kafka Lag for all groups":("uptycs_kafka_group_lag{group!~'db-events|cloudconnectorsgroup'} or uptycs_mon_spark_lag{ topic='event'} or uptycs_mon_spark_lag{topic!~'event|cloudconnectorsink|agentosquery'}",['cluster_id','topic','group']),
                }
    
    @classmethod
    def get_node_level_RAM_used_percentage_queries(cls):
        return dict([(f"{node} node RAM used percentage",(f"((uptycs_memory_used{{node_type='{node}'}}/uptycs_total_memory{{node_type='{node}'}})*100)" , ["host_name"] , '%') ) for node in cls.hostname_types])
    
    @classmethod
    def get_app_level_RAM_used_percentage_queries(cls):
        app_level_RAM_used_percentage_queries= dict([(f"Memory Used by {app}",(f"{key}(uptycs_app_memory{{app_name=~'{app}'}}) by (host_name)" , ["host_name"], '%') ) for key,app_list in cls.common_app_names.items() for app in app_list])
        more_memory_queries={
            "Kafka Disk Used Percentage":("uptycs_percentage_used{partition=~'/data/kafka'}" , ["host_name"], '%'),
        }
        app_level_RAM_used_percentage_queries.update(more_memory_queries)
        return app_level_RAM_used_percentage_queries
    
    @classmethod
    def get_docker_level_mem_used_queries(cls):
        return dict([(f"Memory used by container {cont}",(f"sum(uptycs_docker_mem_used{{container_name=~'{cont}'}}/(1024*1024*1024)) by (host_name)" , ["host_name"], 'GB') ) for cont in cls.common_container_names])

    @classmethod
    def get_pod_level_mem_used_queries(cls):
        return dict([(f"Memory used by pod {pod}",(f"sum(container_memory_working_set_bytes{{container_label_io_kubernetes_pod_name=~'{pod}'}}/(1024*1024*1024)) by (node_name)" , ["node_name"], 'GB') ) for pod in cls.common_pod_names])


    @classmethod
    def get_node_level_CPU_busy_percentage_queries(cls):
        return dict([(f"{node} node CPU busy percentage",(f"100-uptycs_idle_cpu{{node_type='{node}'}}",["host_name"], '%') ) for node in cls.hostname_types])
    
    @classmethod
    def get_app_level_CPU_used_cores_queries(cls):
        return dict([(f"CPU Used by {app}", (f"{key}(uptycs_app_cpu{{app_name=~'{app}'}}) by (host_name)" , ["host_name"], '%') ) for key,app_list in cls.common_app_names.items() for app in app_list])

    @classmethod
    def get_docker_level_cpu_used_queries(cls):
        return dict([(f"CPU used by container {cont}",(f"sum(uptycs_docker_cpu_stats{{container_name=~'{cont}'}}/100) by (host_name)" , ["host_name"], 'cores') ) for cont in cls.common_container_names])

    @classmethod
    def get_pod_level_cpu_used_queries(cls):
        return dict([(f"CPU used by pod {pod}",(f"sum(rate(container_cpu_usage_seconds_total{{container_label_io_kubernetes_pod_name=~'{pod}'}}[10m])) by (node_name)" , ["node_name"] , 'cores') ) for pod in cls.common_pod_names])


    @staticmethod
    def get_inject_drain_and_lag_uptycs_mon_spark(topic):
        return {
            f"Spark Inject Rate for {topic} topic":(f"uptycs_mon_spark_inject_rate{{topic='{topic}'}}",["__name__","cluster_id","topic"]),
            f"Spark Drain Rate for {topic} topic":(f"uptycs_mon_spark_drain_rate{{topic='{topic}'}}",["__name__","cluster_id","topic"]),
            f"Spark lag for {topic} topic":(f"uptycs_mon_spark_lag{{topic='{topic}'}}",["__name__","cluster_id","topic"]),
        }
    
    @staticmethod
    def get_inject_drain_and_lag_uptycs_kafka_group(group):
        return {
            f"Kafka Inject Rate for {group} group":(f"uptycs_kafka_group_inject_rate{{group='{group}'}}",["__name__","cluster_id","group"]),
            f"Kafka Drain Rate for {group} group":(f"uptycs_kafka_group_drain_rate{{group='{group}'}}",["__name__","cluster_id","group"]),
            f"Kafka lag for {group} group":(f"uptycs_kafka_group_lag{{group='{group}'}}",["__name__","cluster_id","group"]),
        }
        
    @classmethod
    def get_inject_drain_rate_and_lag_chart_queries(cls):
        queries={}
        queries['Debezium Replication Lag']=('sum(uptycs_pg_logical_replication_lag{slot_name=~".*debezium.*"}) by (database,lag_type,slot_name,slot_type)' , ['slot_name','lag_type'] , 'bytes' )
        for topic in cls.mon_spark_topic_names:
            queries.update(cls.get_inject_drain_and_lag_uptycs_mon_spark(topic))
        for group in cls.kafka_group_names:
            queries.update(cls.get_inject_drain_and_lag_uptycs_kafka_group(group))
        return copy.deepcopy(queries)

    @staticmethod
    def get_connections_chart_queries():
        return {
            "No.of active connections group by application for configdb on master":("uptycs_pg_idle_active_connections_by_app{state=\"active\",db=\"configdb\",role=\"master\"}" , ["application_name"]),
            "Active Client Connections":("uptycs_pgb_cl_active" , ["host_name","db","db_user"]),
            "Waiting Client Connections":("uptycs_pgb_cl_waiting", ["db" , "db_user"]),
            "Uptycs pg Connections by app":("sum(uptycs_pg_connections_by_app)" , []),
            "Uptycs redis Connections":("sum(uptycs_redis_connection)" , []),
            "Redis client connections for tls":("sum(uptycs_app_redis_clients{app_name='/opt/uptycs/cloud/tls/tls.js'}) by (host_name)" , ["host_name"]),
            "Top 10 redis client connections by app":("sort(topk(9,sum(uptycs_app_redis_clients{}) by (app_name)))" , ["app_name"]),
            "Active Server Connections":("uptycs_pgb_sv_active", ["db" , "db_user"]),
            "Idle server connections":("uptycs_pgb_sv_idle", ["db" , "db_user"]),
        }

    @staticmethod
    def get_other_chart_queries():
        return {
            "Configdb Pg wal folder size":("configdb_wal_folder",["host_name"]),
            "Configdb number of wal files":("configdb_wal_file{}" , ["host_name"]),
            "Configdb folder size":("configdb_size" , ["host_name"]),
            "Average records in pg bouncer":("uptycs_pbouncer_stats{col=~'avg.*', col!~'.*time'}" , ["col"]),
            "Average time spent by pg bouncer":("uptycs_pbouncer_stats{col=~'avg.*time'}" , ["col"] , 'μs'),
            "iowait time":("uptycs_iowait{}" , ["host_name"]),
            "iowait util%":("uptycs_iowait_util_percent{}" , ["host_name" , "device"]),
            "Disk read wait time":("uptycs_r_await{}" , ["host_name" , "device"],'ms'),
            "Disk write wait time":("uptycs_w_await{}", ["host_name" , "device"],'ms'),
            "Disk blocks in configdb":("uptycs_configdb_stats{col =~ \"blks.*\"}",["col"]),
            "Transaction count in configdb":("uptycs_configdb_stats{col =~ \"xact.*\"}",["col"]),
            "Row count in configdb":("uptycs_configdb_stats{col =~ \"tup.*\"}",["col"]),
            "Assets table stats":("uptycs_psql_table_stats",["col"]),
            "pg and data partition disk usage" : ("uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/data\"} or uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/pg\"}" , ["partition","host_name"],'bytes'),
            "configdb partition disk usage" : ("uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/data/pgdata/configdb\"}" , ["partition","host_name"],'bytes'),
            "statedb partition disk usage" :  ("uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/data/pgdata/statedb\"}" , ["partition","host_name"],'bytes'),
            "StateDB errors":("sum(curr_state_db_errors) by (error,table_name)" , ["error" , "table_name"])
        }
    
    @staticmethod
    def get_pg_charts():
        return {
            "Configb PG table size per table":('uptycs_pg_stats{db=~"configdb",stat="table_size_bytes"}',["table_name"]),
            "Configb PG index size per table":('uptycs_pg_stats{db=~"configdb",stat="index_size_bytes"}',["table_name"]),
            "Configb PG live tuples per table":('uptycs_pg_stats{db=~"configdb",stat="live_tuples"}',["table_name"]),
            "Configb PG connections by state":('sum(uptycs_pg_connections_by_state{db=~"configdb"}) by (state)',["state"]),
            "Configb PG connections by application":('sum(uptycs_pg_connections_by_app{db=~"configdb"}) by (application_name)',["application_name"]),
            "Statedb PG table size per table":('uptycs_pg_stats{db=~"statedb",stat="table_size_bytes"}',["table_name"]),
            "Statedb PG index size per table":('uptycs_pg_stats{db=~"statedb",stat="index_size_bytes"}',["table_name"]),
            "Statedb PG live tuples per table":('uptycs_pg_stats{db=~"statedb",stat="live_tuples"}',["table_name"]),
            "Statedb PG connections by state":('sum(uptycs_pg_connections_by_state{db=~"statedb"}) by (state)',["state"]),
            "Statedb PG connections by application":('sum(uptycs_pg_connections_by_app{db=~"statedb"}) by (application_name)',["application_name"]),
        }
    
    @staticmethod
    def get_restart_count_charts():
        return {
            "Uptycs containers restart count":('sum(uptycs_container_restart_count) by (container_name)' , ["container_name"]),
            }
    
    @classmethod
    def get_all_chart_queries(cls):
        return {
            "Live Assets and Kafka lag for all groups":cls.get_basic_chart_queries(),
            "Node-level Memory Charts":cls.get_node_level_RAM_used_percentage_queries(),
            "Node-level CPU Charts":cls.get_node_level_CPU_busy_percentage_queries(),
            "Application-level Memory Charts":cls.get_app_level_RAM_used_percentage_queries(),
            "Application-level CPU Charts":cls.get_app_level_CPU_used_cores_queries(),
            "Container-level Memory Charts":cls.get_docker_level_mem_used_queries(),
            "Container-level CPU Charts":cls.get_docker_level_cpu_used_queries(),
            "Pod-level Memory Charts":cls.get_pod_level_mem_used_queries(),
            "Pod-level CPU Charts":cls.get_pod_level_cpu_used_queries(),
            "Inject-Drain rate and Lag Charts":cls.get_inject_drain_rate_and_lag_chart_queries(),
            "Pg Stats Charts": cls.get_pg_charts(),
            "Restart count Charts": cls.get_restart_count_charts(),
            "Connection Charts": cls.get_connections_chart_queries(),
            "Other Charts":cls.get_other_chart_queries()
        }


    load_specific_details=defaultdict(lambda:{})

    @classmethod
    def get_load_specific_details(cls,load_name):
        return cls.load_specific_details[load_name]
    
    
    @classmethod
    def get_dictionary_of_observations(cls):
        observations_dict=dict([(observation,{"Status":"" , "Comments":""}) for observation in cls.list_of_observations_to_make])
        return observations_dict
    
    @classmethod
    @property
    def trino_details_commands(cls):
        limit=100
        return {
            "Total number of trino queries executed from each source" : {
                "query" :  "SELECT\
                                source,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(*) as total_count\
                            FROM presto_query_logs\
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            GROUP BY 1\
                            ORDER BY 1;",
                "columns":['source','success_count','failure_count','total_count'],
                "schema":{
                    "merge_on_cols" : ["source"],
                    "compare_cols":["total_count"]
                }
            },
            "Total number of trino queries executed from each source grouped by query_operation" : {
                "query" :  "SELECT\
                                source,\
                                COALESCE(query_operation,'NaN') AS query_operation,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(*) as total_count\
                            FROM presto_query_logs\
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            GROUP BY 1,2\
                            ORDER BY 1,2;",
                "columns":['source','query_operation','success_count','failure_count','total_count'],
                "schema":{
                    "merge_on_cols" : ["source","query_operation"],
                    "compare_cols":["total_count"]
                }
            },
            "Total number of failed queries grouped by failure message" : {
                "query" :  "select \
                                source,\
                                COALESCE(query_operation,'NaN') AS query_operation,\
                                failure_message,\
                                failure_type,\
                                count(*) as failure_count \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            and query_status='FAILURE' \
                            group by 1,2,3,4 \
                            order by 1,2;",
                "columns":['source','query_operation','failure_message','failure_type','failure_count'],
                "schema":{
                    "merge_on_cols" : ['source','query_operation','failure_message','failure_type'],
                    "compare_cols":["failure_count"]
                }
            },
            "Time taken by the queries on an hourly basis":{
                "query" :  "select \
                                'day-' || CAST(upt_day AS varchar) AS upt_day,\
                                'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                                count(*) as total_queries,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(CASE WHEN query_text LIKE '%like%' THEN 1 END) AS like_queries,\
                                COUNT(CASE WHEN query_text LIKE '%regex%' THEN 1 END) AS regex_queries,\
                                SUM(CAST(wall_time AS bigint)) AS total_wall_time,\
                                SUM(CAST(queued_time AS bigint)) AS total_queued_time,\
                                SUM(CAST(cpu_time AS bigint)) AS total_cpu_time,\
                                COALESCE(SUM(CAST(analysis_time AS bigint)),0) AS total_analysis_time\
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            GROUP BY 'day-' || CAST(upt_day AS varchar), 'batch-' || CAST(upt_batch AS varchar) \
                            ORDER BY upt_day, upt_batch;",
                "columns":['upt_day','upt_batch','total_queries','success_count','failure_count','like_queries','regex_queries','total_wall_time','total_queued_time','total_cpu_time','total_analysis_time'],
                "schema":{
                    "merge_on_cols" : ["upt_batch"],
                    "compare_cols":["total_wall_time"],
                }
            },
            "Time taken by queries by each source":{
                "query" :  "select \
                                source,\
                                count(*) as total_queries,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(CASE WHEN query_text LIKE '%like%' THEN 1 END) AS like_queries,\
                                COUNT(CASE WHEN query_text LIKE '%regex%' THEN 1 END) AS regex_queries,\
                                SUM(CAST(wall_time AS bigint)) AS total_wall_time,\
                                SUM(CAST(queued_time AS bigint)) AS total_queued_time,\
                                SUM(CAST(cpu_time AS bigint)) AS total_cpu_time,\
                                COALESCE(SUM(CAST(analysis_time AS bigint)),0) AS total_analysis_time\
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            group by 1 \
                            order by 7,8;",
                "columns":['source','total_queries','success_count','failure_count','like_queries','regex_queries','total_wall_time','total_queued_time','total_cpu_time','total_analysis_time'],
                "schema":{
                    "merge_on_cols" : ["source"],
                    "compare_cols":["total_wall_time"],
                }
            },
            "Time taken by queries executed from all sources on an hourly basis":{
                "query" :  "select \
                                source,\
                                'day-' || CAST(upt_day AS varchar) AS upt_day,\
                                'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                                count(*) as total_queries,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(CASE WHEN query_text LIKE '%like%' THEN 1 END) AS like_queries,\
                                COUNT(CASE WHEN query_text LIKE '%regex%' THEN 1 END) AS regex_queries,\
                                SUM(CAST(wall_time AS bigint)) AS total_wall_time,\
                                SUM(CAST(queued_time AS bigint)) AS total_queued_time,\
                                SUM(CAST(cpu_time AS bigint)) AS total_cpu_time,\
                                COALESCE(SUM(CAST(analysis_time AS bigint)),0) AS total_analysis_time\
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            GROUP BY source,'day-' || CAST(upt_day AS varchar), 'batch-' || CAST(upt_batch AS varchar) \
                            ORDER BY source,upt_day, upt_batch;",
                "columns":['source','upt_day','upt_batch','total_queries','success_count','failure_count','like_queries','regex_queries','total_wall_time','total_queued_time','total_cpu_time','total_analysis_time'],
                "schema":{
                    "merge_on_cols" : ["source","upt_batch"],
                    "compare_cols":["total_queries","total_wall_time",'total_queued_time','total_cpu_time','total_analysis_time'],
                }
            },
            # "client tag details of failed dags":{
            #     "query" :  "select \
            #                 source,\
            #                 count(*),client_tags,failure_message \
            #                 from presto_query_logs \
            #                 where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
            #                 and query_status='FAILURE' \
            #                 and client_tags like '%dagName%'\
            #                 group by 1,3,4 \
            #                 order by 2 desc;",
            #     "columns":['source','failed_count','client_tags','failure_message'],
            #     "schema":{
            #         "merge_on_cols" : [],
            #         "compare_cols":[],
            #         "do_not_compare":True
            #     }
            # },
            "Total time taken by each dag":{
                "query" :  """WITH dag_summary AS (\
                                    SELECT\
                                    COALESCE(\
                                        REGEXP_EXTRACT(client_tags, '\\"dagName\\": \\"([^,}]+)\\"', 1),\
                                        'Unknown'\
                                    ) AS dagName,\
                                    COUNT(*) AS total_count, sum(wall_time) as total_wall_time, sum(cpu_time) as total_cpu_time ,COALESCE(SUM(CAST(analysis_time AS bigint)),0) AS total_analysis_time, sum(queued_time) as total_queued_time\
                                    FROM presto_query_logs\
                                    WHERE client_tags IS NOT NULL and client_tags like '%dagName%' and \
                                    client_tags NOT LIKE '%SCHEDULED_GLOBAL_TAG_RULE%' \
                                    and upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                                    GROUP BY 1 
                                ),
                                scheduled_global_tag_rule_summary AS (\
                                    SELECT\
                                    'SCHEDULED_GLOBAL_TAG_RULE' AS dagName,\
                                    COUNT(*) AS total_count, sum(wall_time) as total_wall_time, sum(cpu_time) as total_cpu_time , sum(CAST(analysis_time as bigint)) as total_analysis_time, sum(queued_time) as total_queued_time\
                                    FROM presto_query_logs\
                                    WHERE client_tags IS NOT NULL and client_tags like '%dagName%' and \
                                    client_tags LIKE '%SCHEDULED_GLOBAL_TAG_RULE%'\
                                    and upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                                    GROUP BY 1 
                                )\
                                SELECT * FROM dag_summary\
                                UNION ALL\
                                SELECT * FROM scheduled_global_tag_rule_summary\
                                ORDER BY total_wall_time DESC;\
                            """,
                "columns":['dagName','total_count','total_wall_time','total_cpu_time','total_analysis_time','total_queued_time'],
                "schema":{
                    "merge_on_cols" : ["dagName"],
                    "compare_cols":["total_count","total_wall_time",'total_queued_time','total_cpu_time','total_analysis_time'],
                }
            },
            "Total time taken by each dag in each upt_batch":{
                "query" :  """WITH dag_summary AS (\
                                    SELECT
                                    COALESCE(
                                        REGEXP_EXTRACT(client_tags, '\\"dagName\\": \\"([^,}]+)\\"', 1),
                                        'Unknown'
                                    ) AS dagName,upt_day,upt_batch,
                                    COUNT(*) AS total_count, sum(wall_time) as total_wall_time, sum(cpu_time) as total_cpu_time , COALESCE(SUM(CAST(analysis_time AS bigint)),0) AS total_analysis_time, sum(queued_time) as total_queued_time
                                    FROM presto_query_logs
                                    WHERE client_tags IS NOT NULL and client_tags like '%dagName%' and
                                    client_tags NOT LIKE '%SCHEDULED_GLOBAL_TAG_RULE%' 
                                    and upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'
                                    GROUP BY 1,2,3
                                ),
                                scheduled_global_tag_rule_summary AS (\
                                    SELECT
                                    'SCHEDULED_GLOBAL_TAG_RULE' AS dagName,upt_day,upt_batch,
                                    COUNT(*) AS total_count, sum(wall_time) as total_wall_time, sum(cpu_time) as total_cpu_time , sum(CAST(analysis_time as bigint)) as total_analysis_time, sum(queued_time) as total_queued_time
                                    FROM presto_query_logs
                                    WHERE client_tags IS NOT NULL and client_tags like '%dagName%' and
                                    client_tags NOT LIKE '%SCHEDULED_GLOBAL_TAG_RULE%' 
                                    and upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'
                                    GROUP BY 1,2,3
                                )\
                                SELECT * FROM dag_summary\
                                UNION ALL\
                                SELECT * FROM scheduled_global_tag_rule_summary\
                                ORDER BY total_wall_time DESC;\
                            """,
                "columns":['dagName','upt_day','upt_batch','total_count','total_wall_time','total_cpu_time','total_analysis_time','total_queued_time'],
                "schema":{
                    "merge_on_cols" : ["dagName","upt_batch"],
                    "compare_cols":["total_count","total_wall_time",'total_queued_time','total_cpu_time','total_analysis_time'],
                }
            },

            # "Total time taken by each non-dag query":{
            #     "query" :  """SELECT
            #                 COALESCE(
            #                     source || '-' || REGEXP_EXTRACT(client_tags, '\\"queryType\\":\\"([^,}]+)\\"', 1),source || '-' || REGEXP_EXTRACT(client_tags, '\\"queryName\\":\\"([^,}]+)\\"', 1),source  ,
            #                     'Unknown'
            #                 ) AS query_type_or_name,
            #                 COUNT(*) AS total_count, sum(wall_time) as total_wall_time, sum(cpu_time) as total_cpu_time , sum(CAST(analysis_time as bigint)) as total_analysis_time, sum(queued_time) as total_queued_time
            #                 FROM presto_query_logs
            #                 WHERE client_tags IS NOT NULL and client_tags not like '%dagName%' and 
            #                 upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'
            #                 GROUP BY 1 order by 3 desc;""",
            #     "columns":['query_type_or_name','total_count','total_wall_time','total_cpu_time','total_analysis_time','total_queued_time'],
            #     "schema":{
            #         "merge_on_cols" : ["query_type_or_name"],
            #         "compare_cols":["total_count","total_wall_time",'total_queued_time','total_cpu_time','total_analysis_time'],
            #     }
            # },

            #delete this table after 2 sprints
            # "Time taken by etl-jobs queries on an hourly basis":{
            #     "query" :  "select \
            #                     'day-' || CAST(upt_day AS varchar) AS upt_day,\
            #                     'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
            #                     count(*) as total_queries,\
            #                     COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
            #                     COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
            #                     COUNT(CASE WHEN query_text LIKE '%like%' THEN 1 END) AS like_queries,\
            #                     COUNT(CASE WHEN query_text LIKE '%regex%' THEN 1 END) AS regex_queries,\
            #                     SUM(CAST(wall_time AS bigint)) AS total_wall_time,\
            #                     SUM(CAST(queued_time AS bigint)) AS total_queued_time,\
            #                     SUM(CAST(cpu_time AS bigint)) AS total_cpu_time,\
            #                     SUM(CAST(analysis_time AS bigint)) AS total_analysis_time\
            #                 from presto_query_logs \
            #                 where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
            #                 and source='etl-jobs'\
            #                 GROUP BY 'day-' || CAST(upt_day AS varchar), 'batch-' || CAST(upt_batch AS varchar) \
            #                 ORDER BY upt_day, upt_batch;",
            #     "columns":['upt_day','upt_batch','total_queries','success_count','failure_count','like_queries','regex_queries','total_wall_time','total_queued_time','total_cpu_time','total_analysis_time'],
            #     "schema":{
            #         "merge_on_cols" : ["upt_batch"],
            #         "compare_cols":["total_wall_time"],
            #     }
            # },
            #delete this table after 2 sprints
            # "Total time taken by each non-dag query in each upt_batch":{
            #     "query" :  """SELECT
            #                 COALESCE(
            #                     source || '-' || REGEXP_EXTRACT(client_tags, '\\"queryType\\":\\"([^,}]+)\\"', 1),source || '-' || REGEXP_EXTRACT(client_tags, '\\"queryName\\":\\"([^,}]+)\\"', 1),source  ,
            #                     'Unknown'
            #                 ) AS query_type_or_name,upt_day,upt_batch,
            #                 COUNT(*) AS total_count, sum(wall_time) as total_wall_time, sum(cpu_time) as total_cpu_time , sum(CAST(analysis_time as bigint)) as total_analysis_time, sum(queued_time) as total_queued_time
            #                 FROM presto_query_logs
            #                 WHERE client_tags IS NOT NULL and client_tags not like '%dagName%' and 
            #                 upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'
            #                 GROUP BY 1,2,3 order by 5 desc;""",
            #     "columns":['query_type_or_name','upt_day','upt_batch','total_count','total_wall_time','total_cpu_time','total_analysis_time','total_queued_time'],
            #     "schema":{
            #         "merge_on_cols" : ["query_type_or_name","upt_batch"],
            #         "compare_cols":["total_wall_time"],
            #     }
            # },
            
            f"Top {limit} slowest queries sorted by analysis time":{
                "query" :  f"select \
                            source,\
                            client_tags,\
                            'day-' || CAST(upt_day AS varchar) AS upt_day,'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                            analysis_time,cpu_time,queued_time,wall_time,schema,query_operation,query_status,failure_message \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            order by CAST(analysis_time AS bigint) desc \
                            limit {limit};",
                "columns":['source','client_tags','upt_day','upt_batch','analysis_time','cpu_time','queued_time','wall_time','schema','query_operation','query_status','failure_message'],
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                }
            },
            f"Top {limit} slowest queries sorted by cpu time":{
                "query" :  f"select \
                            source,\
                            client_tags,\
                            'day-' || CAST(upt_day AS varchar) AS upt_day,'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                            analysis_time,cpu_time,queued_time,wall_time,schema,query_operation,query_status,failure_message \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            order by CAST(cpu_time AS bigint) desc \
                            limit {limit};",
                "columns":['source','client_tags','upt_day','upt_batch','analysis_time','cpu_time','queued_time','wall_time','schema','query_operation','query_status','failure_message'],
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                }
            },
            f"Top {limit} slowest queries sorted by wall time":{
                "query" :  f"select \
                            source,\
                            client_tags,\
                            'day-' || CAST(upt_day AS varchar) AS upt_day,'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                            analysis_time,cpu_time,queued_time,wall_time,schema,query_operation,query_status,failure_message \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            order by CAST(wall_time AS bigint) desc \
                            limit {limit};",
                "columns":['source','client_tags','upt_day','upt_batch','analysis_time','cpu_time','queued_time','wall_time','schema','query_operation','query_status','failure_message'],
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                }
            },
            f"Top {limit} slowest queries sorted by queued time":{
                "query" :  f"select \
                            source,\
                            client_tags,\
                            'day-' || CAST(upt_day AS varchar) AS upt_day,'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                            analysis_time,cpu_time,queued_time,wall_time,schema,query_operation,query_status,failure_message \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            order by CAST(queued_time AS bigint) desc \
                            limit {limit};",
                "columns":['source','client_tags','upt_day','upt_batch','analysis_time','cpu_time','queued_time','wall_time','schema','query_operation','query_status','failure_message'],
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                }
            },
            "Distribution of time taken by all the queries from each source" : {
                "query" :  get_full_query("complete_table")[0],
                "columns": get_full_query("complete_table")[1],
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                }
            },
            # "Distribution of time taken by all the queries" : {
            #     "query" :  get_full_query("all")[0],
            #     "columns":get_full_query("all")[1],
            #     "schema":{
            #         "merge_on_cols" : [],
            #         "compare_cols":[],
            #         "do_not_compare":True
            #     }
            # },
            # "Distribution of time taken by all the DAGs" : {
            #     "query" :  get_full_query("dag")[0],
            #     "columns":get_full_query("dag")[1],
            #     "schema":{
            #         "merge_on_cols" : [],
            #         "compare_cols":[],
            #         "do_not_compare":True
            #     }
            # },
            # "Distribution of time taken by all non-DAGs" : {
            #     "query" :  get_full_query("nondag")[0],
            #     "columns":get_full_query("nondag")[1],
            #     "schema":{
            #         "merge_on_cols" : [],
            #         "compare_cols":[],
            #         "do_not_compare":True
            #     }
            # },
          }