import re
import os
import sys
sys.path.append('kubequery/') 
import json
import paramiko
from .kubequery_configs import *
from fabric import Connection
from datetime import datetime, timedelta
from pathlib import Path


# PROJECT_ROOT = Path(__file__).resolve().parent
# CONFIG_PATH = "./config"

# Variables
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
base_stack_config_path = f"{ROOT_PATH}/config"
print(base_stack_config_path)

class Kube_Accuracy:

    def __init__(self,start_timestamp,end_timestamp,prom_con_obj,variables):
        
        test_env_file_path = "{}/{}".format(base_stack_config_path,variables["test_env_file_name"])
        
        with open(test_env_file_path,"r") as file:
            data = json.load(file)
            # print(data)
        
        self.load_start=start_timestamp
        self.load_end=end_timestamp
        self.upt_day="".join(str(start_timestamp.strftime("%Y-%m-%d")).split('-'))
        # self.test_env_file_path=prom_con_obj.test_env_file_path
        # self.PROMETHEUS = prom_con_obj.prometheus_path
        # self.API_PATH = prom_con_obj.prom_point_api_path
        # self.port=prom_con_obj.ssh_port
        # self.username = prom_con_obj.abacus_username
        # self.password  = prom_con_obj.abacus_password
        self.port = 22
        self.username = "abacus"
        self.password  = "abacus"
        self.target_host = data["dnodes"][0]
        self.cloud_domain = data["domain"]
        if self.cloud_domain ==  "longevity":
            self.cloud_domain = "longevity1"
        self.data = final_data
        self.expected_data = None
        self.actual_data = dict()
        self.simnodes = data["kubesim_nodes"]
        self.kubedata = {0:0,1:0,2:0,3:0,5:0,6:0,7:0,8:0,9:0,10:0}
        self.cvddata = cvd_data
        self.tables = tables
        self.accuracy = dict()


    def actual_records(self):
        
        time_change = timedelta(minutes=deltaTime)
        end_time = self.load_end + time_change        
        
        for t in self.tables:
            if t == "vulnerabilities_scanned_images":
                query = """select count(*) from {} where system_id like 'c0d3%'""".format("upt_"+t)
            else:
                query = """select count(*) from {} where upt_day>={} and upt_time>=timestamp'{}' and upt_time<=timestamp'{}' and upt_hostname like 'cluster%'""".format(t,self.upt_day,self.load_start,end_time)
            
            command="""sudo TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --server https://localhost:5665 --user uptycs --catalog uptycs --schema upt_{} --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/cloud/config/wildcard.jks --insecure --execute "{} ;" """.format(self.cloud_domain, query)
            conn = Connection(host=self.target_host, user=self.username, connect_kwargs={'password': self.password})
            print(command)
            res = conn.sudo(command, password=self.password, hide='stderr')
            result_list = res.stdout.split("\n")
            self.actual_data[t] = int(result_list[0].split("\"")[1])

        #print(self.actual_data)


    def expected_records(self):
        for node in self.simnodes:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(node, self.port, self.username, self.password)
            
            for port in kubesim_ports:
                command = "cd /home/abacus/kubequerysim/accuracy && tail -n 11 Kubesim{}.log".format(port)
                # command = "cd /home/abacus/kubequerysim/accuracy && tail -n 11 \"$(ls -lrth | tail -n 1 | awk '{print $9}')\" | awk '{ for (i = 7; i <= NF; i++) printf $i \" \"; printf \"\\n\" }'"
                # command = "cd /home/abacus/kubequerysim/logs && tail -n 11 \"$(ls -lrth | head -n 60 | tail -n 1 | awk '{print $9}')\" | awk '{ for (i = 7; i <= NF; i++) printf $i \" \"; printf \"\\n\" }'"

                stdin, stdout, stderr = ssh_client.exec_command(command)
                output = stdout.read().decode('utf-8')
                errors = stderr.read().decode('utf-8')
                
                if output == "":
                    print("Please check the existence your Kubesim{}.log file in /home/abacus/kubequerysim/accuracy".format(port))
                # print(output)
                # sys.exit()
            
                for i,data in enumerate(output.split("\n")):
                    # print(data)
                    if i in self.kubedata.keys():
                        # print(re.findall(r'\d+',data)[-1])
                        self.kubedata[i]+=int(re.findall(r'\d+',data)[-1])

            self.kube_data = {kube_index_map[key]: value for key, value in self.kubedata.items()}
            print(json.dumps(self.kube_data, indent=4)) 
            # sys.exit()
            
            for port in osquery_ports:

                ssh_client.connect(node, self.port, self.username, self.password)

                command = "cd /home/abacus/new_kubequery && cat osx_log{}.out | grep statistic".format(port)
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
                        self.cvddata = {key: self.cvddata[key] + values[key] for key in self.cvddata}
                
               
        self.cvddata = {key: self.cvddata[key] * asset_count for key in self.cvddata}
        self.cvddata = {key_mapping[key]: value for key, value in self.cvddata.items()}
        print(json.dumps(self.cvddata, indent=4))
        self.expected_data = {**self.kube_data, **self.cvddata}
        #print(self.expected_data)

    def accuracy_kubernetes(self):
        self.expected_records()
        self.actual_records()
        # sys.exit()
        for t in self.tables:
            self.accuracy[t] = {
                "Expected Records" : self.expected_data[t],
                "Actual Records" : self.actual_data[t],
                "Accuracy" : (self.actual_data[t]+1/self.expected_data[t]+1)*100
            }
        #print(self.accuracy)
        return self.accuracy
    





    

