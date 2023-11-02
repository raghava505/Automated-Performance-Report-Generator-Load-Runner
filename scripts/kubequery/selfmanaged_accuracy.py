import re
import sys
sys.path.append('kubequery/') 
import json
import paramiko
from selfmanaged_configs import *
from fabric import Connection
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

class SelfManaged_Accuracy:

    def __init__(self,start_timestamp,end_timestamp,prom_con_obj,variables):
        self.load_start=start_timestamp
        self.load_end=end_timestamp
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password
        self.target_host = "192.168.143.26"
        self.cloud_domain = "alphacentauri"
        self.expected_data = None
        self.actual_data = dict()
        self.simnodes = sim_nodes
        self.vsidata = vsi_data
        self.tables = tables
        self.accuracy = dict()

    def actual_records(self):
        for t in self.tables:
            if t == "vulnerabilities_scanned_images":
                query = """select count(*) from {} ;""".format("upt_"+t)
            else:
                query = """select count(*) from {} where upt_day>={} and upt_time>=timestamp'{}' and upt_time<=timestamp'{}';""".format(t,"2023-08-19",self.load_start,self.load_end)
            
            command="""sudo TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --server https://localhost:5665 --user uptycs --catalog uptycs --schema upt_{} --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/cloud/config/wildcard.jks --insecure --execute "{};" """.format(self.cloud_domain, query)
            conn = Connection(host=self.target_host, user=self.username, connect_kwargs={'password': self.password})
            res = conn.sudo(command, password=self.password, hide='stderr')
            result_list = res.stdout.split("\n")
            self.actual_data[t] = int(result_list[0].split("\"")[1])
        #print(self.actual_data)

    def expected_records(self):
        for node in self.simnodes:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(node, self.port, self.username, self.password)
    
            command = "cd /home/abacus/vsi_selfmanaged && cat osx_log28001.out | grep statistic"
            stdin, stdout, stderr = ssh_client.exec_command(command)
            output = stdout.read().decode('utf-8')
            errors = stderr.read().decode('utf-8')
            #print(errors)
            pattern = r'statistics_[a-zA-Z]+:\s*({[^}]+})'
            
            #print(output.split("\n"))
            for i,data in enumerate(output.split("\n")):
                if len(data)>0:
                    match = re.search(pattern, data).group(1)
                    valid_json_string = match.replace(" ",",").replace("{", '{"').replace(":", '":').replace(',',',"')
                    values = json.loads(valid_json_string)
                    self.vsidata = {key: self.vsidata[key] + values[key] for key in self.vsidata}
                
        self.vsidata = {key: self.vsidata[key] * asset_count for key in self.vsidata}
        self.expected_data = {key_mapping[key]: value for key, value in self.vsidata.items()}
            #print(self.cvddata)
        #print(self.expected_data)

    def accuracy_selfmanaged(self):
        self.expected_records()
        self.actual_records()
        for t in self.tables:
            self.accuracy[t] = {
                "Expected Records" : self.expected_data[t],
                "Actual Records" : self.actual_data[t],
                "Accuracy" : (self.actual_data[t]/self.expected_data[t])*100
            }
        #print(self.accuracy)
        return self.accuracy
    

