import re
import os
import sys
sys.path.append('kubequery/') 
import json
import paramiko
from .selfmanaged_configs import *
from fabric import Connection
from datetime import timedelta
from pathlib import Path
from helper import measure_time

# Variables
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
base_stack_config_path = f"{ROOT_PATH}/config"

class SelfManaged_Accuracy:

    def __init__(self,start_timestamp,end_timestamp,prom_con_obj,variables):
        test_env_file_path=prom_con_obj.test_env_file_path
        with open(test_env_file_path,"r") as file:
            data = json.load(file)
        
        self.load_start=start_timestamp
        self.load_end=end_timestamp
        self.upt_day="".join(str(start_timestamp.strftime("%Y-%m-%d")).split('-'))
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password
        self.target_host = prom_con_obj.execute_trino_queries_in
        self.cloud_domain = data["domain"]
        if self.cloud_domain ==  "longevity":
            self.cloud_domain = "longevity1"
        self.expected_data = None
        self.actual_data = dict()
        self.simnodes = data["selfsim_nodes"]
        self.vsidata = vsi_data
        self.tables = tables
        self.accuracy = dict()


    @measure_time
    def actual_records(self):
        
        time_change = timedelta(minutes=deltaTime)
        end_time = self.load_end + time_change
        
        for t in self.tables:
            if t == "vulnerabilities_scanned_images":
                query = """select count(*) from {} where system_id like 'bat%'""".format("upt_"+t)
            else:
                query = """select count(*) from {} where upt_day>={} and upt_time>=timestamp'{}' and upt_time<=timestamp'{}' and upt_hostname like 'self%'""".format(t,self.upt_day,self.load_start,end_time)
                                    
            command="""sudo TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --server https://localhost:5665 --user uptycs --catalog uptycs --schema upt_{} --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/cloud/config/wildcard.jks --insecure --execute "{} ;" """.format(self.cloud_domain, query)
            # print(command)
            conn = Connection(host=self.target_host, user=self.username, connect_kwargs={'password': self.password})
            res = conn.sudo(command, password=self.password, hide='stderr')
            result_list = res.stdout.split("\n")
            self.actual_data[t] = int(result_list[0].split("\"")[1])
        # print(self.actual_data)

    @measure_time
    def expected_records(self):
        for node in self.simnodes:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(node, self.port, self.username, self.password)
            
            for port in ports: 
                command = "cd /home/abacus/vsi_selfmanaged && cat osx_log{}.out | grep statistic".format(port)
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
        print(json.dumps(self.expected_data, indent=4))

    def accuracy_selfmanaged(self):
        self.expected_records()
        self.actual_records()
        for t in self.tables:
            self.accuracy[t] = {
                "Expected Records" : self.expected_data[t],
                "Actual Records" : self.actual_data[t],
                "Accuracy" : round(((self.actual_data[t]+1)/(self.expected_data[t]+1))*100 , 2)
            }
        #print(self.accuracy)
        return self.accuracy
   

