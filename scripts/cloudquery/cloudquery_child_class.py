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
    def hostname_types(cls):
        return ["process","data","pg","ep"]

    @classmethod
    @property
    def common_app_names(cls):
        temp = copy.deepcopy(parent.common_app_names)
        temp['sum'].extend([".*effectivePermissions.*","sts.*","/usr/lib/memgraph/memgraph","/opt/uptycs/cloud/go/bin/cloudqueryConsumer","cloudDetectionConsumer",".*statedb.*","cloudConnectorIngestion"])
        return temp
    

    @classmethod
    @property
    def application_level_usage_app_names_for_table(cls):
        temp = copy.deepcopy(parent.application_level_usage_app_names_for_table)
        temp.extend([".*effectivePermissions.*","sts.*","/usr/lib/memgraph/memgraph","/opt/uptycs/cloud/go/bin/cloudqueryConsumer","cloudDetectionConsumer",".*statedb.*","cloudConnectorIngestion"])
        return temp


    @classmethod
    @property
    def mon_spark_topic_names(cls):
        temp = copy.deepcopy(parent.mon_spark_topic_names)
        temp.extend(["cloudconnectorsink"])
        return temp
    
    @classmethod
    @property
    def kafka_group_names(cls):
        temp = copy.deepcopy(parent.kafka_group_names)
        temp.extend(["cloudqueryinventorygroup" , "cloudcompliancemanager" , "ruleenginecc"])
        return temp
    
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
                    'Triage bugs and check for blockers',
                    'Check if PG master is in sync with replica',
                    'Check for memory leaks',
                    'Check for variation in HDFS disk usage',
                    'Check for variation in PG disk usage',
                    'Check for variation in Kafka disk usage',
                ]