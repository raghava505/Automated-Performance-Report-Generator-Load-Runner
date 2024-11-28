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
from helper import measure_time
import pandas as pd

# PROJECT_ROOT = Path(__file__).resolve().parent
# CONFIG_PATH = "./config"


class Kube_Accuracy:

    def __init__(self,stack_obj):
        self.stack_obj=stack_obj
        self.load_start=stack_obj.start_time_UTC
        self.load_end=stack_obj.end_time_UTC

        test_env_file_path=stack_obj.test_env_file_path
        with open(test_env_file_path,"r") as file:
            data = json.load(file)
        
        self.upt_day="".join(str(self.load_start.strftime("%Y-%m-%d")).split('-'))
        self.port = 22
        self.username = "abacus"
        self.password  = "abacus"
        self.target_host = stack_obj.execute_trino_queries_in
        self.cloud_domain = data["domain"]
        if self.cloud_domain ==  "longevity":
            self.cloud_domain = "longevity1"
        self.data = final_data
        self.expected_data = None
        self.actual_data = dict()
        self.simnodes = data["kubesim_nodes"]
        self.kubedata = kube_data
        self.cvddata = cvd_data
        self.tables = tables
        self.accuracy = dict()


    @measure_time
    def actual_records(self):
        
        time_change = timedelta(minutes=deltaTime)
        end_time = self.load_end + time_change        
        
        for t in self.tables:
            if t == "vulnerabilities_scanned_images":
                query = """select count(*) from {} where system_id like 'c0d3%'""".format("upt_"+t)
            elif "kubernetes" in t:
                query = """select count(*) from {} where upt_day>={} and upt_time>=timestamp'{}'  and upt_time<=timestamp'{}'""".format(t,self.upt_day,self.load_start,end_time)
            else:
                query = """select count(*) from {} where upt_day>={} and upt_time>=timestamp'{}'  and upt_time<=timestamp'{}' and upt_hostname like 'cluster%'""".format(t,self.upt_day,self.load_start,end_time)
            
            command="""sudo -u monkey docker exec node /opt/uptycs/cloud/utilities/trino-cli.sh --user uptycs --password prestossl --catalog uptycs --schema upt_{} --execute "{};" """.format(self.cloud_domain, query)
            conn = Connection(host=self.target_host, user=self.username, connect_kwargs={'password': self.password})
            # print(command)
            res = conn.sudo(command, password=self.password, hide='stderr')
            result_list = res.stdout.split("\n")
            self.actual_data[t] = int(result_list[0].split("\"")[1])

        #print(self.actual_data)


    @measure_time
    def expected_records(self):
        for node in self.simnodes:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(node, self.port, self.username, self.password)
            
            for port in kubesim_ports:
                command = "cd /home/abacus/kubequerysim/accuracy && tail -n 13 Kubesim{}.log".format(port)
                # command = "cd /home/abacus/kubequerysim/accuracy && tail -n 11 \"$(ls -lrth | tail -n 1 | awk '{print $9}')\" | awk '{ for (i = 7; i <= NF; i++) printf $i \" \"; printf \"\\n\" }'"
                # command = "cd /home/abacus/kubequerysim/logs && tail -n 11 \"$(ls -lrth | head -n 60 | tail -n 1 | awk '{print $9}')\" | awk '{ for (i = 7; i <= NF; i++) printf $i \" \"; printf \"\\n\" }'"

                stdin, stdout, stderr = ssh_client.exec_command(command)
                output = stdout.read().decode('utf-8')
                errors = stderr.read().decode('utf-8')
                
                if output == "":
                    self.stack_obj.log.error("Please check the existence your Kubesim{}.log file in /home/abacus/kubequerysim/accuracy".format(port))
                    continue
                # print(output)
                # sys.exit()
            
                for i,data in enumerate(output.split("\n")):
                    # print(data)
                    if i in self.kubedata.keys():
                        # print(re.findall(r'\d+',data)[-1])
                        self.kubedata[i]+=int(re.findall(r'\d+',data)[-1])

            self.kube_data = {kube_index_map[key]: value for key, value in self.kubedata.items()}
            
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
        self.stack_obj.log.info(json.dumps(self.kube_data, indent=4)) 
        self.stack_obj.log.info(json.dumps(self.cvddata, indent=4))
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
                "Accuracy" : round(((self.actual_data[t]+1)/(self.expected_data[t]+1))*100 , 2)
            }
        #print(self.accuracy)
        df = pd.DataFrame(self.accuracy)
        df=df.T
        if df.empty : 
            self.stack_obj.log.warning("empty dataframe found for kubequery accuracies")
            self.stack_obj.log.info("\n%s",df)
            return None
        df = df.reset_index().rename(columns={'index': 'table'})
        self.stack_obj.log.info("\n%s",df)
        return_dict ={
                "format":"table","collapse":True,
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[]
                },
                "data":df.to_dict(orient="records")
            }
        return return_dict
    

