import paramiko
import math
from concurrent.futures import ThreadPoolExecutor

class EVE_COUNTS:
    def __init__(self, variables):
        self.simulators = ["s4simhost1a", "s4simhost1d", "s4simhost2b", "s4simhost2d", "s4simhost3b", "s4simhost3d",
                           "s4simhost4b", "s4simhost4d", "s4simhost5b", "s4simhost5d", "s4simhost6b", "s4simhost6d"]
        self.load_name = variables['load_name']
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

    def run_remote_command(self, host, command):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(host, username=self.ssh_user, password=self.ssh_password)

        stdin, stdout, stderr = ssh_client.exec_command(command)

        result = stdout.read().decode().strip()
        ssh_client.close()
        return int(result)

    def analyze_logs(self, simulator, pattern, pattern2, pattern3):
        events_pattern = f'cd {self.remote_logs_path} && tail -10 "$(ls -trh | tail -1)" | awk \'{pattern}\''
        modified_events_pattern = f'cd {self.remote_logs_path} && tail -10 "$(ls -trh | tail -1)" | awk \'{pattern2}\''
        inventory_pattern = f'cd {self.remote_logs_path} && tail -10 "$(ls -trh | tail -1)" | awk \'{pattern3}\''

        total_sum = self.run_remote_command(simulator, events_pattern)
        total_sum2 = self.run_remote_command(simulator, modified_events_pattern)
        total_sum3 = self.run_remote_command(simulator, inventory_pattern)
        print(total_sum,total_sum3,total_sum2)
        return total_sum, total_sum2, total_sum3

    @staticmethod
    def format_in_millions(value):
        return "{:.2f} million".format(value / 1000000)

    def get_events_count(self):
        save_dict = {}
        if self.load_name in ["AWS_MultiCustomer", "AWS_SingleCustomer"]:
            events_pattern = '/Total no\\.of events happened till now:/ {sum+=$NF} END {print sum}'
            modified_events_pattern = '/Total no\\.of modified events happened till now:/ {sum+=$NF} END {print sum}'
            inventory_pattern = '/Total no\\.of inventory events happened till now:/ {sum+=$NF} END {print sum}'

        elif self.load_name == "GCP_MultiCustomer":
            events_pattern = '/Total no\.of events happened till now :/ {sum+=$NF} END {print sum}'
            modified_events_pattern = '/Total no\.of modified events happened during load:/ {sum+=$NF} END {print sum}'
            inventory_pattern = '/Total no\.of inventory events happened during load:/ {sum+=$NF} END {print sum}'

        with ThreadPoolExecutor(max_workers=len(self.simulators)) as executor:
            results = list(executor.map(self.analyze_logs, self.simulators, [events_pattern] * len(self.simulators), [modified_events_pattern] * len(self.simulators), [inventory_pattern] * len(self.simulators)))

        for total_sum, total_sum2, total_sum3 in results:
            self.total_sum += total_sum
            self.total_sum2 += total_sum2
            self.total_sum3 += total_sum3

        save_dict["Total inventory count"] = self.format_in_millions(self.total_sum3)
        save_dict["Total inventory count / hour"] = self.format_in_millions(self.total_sum3 / 12)

        save_dict["Total cloud trail events count"] = self.format_in_millions(self.total_sum2)
        save_dict["Total cloud trail events count / hour"] = self.format_in_millions(self.total_sum2 / 12)

        save_dict["Total count:"] = self.format_in_millions(self.total_sum)
        save_dict["Total count / hour:"] = self.format_in_millions(self.total_sum / 12)

        inventory_events_ratio = math.ceil(self.total_sum2 / self.total_sum3)
        save_dict["Ratio (inventory:events)"] = f"1:{inventory_events_ratio}"

        print(save_dict)
        return save_dict
