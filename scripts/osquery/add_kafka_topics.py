import paramiko
import json

class kafka_topics:
    def __init__(self,prom_con_obj):
        self.local_script_path = f'{prom_con_obj.ROOT_PATH}/scripts/kafka_topics.py'
        self.host = prom_con_obj.execute_kafka_topics_script_in
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password
        # self.remote_directory = f'/home/{self.username}'

    def add_topics_to_report(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            print(f"Executing kafka topics script in host {self.host}")
            ssh.connect(self.host, self.port, self.username, self.password)
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