import paramiko
import math
import socket
from concurrent.futures import ThreadPoolExecutor

class EVE_COUNTS:
    def __init__(self, variables,stack_obj):
        self.stack_obj=stack_obj
        self.simulators1 = ["s4simhost1a","s4simhost1c", "s4simhost1d", "s4simhost2a","s4simhost2b","s4simhost2c", "s4simhost2d", "s4simhost3a","s4simhost3b", "s4simhost3c"]
        self.simulators2 = ["long-aws-sim1", "long-aws-sim2"]
        self.simulators3 = ["long-gcp-sim1", "long-gcp-sim2"]
        self.azure_s18sims = ["s18sim1a"]
        self.load_name = variables['load_name']
        self.load_type = variables['load_type']
        self.ssh_user = "abacus"
        self.ssh_password = "abacus"
        self.total_sum = 0
        self.total_sum2 = 0
        self.total_sum3 = 0

        self.path_mappings = {
            "Azure_MultiCustomer": "~/cloud_query_sim/azure_multi/logs",
            "AWS_MultiCustomer": "~/multi_customer_attackpath/aws/logs",
            "GCP_MultiCustomer": "~/multi-customer-cqsim/gcp/logs",
            "AWS_SingleCustomer": "~/cloud_query_sim/aws_sts_test/logs",
        }

        self.remote_logs_path = self.path_mappings.get(self.load_name, "~/multi_customer_attackpath/aws/logs")

    def run_remote_command(self, host, command):
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(host, username=self.ssh_user, password=self.ssh_password, timeout=30) 

            stdin, stdout, stderr = ssh_client.exec_command(command)

            result = stdout.read().decode().strip()
            ssh_client.close()

            return int(result)
        except (paramiko.SSHException, socket.timeout) as e:
            self.stack_obj.log.error(f"Error connecting to {host}: {e}")
            return 0
    def analyze_logs(self, simulator, pattern, pattern2, pattern3):
        events_pattern = f'cd {self.remote_logs_path} && tail -10 "$(ls -trh | tail -1)" | awk \'{pattern}\''
        modified_events_pattern = f'cd {self.remote_logs_path} && tail -10 "$(ls -trh | tail -1)" | awk \'{pattern2}\''
        inventory_pattern = f'cd {self.remote_logs_path} && tail -10 "$(ls -trh | tail -1)" | awk \'{pattern3}\''

        total_sum = self.run_remote_command(simulator, events_pattern)
        total_sum2 = self.run_remote_command(simulator, modified_events_pattern)
        total_sum3 = self.run_remote_command(simulator, inventory_pattern)
        self.stack_obj.log.info(total_sum,total_sum3,total_sum2,simulator)
        return total_sum, total_sum2, total_sum3

    @staticmethod
    def format_in_millions(value):
        return "{:.2f} million".format(value / 1000000)

    def get_events_count(self):
        save_dict = {}

        if self.load_name in ["AWS_MultiCustomer", "AWS_SingleCustomer","Azure_MultiCustomer"]:
            events_pattern = '/Total no\\.of events happened till now:/ {sum+=$NF} END {print sum}'
            modified_events_pattern = '/Total no\\.of modified events happened till now:/ {sum+=$NF} END {print sum}'
            inventory_pattern = '/Total no\\.of inventory events happened till now:/ {sum+=$NF} END {print sum}'

        elif self.load_name == "GCP_MultiCustomer":
            events_pattern = '/Total no\\.of events happened till now :/ {sum+=$NF} END {print sum}'
            modified_events_pattern = '/Total no\\.of modified events happened during load:/ {sum+=$NF} END {print sum}'
            inventory_pattern = '/Total no\\.of inventory events happened during load:/ {sum+=$NF} END {print sum}'

        with ThreadPoolExecutor(max_workers=len(self.simulators1)) as executor:
            if self.load_name in ["Osquery(multi)_CloudQuery(aws_gcp_multi)", "GoldenTest"]:
                
                events_pattern_aws = '/Total no\\.of events happened till now:/ {sum+=$NF} END {print sum}'
                modified_events_pattern_aws = '/Total no\\.of modified events happened till now:/ {sum+=$NF} END {print sum}'
                inventory_pattern_aws = '/Total no\\.of inventory events happened till now:/ {sum+=$NF} END {print sum}'

                events_pattern_gcp = '/Total no\\.of events happened till now :/ {sum+=$NF} END {print sum}'
                modified_events_pattern_gcp = '/Total no\\.of modified events happened during load:/ {sum+=$NF} END {print sum}'
                inventory_pattern_gcp = '/Total no\\.of inventory events happened during load:/ {sum+=$NF} END {print sum}'

                results_aws = list(executor.map(self.analyze_logs,  self.simulators2, [events_pattern_aws] * len(self.simulators2), [modified_events_pattern_aws] * len(self.simulators2), [inventory_pattern_aws] * len(self.simulators2)))
                self.remote_logs_path = self.path_mappings.get("GCP_MultiCustomer", "~/multi-customer-cqsim/aws/logs")
                results_gcp = list(executor.map(self.analyze_logs,  self.simulators3, [events_pattern_gcp] * len(self.simulators3), [modified_events_pattern_gcp] * len(self.simulators3), [inventory_pattern_gcp] * len(self.simulators3)))
            
            elif self.load_name == "Azure_MultiCustomer":
                results = list(executor.map(self.analyze_logs,  self.azure_s18sims, [events_pattern] * len(self.azure_s18sims), [modified_events_pattern] * len(self.azure_s18sims), [inventory_pattern] * len(self.azure_s18sims)))
            else:
                results = list(executor.map(self.analyze_logs,  self.simulators1, [events_pattern] * len(self.simulators1), [modified_events_pattern] * len(self.simulators1), [inventory_pattern] * len(self.simulators1)))

        if self.load_name in ["Osquery(multi)_CloudQuery(aws_gcp_multi)", "GoldenTest"]:
            
            total_sum_aws = sum(result[0] for result in results_aws)
            total_sum2_aws = sum(result[1] for result in results_aws)
            total_sum3_aws = sum(result[2] for result in results_aws)

            total_sum_gcp = sum(result[0] for result in results_gcp)
            total_sum2_gcp = sum(result[1] for result in results_gcp)
            total_sum3_gcp = sum(result[2] for result in results_gcp)

            save_dict["AWS"] = {
                "Total inventory count": self.format_in_millions(total_sum3_aws),
                "Total inventory count / hour" : self.format_in_millions(total_sum3_aws / 12),
                "Total cloud trail events count": self.format_in_millions(total_sum2_aws),
                "Total cloud trail events count / hour" : self.format_in_millions(total_sum2_aws / 12),
                "Total count": self.format_in_millions(total_sum_aws),
                "Total count / hour:" : self.format_in_millions(total_sum_aws / 12),
                "Ratio (inventory:events)": f"1:{math.ceil(total_sum2_aws / total_sum3_aws)}"
            }

            save_dict["GCP"] = {
                "Total inventory count": self.format_in_millions(total_sum3_gcp),
                "Total inventory count / hour" : self.format_in_millions(total_sum3_gcp / 12),
                "Total cloud trail events count": self.format_in_millions(total_sum2_gcp),
                "Total cloud trail events count / hour" : self.format_in_millions(total_sum2_gcp / 12),
                "Total count": self.format_in_millions(total_sum_gcp),
                "Total count / hour:" : self.format_in_millions(total_sum_gcp / 12),
                "Ratio (inventory:events)": f"1:{math.ceil(total_sum2_gcp / total_sum3_gcp)}"
            }
        else:
            
            for total_sum, total_sum2, total_sum3 in results:
                self.total_sum += total_sum
                self.total_sum2 += total_sum2
                self.total_sum3 += total_sum3

            if self.load_name in ["AWS_MultiCustomer", "AWS_SingleCustomer"]:
                x="AWS"
            elif self.load_name == "GCP_MultiCustomer":
                x="GCP"
            elif self.load_name == "Azure_MultiCustomer":
                x="Azure"

            save_dict[x] = {
            "Total inventory count": self.format_in_millions(self.total_sum3),
            "Total inventory count / hour": self.format_in_millions(self.total_sum3 / 12),
            "Total cloud trail events count": self.format_in_millions(self.total_sum2),
            "Total cloud trail events count / hour": self.format_in_millions(self.total_sum2 / 12),
            "Total count": self.format_in_millions(self.total_sum),
            "Total count / hour": self.format_in_millions(self.total_sum / 12),
            "Ratio (inventory:events)": f"1:{math.ceil(self.total_sum2 / self.total_sum3)}"
            }

        self.stack_obj.log.info(save_dict)
        return save_dict
