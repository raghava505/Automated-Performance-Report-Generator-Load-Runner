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

# Variables
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
base_stack_config_path = f"{ROOT_PATH}/config"

class SelfManaged_Accuracy:

    def __init__(self,start_timestamp,end_timestamp,prom_con_obj,variables):
        
        test_env_file_path = "{}/{}".format(base_stack_config_path,variables["test_env_file_name"])
        
        with open(test_env_file_path,"r") as file:
            data = json.load(file)
            # print(data)
        
        self.load_start=start_timestamp
        self.load_end=end_timestamp
        self.upt_day="".join(str(start_timestamp.strftime("%Y-%m-%d")).split('-'))
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password
        self.target_host = data["dnodes"][0]
        self.cloud_domain = data["domain"]
        if self.cloud_domain ==  "longevity":
            self.cloud_domain = "longevity1"
        self.expected_data = None
        self.actual_data = dict()
        self.simnodes = data["selfsim_nodes"]
        self.vsidata = vsi_data
        self.tables = tables
        self.accuracy = dict()
        
        
    def fetch_trino_password(self): 
        
        remote_host = self.target_host
        remote_username = 'abacus'
        remote_password = 'abacus'


        psql_command = "PGPASSWORD=pguptycs psql -h {} -U uptycs -p 5432 -d configdb -c \"select read_password from customer_database where database_name='upt_{}';\"".format(remote_host,self.cloud_domain)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(remote_host, username=remote_username, password=remote_password)
            print("SSH connection established successfully.")

            stdin, stdout, stderr = ssh.exec_command(psql_command)
            output = stdout.read().decode('utf-8')
            error_output = stderr.read().decode('utf-8')
            password = output.split()[2]
            
            if error_output:
                print("Error output:")
                print(error_output)

        finally:
            
            stdin.close()
            stdout.close()
            stderr.close()
            ssh.close()
        return password

    def actual_records(self):
        
        time_change = timedelta(minutes=deltaTime)
        end_time = self.load_end + time_change
        
        for t in self.tables:
            if t == "vulnerabilities_scanned_images":
                query = """select count(*) from {} where system_id like 'bat%'""".format("upt_"+t)
            else:
                query = """select count(*) from {} where upt_day>={} and upt_time>=timestamp'{}' and upt_time<=timestamp'{}' and upt_hostname like 'self%'""".format(t,self.upt_day,self.load_start,end_time)
            
            # trino_password = self.fetch_trino_password()
            
            # command = f"sudo -u monkey TRINO_PASSWORD={trino_password} /opt/uptycs/cloud/utilities/trino-cli --insecure --server https://localhost:5665 --schema upt_system --user upt_read_{self.cloud_domain} --catalog uptycs --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/etc/presto/presto.jks --execute \"{query}\""
            
            command="""sudo TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --server https://localhost:5665 --user uptycs --catalog uptycs --schema upt_{} --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/cloud/config/wildcard.jks --insecure --execute "{} ;" """.format(self.cloud_domain, query)
            # print(self.target_host)
            # print(command)
            conn = Connection(host=self.target_host, user=self.username, connect_kwargs={'password': self.password})
            res = conn.sudo(command, password=self.password, hide='stderr')
            result_list = res.stdout.split("\n")
            self.actual_data[t] = int(result_list[0].split("\"")[1])
        # print(self.actual_data)

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
   

