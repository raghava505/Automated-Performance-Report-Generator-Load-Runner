import requests
from datetime import datetime
import json
import paramiko

class TRINO:
    def __init__(self,curr_ist_start_time,curr_ist_end_time,prom_con_obj):
        self.curr_ist_start_time=curr_ist_start_time
        self.curr_ist_end_time=curr_ist_end_time
        
        self.test_env_file_path=prom_con_obj.test_env_file_path
        self.PROMETHEUS = prom_con_obj.prometheus_path
        self.API_PATH = prom_con_obj.prom_point_api_path
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password

        with open(self.test_env_file_path, 'r') as file:
            self.stack_details = json.load(file)

            
    def trino_queries(self):
        save_dict = {}
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        n = self.stack_details['dnodes'][0]

        ist_time_format = '%Y-%m-%d %H:%M'
        start_time_utc = (datetime.strptime(self.curr_ist_start_time, ist_time_format))
        end_time_utc = (datetime.strptime(self.curr_ist_end_time, ist_time_format))
        

        try:
            ssh_client.connect(n, 22, "abacus", "abacus")
            command = f"sudo -u monkey TRINO_PASSWORD={self.stack_details['trino_password']} /opt/uptycs/cloud/utilities/trino-cli --insecure --server https://localhost:5665 --schema upt_system --user upt_read_{self.stack_details['domain']} --catalog uptycs --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/etc/presto/presto.jks --execute \"select source,query_operation,count(*) from presto_query_logs where upt_time > timestamp '{start_time_utc}' and upt_time< timestamp '{end_time_utc}' group by source,query_operation order by source;\""

            stdin, stdout, stderr = ssh_client.exec_command(command)

            output = stdout.read().decode('utf-8')
            errors = stderr.read().decode('utf-8')

            if errors:
                print("Errors:")
                print(errors)

            
            lines = output.strip().split('\n')
            
            
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    key1 = parts[0].strip('"')
                    key2 = parts[1].strip('"')
                    value = int(parts[2].strip('"'))
                    
                    
                    if key1 not in save_dict:
                        save_dict[key1] = {}
                    save_dict[key1][key2] = value

        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            ssh_client.close()

        
        return save_dict


    def save(self,_ ,current_build_data):
        save_dict=_
        current_build_data[f"Trino Queries"] = save_dict
        return current_build_data
    
    def make_calculations(self):
        
        current_build_data={}
        current_build_data=self.save(self.trino_queries(),current_build_data)

        return current_build_data
    


