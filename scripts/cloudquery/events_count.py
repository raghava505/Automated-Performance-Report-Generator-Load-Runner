import paramiko
import math
import os
import json

class EVE_COUNTS:
    def __init__(self,variables):
        self.simulators = ["s4simhost1b", "s4simhost1d", "s4simhost2b", "s4simhost2d", "s4simhost3b", "s4simhost3d",
                  "s4simhost4b", "s4simhost4d", "s4simhost5b", "s4simhost5d", "s4simhost6b", "s4simhost6d"]
        self.load_name=variables['load_name']
        self.ssh_user = "abacus"
        self.ssh_password = "abacus"
        self.total_sum = 0
        self.total_sum2 = 0
        self.total_sum3 = 0

        path_mappings = {
            "AWS_MultiCustomer": "~/multi-customer-cqsim/aws/logs",
            "GCP_MultiCustomer": "~/multi-customer-cqsim/gcp/logs",
            "AWS_SingleCustomer": "~/cloud_query_sim/aws/logs",
        }

        self.remote_logs_path = path_mappings.get(self.load_name, "~/multi-customer-cqsim/aws/logs")

    def run_remote_command_aws(self, host, pattern):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(host, username=self.ssh_user, password=self.ssh_password)

        command = f'cd {self.remote_logs_path} && tail -10 "$(ls -trh | tail -1)" | awk \'{pattern}\''
        stdin, stdout, stderr = ssh_client.exec_command(command)

        result = stdout.read().decode().strip()
        ssh_client.close()
        return int(result)
    
    def run_remote_command_gcp(self, host, pattern):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(host, username=self.ssh_user, password=self.ssh_password)

        command = f'cd {self.remote_logs_path} && tail -100 "$(ls -trh | tail -1)" | awk \'{pattern}\''
        stdin, stdout, stderr = ssh_client.exec_command(command)

        result = stdout.read().decode().strip()
        ssh_client.close()
        return int(result)

    def analyze_logs_aws(self, save_dict):
        for simulator in self.simulators:
            events_pattern = '/Total no\\.of events happened till now:/ {sum+=$NF} END {print sum}'
            modified_events_pattern = '/Total no\\.of modified events happened till now:/ {sum+=$NF} END {print sum}'
            inventory_pattern = '/Total no\\.of inventory events happened till now:/ {sum+=$NF} END {print sum}'

            self.total_sum += self.run_remote_command_aws(simulator, events_pattern)
            self.total_sum2 += self.run_remote_command_aws(simulator, modified_events_pattern)
            self.total_sum3 += self.run_remote_command_aws(simulator, inventory_pattern)

            save_dict["Total inventory count"] = self.format_in_millions(self.total_sum3)
            save_dict["Total inventory count / hour"] = self.format_in_millions(self.total_sum3 / 12)
            
            save_dict["Total cloud trail events count"] = self.format_in_millions(self.total_sum2)
            save_dict["Total cloud trail events count / hour"] = self.format_in_millions(self.total_sum2 / 12)
            
            save_dict["Total count:"] = self.format_in_millions(self.total_sum)
            save_dict["Total count / hour:"] = self.format_in_millions(self.total_sum / 12)
            
            inventory_events_ratio = math.ceil(self.total_sum3 / self.total_sum2)
            save_dict["Ratio (inventory:events)"] = f"1:{inventory_events_ratio}"

            return save_dict


    def analyze_logs_gcp(self, save_dict):
        for simulator in self.simulators:
            events_pattern = '/Total no\.of events happened till now :/ {sum+=$NF} END {print sum}'
            modified_events_pattern = '/Total no\.of modified events happened during load:/ {sum+=$NF} END {print sum}'
            inventory_pattern = '/Total no\.of inventory events happened during load:/ {sum+=$NF} END {print sum}'

            self.total_sum += self.run_remote_command_gcp(simulator, events_pattern)
            self.total_sum2 += self.run_remote_command_gcp(simulator, modified_events_pattern)
            self.total_sum3 += self.run_remote_command_gcp(simulator, inventory_pattern)

            save_dict["Total inventory count"] = self.format_in_millions(self.total_sum3)
            save_dict["Total inventory count / hour"] = self.format_in_millions(self.total_sum3 / 12)
            
            save_dict["Total cloud log events count"] = self.format_in_millions(self.total_sum2)
            save_dict["Total cloud log events count / hour"] = self.format_in_millions(self.total_sum2 / 12)
            
            save_dict["Total count:"] = self.format_in_millions(self.total_sum)
            save_dict["Total count / hour:"] = self.format_in_millions(self.total_sum / 12)
            
            inventory_events_ratio = math.ceil(self.total_sum3 / self.total_sum2)
            save_dict["Ratio (inventory:events)"] = f"1:{inventory_events_ratio}"

            return save_dict

    @staticmethod
    def format_in_millions(value):
        return "{:.2f} million".format(value / 1000000)

    def get_events_count(self):
        save_dict={}
        if(self.load_name=="AWS_MultiCustomer" or self.load_name=="AWS_SingleCustomer"):
            save_dict = self.analyze_logs_aws(save_dict)
        elif(self.load_name=="GCP_MultiCustomer"):
            save_dict = self.analyze_logs_gcp(save_dict)

        return save_dict
        






