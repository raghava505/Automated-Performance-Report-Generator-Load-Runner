import os
#ports
API_REPORT_PORT = 8001
PGBADGER_REPORT_PORT = 8000
PROMETHEUS_PORT = 9090
KUBE_PROMETHEUS_PORT = 31090
SSH_PORT = 22
PGBADGER_PORT = 5602
ELASTICSEARCH_PORT = 9200

#ips
PERF_PROD_DASHBOARD = "192.168.146.69"

#int and strings
PROM_API_PATH = "/api/v1/query_range"
PROM_POINT_API_PATH = "/api/v1/query"
ABACUS_USERNAME = 'abacus'  
ABACUS_PASSWORD = 'abacus' 
MONGO_CONNECTION_STRING = "mongodb://localhost:27017"
# api_loads_folder_path = "/home/abacus/apache-jmeter-5.6.2/bin/reports/"
PRESTO_LOADS_FOLDER_PATH = "/home/abacus/benchto_reports/"
API_LOADS_FOLDER_PATH_TEMP = "/home/abacus/apache-jmeter-5.6.2/bin/reports/"

#other types
KUBE_METRICS = ["container_memory_working_set_bytes","container_cpu_usage_seconds_total"]

#dynamic
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
STACK_JSONS_PATH = os.path.join(ROOT_PATH,'stacks')
BASE_GRAPHS_PATH = os.path.join(os.path.dirname(ROOT_PATH),'graphs')
BASE_HTMLS_PATH = os.path.join(os.path.dirname(ROOT_PATH),'htmls')
BASE_PDFS_PATH = os.path.join(os.path.dirname(ROOT_PATH),'pdfs')
BASE_LOGS_PATH = os.path.join(ROOT_PATH,'logs')
BASE_ANALYSIS_PIECHARTS_PATH = os.path.join(ROOT_PATH,'analysis_piecharts')


