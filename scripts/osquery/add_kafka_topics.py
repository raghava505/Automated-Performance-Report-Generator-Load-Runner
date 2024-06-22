import paramiko
from config_vars import *
class kafka_topics:
    def __init__(self,host):
        self.local_script_path = f'{ROOT_PATH}/scripts/kafka_topics.py'
        self.host = host

    def add_topics_to_report(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            print(f"Executing kafka topics script in host {self.host}")
            ssh.connect(self.host, ssh_port, abacus_username, abacus_password)
            sftp = ssh.open_sftp()
            # remote_script_path = f'{self.remote_directory}/get_kafka_topics.py'
            remote_script_path="get_kafka_topics.py"
            sftp.put(self.local_script_path, remote_script_path)
            print(f"The script '{remote_script_path}' has been uploaded to the remote server.")
            remote_command = f'python3 {remote_script_path}'
            pip_command="pip install kafka-python"
            stdin, stdout, stderr = ssh.exec_command(pip_command)
            print(stdout.read().decode('utf-8'))
            stdin, stdout, stderr = ssh.exec_command(remote_command)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            output_list = [line for line in output.split('\n') if line.strip()]
            print("Kafka topics found are : " , output_list)
        except Exception as e:
            print("Error while fetching kafka topics : " , str(e))
            return []
        finally:
            ssh.close()
            return output_list