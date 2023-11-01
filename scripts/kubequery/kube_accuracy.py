import json
from .configs import *
from fabric import Connection
from datetime import datetime, timedelta

# Variables

cloud_domain = stack_domain
day = "20231018"

class Kube_Accuracy:

    def __init__(self,start_timestamp,end_timestamp,prom_con_obj,variables):
        self.load_start=start_timestamp
        self.load_end=end_timestamp
        self.test_env_file_path=prom_con_obj.test_env_file_path
        self.PROMETHEUS = prom_con_obj.prometheus_path
        self.API_PATH = prom_con_obj.prom_point_api_path
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password
        self.target_host = "192.168.143.26"
        self.cloud_domain = "alphacentauri"


        #self.total_counts = getattr(configs, f'total_counts_{self.load_name.split("_")[0]}', None)

    def execute_command_on_presto(query):
        command="""sudo TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --server https://localhost:5665 --user uptycs --catalog uptycs --schema upt_{} --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/cloud/config/wildcard.jks --insecure --execute "{};" """.format(cloud_domain, query)
        conn = Connection(host=self.target_host, user=self.username, connect_kwargs={'password': self.password})
        res = conn.sudo(command, password=self.password, hide='stderr')
        result_list = res.stdout.split("\n")
        return int(result_list[0].split("\"")[1])

# Tables Order important


# Get the Expected Values json
f = open('kube_data.json')
kube_data = json.load(f)

f = open('kubequery_cvd.json')
kubecvd_data = json.load(f)

ExpectedValues = {**kube_data, **kubecvd_data}


# Populate the Actual Values Dictionary
ActualValues = {}
for table in tables:
    if table == "vulnerabilities_scanned_images":
        query = """select count(*) from {} ;""".format("upt_"+table)
    else:
        query = """select count(*) from {} where upt_day>={} and upt_time>=timestamp'{}' and upt_time<=timestamp'{}';""".format(table,day,start_timestamp,end_timestamp)
    ActualValues[table] = execute_command_on_presto(query)



  

# Accuracy Calculation
accuracy = {}  
for table in tables:
    accuracy[table] = {
        "Expected Records" : ExpectedValues[table],
        "Actual Records" : ActualValues[table],
        "Accuracy" : (ActualValues[table]/ExpectedValues[table])*100
    }


file_name = 'accuracy.json'

with open(file_name, 'w') as json_file:
    json.dump(accuracy, json_file, indent=4)

