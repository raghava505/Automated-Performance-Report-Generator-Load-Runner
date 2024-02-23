import paramiko
import os
import shutil

class LOGScriptRunner:
    def __init__(self):
        self.simulators1 = ["s4simhost1a", "s4simhost1d", "s4simhost2b", "s4simhost2d", "s4simhost3b", "s4simhost3d", "s4simhost4b", "s4simhost4d", "s4simhost5b", "s4simhost5d", "s4simhost6b", "s4simhost6d"]
        self.simulators2 = ["long-aws-sim1", "long-aws-sim2"]
        self.simulators3 = ["long-gcp-sim1", "long-gcp-sim2"]
        self.azure_simulators = ["long-azure-sim1"]
        self.azure_s18sims = ["s18sim1a"]
        self.output_folder = "cloudquery/expected_logs"
        self.password = "abacus"

        self.path_mappings = {
            "Azure_MultiCustomer": "~/cloud_query_sim/azure_multi/logs",
            "AWS_MultiCustomer": "~/multi_customer_attackpath/aws/logs",
            "GCP_MultiCustomer": "~/multi-customer-cqsim/gcp/logs",
            "AWS_SingleCustomer": "~/cloud_query_sim/aws/logs",
        }

        self.remote_logs_path = None

        
    def get_log(self,simulators,load_name):
        if os.path.exists(self.output_folder):
            shutil.rmtree(self.output_folder)

        os.makedirs(self.output_folder)
        self.remote_logs_path = self.path_mappings.get(load_name, "~/multi_customer_attackpath/aws/logs")
        for simulator in simulators:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            try:
                
                ssh.connect(simulator, username="abacus", password=self.password)

                
                command = f"cd {self.remote_logs_path}; tail -1 $(ls -trh | tail -1) | grep -oP 'printlogs:\s+\K.*'"
                stdin, stdout, stderr = ssh.exec_command(command)
                output = stdout.read().decode('utf-8').strip()

                ssh.close()
                json_data = output.replace("'", '"')

                with open(f"{self.output_folder}/{simulator}_dict.json", "w") as file:
                    file.write(json_data)

                print(f"Extracted dictionary saved for {simulator}")
            except Exception as e:
                print(f"Error connecting to {simulator}: {str(e)}")

        print("Extraction and saving process completed")





