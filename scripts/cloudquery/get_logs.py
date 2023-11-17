import paramiko
import os

class LOGScriptRunner:
    def __init__(self,load_name):
        self.simulators = ["s4simhost1a", "s4simhost1d", "s4simhost2b", "s4simhost2d", "s4simhost3b", "s4simhost3d", "s4simhost4b", "s4simhost4d", "s4simhost5b", "s4simhost5d", "s4simhost6b", "s4simhost6d"]
        # self.remote_logs_path = "~/multi-customer-cqsim/aws/logs"
        self.output_folder = "cloudquery/expected_logs"
        self.password = "abacus"

        path_mappings = {
            "AWS_MultiCustomer": "~/multi-customer-cqsim/aws/logs",
            "GCP_MultiCustomer": "~/multi-customer-cqsim/gcp/logs",
            "AWS_SingleCustomer": "~/cloud_query_sim/aws/logs",
        }

        self.remote_logs_path = path_mappings.get(load_name, "~/multi-customer-cqsim/aws/logs")

        
    def get_log(self):
        os.makedirs(self.output_folder, exist_ok=True)

        for simulator in self.simulators:
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





