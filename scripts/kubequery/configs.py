from pathlib import Path

json_directory = ""
PROJECT_ROOT = Path(__file__).resolve().parent


tables = ['kubernetes_nodes','kubernetes_pods','kubernetes_namespaces','kubernetes_pod_containers','kubernetes_events','kubernetes_role_policy_rules','kubernetes_cluster_role_policy_rules','kubernetes_role_binding_subjects','kubernetes_cluster_role_binding_subjects','kubernetes_service_accounts','vulnerabilities_scanned_images', 'vulnerabilities','process_events','socket_events', 'process_file_events','dns_lookup_events']

