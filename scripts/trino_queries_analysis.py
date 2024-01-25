import json
import paramiko
import pandas as pd
from io import StringIO

#configdb_command = "PGPASSWORD=pguptycs psql -h {} -U uptycs -p 5432 -d configdb -c \"select read_password from customer_database where database_name='upt_{}';\"".format(remote_host,self.stack_details['domain'])

class TRINO_ANALYSE:
    def __init__(self,start_utc_str,end_utc_str,prom_con_obj):

        self.test_env_file_path=prom_con_obj.test_env_file_path
        with open(self.test_env_file_path, 'r') as file:
            self.stack_details = json.load(file)
        self.start_utc_str=start_utc_str
        self.end_utc_str=end_utc_str
        self.remote_username = prom_con_obj.abacus_username
        self.remote_password  = prom_con_obj.abacus_password
        self.dnode = self.stack_details['dnodes'][0]

    def fetch_trino_results(self,commands):
        save_dict={}
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(self.dnode, 22, self.remote_username, self.remote_password)
            for heading,value in commands.items():
                raw_command=value['query']
                columns=value['columns']
                command = raw_command.replace("<start_utc_str>",self.start_utc_str).replace( "<end_utc_str>", self.end_utc_str)
                complete_command = f"sudo -u monkey TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --insecure --server https://localhost:5665 --schema upt_system --user uptycs --catalog uptycs --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/etc/presto/presto.jks --execute \"{command}\""
                print(f"Executing '{heading}' command in {self.dnode} : " )
                print(complete_command)
                stdin, stdout, stderr = ssh_client.exec_command(complete_command)
                output = stdout.read().decode('utf-8')
                errors = stderr.read().decode('utf-8')
                if errors:
                    print("Errors:")
                    print(errors)
                stringio = StringIO(output)
                df = pd.read_csv(stringio, header=None, names=columns)
                print(df)
                save_dict[heading] = df.to_dict(orient='records')

        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            ssh_client.close()
        return save_dict
    
# if __name__=='__main__':
#     print("Testing trino queries analysis ...")
#     from settings import configuration
#     from parent_load_details import parent
#     calc = TRINO_ANALYSE(" 2024-01-24 01:25"," 2024-01-24 11:25",prom_con_obj=configuration('s1_nodes.json'))
#     trino_queries = calc.fetch_trino_results(parent.trino_details_commands)
#     print(trino_queries)