from pathlib import Path

#json_directory = ""
PROJECT_ROOT = Path(__file__).resolve().parent


tables = ['kubernetes_nodes','kubernetes_pods','kubernetes_namespaces','kubernetes_pod_containers','kubernetes_events','kubernetes_role_policy_rules','kubernetes_cluster_role_policy_rules','kubernetes_role_binding_subjects','kubernetes_cluster_role_binding_subjects','kubernetes_service_accounts','vulnerabilities_scanned_images', 'vulnerabilities','process_events','socket_events', 'process_file_events','dns_lookup_events']

final_data = {
    "kubernetes_nodes": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_pods": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_namespaces": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_pod_containers": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_events": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_role_policy_rules": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_cluster_role_policy_rules": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_role_binding_subjects": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_cluster_role_binding_subjects": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_service_accounts": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "vulnerabilities_scanned_images": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "vulnerabilities": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "process_events": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "socket_events": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "process_file_events": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "dns_lookup_events": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    }
}

asset_count = 100
#sim_nodes = ['s13sim1','s13sim2','s13sim3','s13sim4']
# sim_nodes = ['s13sim2','s13sim3','s13sim4']

kubesim_ports = [1255,1256]
osquery_ports = [28010,28020]
# In Minutes
deltaTime = 10 

kube_data = {0:0,1:0,2:0,3:0,5:0,6:0,7:0,8:0,9:0,10:0}
kube_index_map = {0:'kubernetes_nodes',
                  1:'kubernetes_pods',
                  2:'kubernetes_namespaces',
                  3:'kubernetes_pod_containers',
                  10:'kubernetes_service_accounts',
                  6:'kubernetes_role_policy_rules',
                  8:'kubernetes_role_binding_subjects',
                  7:'kubernetes_cluster_role_policy_rules',
                  9:'kubernetes_cluster_role_binding_subjects',
                  5:'kubernetes_events'}

cvd_data = {"VulnerabilitiesScannedImages_Count":0, 
             "Vulnerabilities_Count":0, 
             "Compliance_Count":0, 
             "ProcessEvents_Count":0, 
             "SocketEvents_Count":0, 
             "ProcessFileEvents_Count":0, 
             "DnsLookupEvents_Count":0, 
             }

key_mapping = {
    'VulnerabilitiesScannedImages_Count': 'vulnerabilities_scanned_images',
    'Vulnerabilities_Count': 'vulnerabilities',
    'Compliance_Count': 'compliance',
    'ProcessEvents_Count': 'process_events',
    'SocketEvents_Count': 'socket_events',
    'ProcessFileEvents_Count': 'process_file_events',
    'DnsLookupEvents_Count': 'dns_lookup_events',
}