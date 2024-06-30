import paramiko
from config_vars import *
class kafka_topics:
    def __init__(self,stack_obj):
        self.local_script_path = f'{ROOT_PATH}/scripts/kafka_topics.py'
        self.host = stack_obj.execute_kafka_topics_script_in
        self.stack_obj = stack_obj

    def add_topics_to_report(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.stack_obj.log.info(f"Executing kafka topics script in host {self.host}")
            ssh.connect(self.host, SSH_PORT, ABACUS_USERNAME, ABACUS_PASSWORD)
            sftp = ssh.open_sftp()
            # remote_script_path = f'{self.remote_directory}/get_kafka_topics.py'
            remote_script_path="get_kafka_topics.py"
            sftp.put(self.local_script_path, remote_script_path)
            self.stack_obj.log.info(f"The script '{remote_script_path}' has been uploaded to the remote server.")
            remote_command = f'python3 {remote_script_path}'
            pip_command="pip install kafka-python"
            stdin, stdout, stderr = ssh.exec_command(pip_command)
            self.stack_obj.log.info(stdout.read().decode('utf-8'))
            stdin, stdout, stderr = ssh.exec_command(remote_command)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            output_list = [line for line in output.split('\n') if line.strip()]
            self.stack_obj.log.info(f"Kafka topics found are : {output_list}")
            ssh.close()
            
            return {"format":"list",
                        "schema":{},
                        "data":output_list
                        }
            
        except Exception as e:
            self.stack_obj.log.error(f"Error while fetching kafka topics : {str(e)}")
            ssh.close()
            return None
