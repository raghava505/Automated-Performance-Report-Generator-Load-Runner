from parent_load_details import parent
import copy
from collections import OrderedDict
from osquery.osquery_child_class import osquery_child
from cloudquery.cloudquery_child_class import cloudquery_child
from kubequery.kubequery_child_class import kubequery_child

all_combined_child_classes = [osquery_child, cloudquery_child,kubequery_child]
class all_combined_child(parent):
    load_specific_details={
                "GoldenTest":{
                    "test_title": "Multiple Customer Rule Engine, Control Plane, CloudQuery, KubeQuery and SelfManaged Load",
                    
                    "RuleEngine and ControlPlane Load Details":{
                        "total_number_of_customers_osquery": 100,

                        # "number_of_customers_with_auto_exception_enabled": 0,
                        # "osquery total_assets": "32K Control Plane +  8K Multi customer",
                        # "records_sent_per_hour_per_customer": "51,84,000",
                        # "records_sent_per_hour" : "51,84,00,000",
                        # "assets_per_cust":80,
                        # "input_file": "rhel7-6tab_12rec.log",
                        # "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events",

                        "number_of_customers_with_auto_exception_enabled": "0",
                        "total_assets": "30K Control Plane + 10K Multi customer",
                        "assets_per_cust":"100",
                        "records_sent_per_hour_per_customer": "6.48 million", #"5.44 million", 
                        "records_sent_per_hour" : "648 million", # "653 million", 
                        "input_file": "rhel7-6tab_12rec.log",
                        "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events"
                    },

                    "CloudQuery Load Details":{
                        "total_number_of_customers_cloudquery": "25",
                        "AWS Services telemetry simulated in the Load" : "EC2, EBS, IAM, Replication Group, Security Group, Elastic Kubernetes Service(EKS), Simple Storage Service(S3), Elastic File System(EFS), RDS, VPC, CodePipeline, ElastiCache, CloudTrail, Redshift, Subnet, Organizations, Elastic Load Balancer, S3 glacier, Lambda, Simple Queue Service(SQS), Simple Notification Service(SNS), CloudFront, CodeCommit, Kinesis, API Gateway,Elastic Container Registry,Elastic Container Service,Route 53, CodeDeploy,CloudWatch,CloudFormation,Config,Service Catalog,Systems Manager, Resource Access Manager, Secrets Manager, GuardDuty,Key Management Service,Directory Service,Web Application Firewall,Security Hub",
                        "AWS Tables Validated in the Load" : "aws_ec2_instance,aws_ec2_address,aws_ec2_image, aws_ec2_snapshot,aws_ec2_volume ,aws_elb , aws_lambda_function ,aws_ecr_repository, aws_ecs_cluster,aws_eks_cluster,aws_s3_bucket ,aws_efs_file_system,aws_glacier_vault , aws_rds_db_instance,aws_rds_db_cluster,aws_rds_db_snapshot,aws_elasticache_cluster, aws_elasticache_replication_group,aws_ec2_vpc,aws_ec2_security_group,aws_ec2_network_acl, aws_cloudfront_distribution,aws_route53_domain, aws_route53_hosted_zone, aws_api_gateway_rest_api,aws_codecommit_repository,aws_codedeploy_application ,aws_codepipeline, aws_organizations_account,aws_organizations_account,aws_cloudwatch_metric_alarm, aws_cloudformation_stack,aws_cloudtrail_trail,aws_cloudtrail_events,aws_config_delivery_channel, aws_servicecatalog_portfolio, aws_ssm_managed_instance, aws_redshift_cluster, aws_kinesis_data_stream,aws_iam_group,aws_iam_user,aws_iam_policy, aws_iam_role, aws_ram_resource_share, aws_secretsmanager_secret ,aws_guardduty_detector, aws_kms_key, aws_directoryservice_directory,aws_wafv2_web_acl,aws_securityhub_hub,aws_ec2_subnet, aws_sqs_queue,aws_sns_topic, aws_workspaces_workspace",
                        "GCP Services used to conduct the Load" : "Identity and Access Management(IAM) , Compute ,Google Kubernetes Engine (GKE) , Cloud Storage , Filestore , Cloud Logging , Cloud Monitoring , Cloud DNS , Pubsub , Cloud SQL , BigQuery , Memorystore , Cloud Functions , Cloud Run , Cloud Key Management, Secret Manager",
                        "GCP Tables Validated in the Load" : "gcp_iam_role , gcp_compute_disk , gcp_container_cluster , gcp_storage_bucket , gcp_file_backup , gcp_logging_metric , gcp_monitoring_alert_policy , gcp_dns_policy , gcp_pubsub_topic , gcp_sql_database , gcp_bigquery_table , gcp_memorystore_redis_instance , gcp_cloud_function , gcp_cloud_run_service , gcp_kms_key , gcp_secret_manager_secret_version, gcp_pubsub_subscription , gcp_file_instance,gcp_compute_image,gcp_dns_managed_zone,gcp_sql_instance,gcp_bigquery_dataset,gcp_memorystore_memcached_instance,gcp_cloud_run_revision,gcp_iam_service_account,gcp_compute_instance,gcp_logging_sink,gcp_secret_manager_secret",
                        "total_number_of_customers_azure": "20",
                        "Azure Services used to conduct the Load" : "Management, Compute, Network, Storage, Databases, Identity, RBAC",
                        "Tables Validated in the Load" : "azure_network_vnet, azure_network_subnet, azure_compute_vm, azure_compute_disk, azure_network_nic, azure_network_nsg, azure_network_load_balancer, azure_network_public_ip_address, azure_network_route_table, azure_resource_group, azure_network_application_gateway, azure_appservice_site, azure_appservice_appsetting, azure_storage_blob_container, azure_storage_account, azure_sql_database, azure_sql_server, azure_storage_file_share, azure_active_directory_service_principal,azure_active_directory_application, azure_active_directory_role_assignment, azure_active_directory_role_definition, azure_rbac_role_definition, azure_rbac_role_assignment, azure_active_directory_group, azure_active_directory_user",
                        "Total number of Accounts": "67",
                    },

                    "KubeQuery Load Details":{
                        "total_number_of_customers_kubequery": "1",
                        "total_clusters": "20",
                        "kubequery total_assets": "800",
                        "total_namespaces": "2000",
                        "total_pods": "40000",
                        "total_containers": "20000",
                    },
                    "SelfManaged Load Details":{
                        "total_number_of_customers_self_managed": "1",
                        "self_managed total_assets": "200"       
                    }             
                }
    }


    @classmethod
    @property
    def common_app_names(cls):
        final_sum=[]
        final_avg=[]
        for load_class in all_combined_child_classes:
            temp=copy.deepcopy(load_class.common_app_names)
            print(temp)
            temp_sum=temp["sum"]
            temp_avg=temp["avg"]
            final_sum=list(OrderedDict.fromkeys(temp_sum+final_sum))
            final_avg=list(OrderedDict.fromkeys(temp_avg+final_avg))
        return {"sum":final_sum,"avg":final_avg}
    
    @classmethod
    @property
    def common_container_names(cls):
        final=[]
        for load_class in all_combined_child_classes:
            temp=copy.deepcopy(load_class.common_container_names)
            final=list(OrderedDict.fromkeys(temp+final))
        return final
    
    @classmethod
    @property
    def mon_spark_topic_names(cls):
        final=[]
        for load_class in all_combined_child_classes:
            temp=copy.deepcopy(load_class.mon_spark_topic_names)
            final=list(OrderedDict.fromkeys(temp+final))
        return final
    
    @classmethod
    @property
    def kafka_group_names(cls):
        final=[]
        for load_class in all_combined_child_classes:
            temp=copy.deepcopy(load_class.kafka_group_names)
            final=list(OrderedDict.fromkeys(temp+final))
        return final
    
    @classmethod
    @property
    def common_pod_names(cls):
        final=[]
        for load_class in all_combined_child_classes:
            temp=copy.deepcopy(load_class.common_pod_names)
            final=list(OrderedDict.fromkeys(temp+final))
        return final
    
    @classmethod
    @property
    def list_of_observations_to_make(cls):
        final=[]
        for load_class in all_combined_child_classes:
            temp=copy.deepcopy(load_class.list_of_observations_to_make)
            final=list(OrderedDict.fromkeys(temp+final))
        return final
