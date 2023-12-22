from parent_load_details import parent
import copy
from collections import defaultdict


class cloudquery_child(parent):
    load_specific_details={
            "AWS_MultiCustomer":{
                "total_number_of_customers": "25",
                "test_title": "AWS Multicustomer load with 25 customers",
                "AWS Services telemetry simulated in the Load" : "EC2, EBS, IAM, Replication Group, Security Group, Elastic Kubernetes Service(EKS), Simple Storage Service(S3), Elastic File System(EFS), RDS, VPC, CodePipeline, ElastiCache, CloudTrail, Redshift, Subnet, Organizations, Elastic Load Balancer, S3 glacier, Lambda, Simple Queue Service(SQS), Simple Notification Service(SNS), CloudFront, CodeCommit, Kinesis, API Gateway,Elastic Container Registry,Elastic Container Service,Route 53, CodeDeploy,CloudWatch,CloudFormation,Config,Service Catalog,Systems Manager, Resource Access Manager, Secrets Manager, GuardDuty,Key Management Service,Directory Service,Web Application Firewall,Security Hub",
                "Tables Validated in the Load" : "aws_ec2_instance,aws_ec2_address,aws_ec2_image, aws_ec2_snapshot,aws_ec2_volume ,aws_elb , aws_lambda_function ,aws_ecr_repository, aws_ecs_cluster,aws_eks_cluster,aws_s3_bucket ,aws_efs_file_system,aws_glacier_vault , aws_rds_db_instance,aws_rds_db_cluster,aws_rds_db_snapshot,aws_elasticache_cluster, aws_elasticache_replication_group,aws_ec2_vpc,aws_ec2_security_group,aws_ec2_network_acl, aws_cloudfront_distribution,aws_route53_domain, aws_route53_hosted_zone, aws_api_gateway_rest_api,aws_codecommit_repository,aws_codedeploy_application ,aws_codepipeline, aws_organizations_account,aws_organizations_account,aws_cloudwatch_metric_alarm, aws_cloudformation_stack,aws_cloudtrail_trail,aws_cloudtrail_events,aws_config_delivery_channel, aws_servicecatalog_portfolio, aws_ssm_managed_instance, aws_redshift_cluster, aws_kinesis_data_stream,aws_iam_group,aws_iam_user,aws_iam_policy, aws_iam_role, aws_ram_resource_share, aws_secretsmanager_secret ,aws_guardduty_detector, aws_kms_key, aws_directoryservice_directory,aws_wafv2_web_acl,aws_securityhub_hub,aws_ec2_subnet, aws_sqs_queue,aws_sns_topic, aws_workspaces_workspace"
            },
            "GCP_MultiCustomer":{
                "total_number_of_customers": "25",
                "test_title": "GCP Multicustomer load with 25 customers",
                "GCP Services used to conduct the Load" : "Identity and Access Management(IAM) , Compute ,Google Kubernetes Engine (GKE) , Cloud Storage , Filestore , Cloud Logging , Cloud Monitoring , Cloud DNS , Pubsub , Cloud SQL , BigQuery , Memorystore , Cloud Functions , Cloud Run , Cloud Key Management, Secret Manager",
                "Tables Validated in the Load" : "gcp_iam_role , gcp_compute_disk , gcp_container_cluster , gcp_storage_bucket , gcp_file_backup , gcp_logging_metric , gcp_monitoring_alert_policy , gcp_dns_policy , gcp_pubsub_topic , gcp_sql_database , gcp_bigquery_table , gcp_memorystore_redis_instance , gcp_cloud_function , gcp_cloud_run_service , gcp_kms_key , gcp_secret_manager_secret_version, gcp_pubsub_subscription , gcp_file_instance,gcp_compute_image,gcp_dns_managed_zone,gcp_sql_instance,gcp_bigquery_dataset,gcp_memorystore_memcached_instance,gcp_cloud_run_revision,gcp_iam_service_account,gcp_compute_instance,gcp_logging_sink,gcp_secret_manager_secret"
            }
    }
    
    
    @classmethod
    @property
    def common_app_names(cls):
        
        return  {"sum":[".*effectivePermissions.*","sts.*","/usr/lib/memgraph/memgraph","/opt/uptycs/cloud/go/bin/cloudqueryConsumer",
                        "cloudDetectionConsumer",".*statedb.*","cloudConnectorIngestion","orc-compaction" ,".*configdb.*", "kafka",".*ruleEngine.*",
                        "data-archival",".*redis-server.*","/opt/uptycs/cloud/go/bin/complianceSummaryConsumer","tls",".*airflow.*",
                        "trino" , "osqueryIngestion",".*osqLogger.*","spark-worker","spark-worker"],
                "avg":[]
                }
    
    @classmethod
    @property
    def hostname_types(cls):
        return ["process","data","pg"]
    
    @classmethod
    @property
    def memory_app_names(cls):
        return copy.deepcopy(cls.common_app_names)
    
    @classmethod
    @property
    def cpu_app_names(cls):
        app_names =copy.deepcopy(cls.common_app_names)
        app_names['sum'].extend(["pgbouncer","spark-master","/usr/local/bin/pushgateway"])
        return app_names

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
        app_level_RAM_used_percentage_queries= dict([(f"Memory Used by {app}",(f"{key}(uptycs_app_memory{{app_name=~'{app}'}}) by (host_name)" , ["host_name"], '%') ) for key,app_list in cls.memory_app_names.items() for app in app_list])
        more_memory_queries={
            "Kafka Disk Used Percentage":("uptycs_percentage_used{partition=~'/data/kafka'}" , ["host_name"], '%'),
            "Debezium memory usage":("uptycs_docker_mem_used{container_name='debezium'}" , ["host_name"],'bytes'),
        }
        app_level_RAM_used_percentage_queries.update(more_memory_queries)
        return app_level_RAM_used_percentage_queries

    @classmethod
    def get_node_level_CPU_busy_percentage_queries(cls):
        return dict([(f"{node} node CPU busy percentage",(f"100-uptycs_idle_cpu{{node_type='{node}'}}",["host_name"], '%') ) for node in cls.hostname_types])
    
    @classmethod
    def get_app_level_CPU_used_cores_queries(cls):
        app_level_CPU_used_cores_queries=dict([(f"CPU Used by {app}", (f"{key}(uptycs_app_cpu{{app_name=~'{app}'}}) by (host_name)" , ["host_name"], '%') ) for key,app_list in cls.cpu_app_names.items() for app in app_list])
        more_cpu_queries={
            "Debezium CPU usage":("uptycs_docker_cpu_stats{container_name='debezium'}" , ["host_name"]),
        }

        app_level_CPU_used_cores_queries.update(more_cpu_queries)
        return app_level_CPU_used_cores_queries
    
    @classmethod
    @property
    def mon_spark_topic_names(cls):
        return ["cloudconnectorsink","event"]
    
    @classmethod
    @property
    def kafka_group_names(cls):
        return ["cloudqueryinventorygroup","cloudcompliancemanager",'ruleenginecc','ruleenginecc','debeziumconsumer']
    
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
        for topic in cls.mon_spark_topic_names:
            queries.update(cls.get_inject_drain_and_lag_uptycs_mon_spark(topic))
        for group in cls.kafka_group_names:
            queries.update(cls.get_inject_drain_and_lag_uptycs_kafka_group(group))
        return copy.deepcopy(queries)
        
    
    @staticmethod
    def get_other_chart_queries():
        return {"Active Client Connections":("uptycs_pgb_cl_active" , ["host_name","db","db_user"]),
                        "Redis client connections for tls":("sum(uptycs_app_redis_clients{app_name='/opt/uptycs/cloud/tls/tls.js'}) by (host_name)" , ["host_name"]),
                        "Configdb Pg wal folder size":("configdb_wal_folder",["host_name"]),
                        "Configdb number of wal files":("configdb_wal_file{}" , ["host_name"]),
                        "Top 10 redis client connections by app":("sort(topk(9,sum(uptycs_app_redis_clients{}) by (app_name)))" , ["app_name"]),
                        "Configdb folder size":("configdb_size" , ["host_name"]),
                        "Average records in pg bouncer":("uptycs_pbouncer_stats{col=~'avg.*', col!~'.*time'}" , ["col"]),
                        "Average time spent by pg bouncer":("uptycs_pbouncer_stats{col=~'avg.*time'}" , ["col"] , 'μs'),
                        "iowait time":("uptycs_iowait{}" , ["host_name"]),
                        "iowait util%":("uptycs_iowait_util_percent{}" , ["host_name" , "device"]),
                        "Waiting Client Connections":("uptycs_pgb_cl_waiting", ["db" , "db_user"]),
                        "Disk read wait time":("uptycs_r_await{}" , ["host_name" , "device"],'ms'),
                        "Disk write wait time":("uptycs_w_await{}", ["host_name" , "device"],'ms'),
                        "Idle server connections":("uptycs_pgb_sv_idle", ["db" , "db_user"]),
                        "Active Server Connections":("uptycs_pgb_sv_active", ["db" , "db_user"]),
                        "Disk blocks in configdb":("uptycs_configdb_stats{col =~ \"blks.*\"}",["col"]),
                        "Transaction count in configdb":("uptycs_configdb_stats{col =~ \"xact.*\"}",["col"]),
                        "Row count in configdb":("uptycs_configdb_stats{col =~ \"tup.*\"}",["col"]),
                        "Assets table stats":("uptycs_psql_table_stats",["col"]),
                        "PG and data partition disk usage in configdb" : ("uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/data\"} or uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/pg\"}" , ["partition","host_name"],'bytes')
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
            "Uptycs applications restart count":('sum(uptycs_app_restart) by (app_name)' , ["app_name"]),
            }
    
    @classmethod
    def get_all_chart_queries(cls):
        return {
            "Live Assets and Kafka lag for all groups":cls.get_basic_chart_queries(),
            "Node-level Memory Charts":cls.get_node_level_RAM_used_percentage_queries(),
            "Node-level CPU Charts":cls.get_node_level_CPU_busy_percentage_queries(),
            "Application-level Memory Charts":cls.get_app_level_RAM_used_percentage_queries(),
            "Application-level CPU Charts":cls.get_app_level_CPU_used_cores_queries(),
            "Inject-Drain rate and Lag Charts":cls.get_inject_drain_rate_and_lag_chart_queries(),
            "Pg Stats Charts": cls.get_pg_charts(),
            "Restart count Charts": cls.get_restart_count_charts(),
            "Other Charts":cls.get_other_chart_queries()
        }


    load_specific_details=defaultdict(lambda:{})

    @classmethod
    def get_load_specific_details(cls,load_name):
        return cls.load_specific_details[load_name]
    
    @classmethod
    @property
    def list_of_observations_to_make(cls):
        return [
                    'Check 100 percent accuracy for inventory tables',
                    'Check 100 percent accuracy for current tables',
                    'Check for Statedb Errors',
                    'Check for Ruleenginecc lag',
                    'Check for cloudquery inventory lag',
                    'Check for cloudtrial events lag',
                    'Check for cloudcompliance manager lag',
                    'Check for Db events lag',
                    'Check for cloudconnector Ingestion lag',

                ]
    
    @classmethod
    def get_dictionary_of_observations(cls):
        observations_dict=dict([(observation,{"Status":"" , "Comments":""}) for observation in cls.list_of_observations_to_make])
        return observations_dict