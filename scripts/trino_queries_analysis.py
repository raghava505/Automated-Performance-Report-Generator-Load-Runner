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
                integer_columns = df.select_dtypes(include='int').columns
                string_columns = df.select_dtypes(include='object').columns
                print("Integer Columns:", list(integer_columns))
                print("String Columns:", list(string_columns))
                new_row=dict([(int_col,df[int_col].sum()) for int_col in integer_columns])
                new_row.update(dict([(str_col,"TOTAL") for str_col in string_columns]))
                df = df._append(new_row, ignore_index=True)
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
#     from datetime import datetime, timedelta
#     import pytz
#     from parent_load_details import parent
#     format_data = "%Y-%m-%d %H:%M"

#     start_time_str = "2024-01-24 03:58"
#     hours=12

#     start_time = datetime.strptime(start_time_str, format_data)
#     end_time = start_time + timedelta(hours=hours)
#     end_time_str = end_time.strftime(format_data)

#     ist_timezone = pytz.timezone('Asia/Kolkata')
#     utc_timezone = pytz.utc

#     start_ist_time = ist_timezone.localize(datetime.strptime(start_time_str, '%Y-%m-%d %H:%M'))
#     start_timestamp = int(start_ist_time.timestamp())
#     start_utc_time = start_ist_time.astimezone(utc_timezone)
#     start_utc_str = start_utc_time.strftime(format_data)

#     end_ist_time = ist_timezone.localize(datetime.strptime(end_time_str, '%Y-%m-%d %H:%M'))
#     end_timestamp = int(end_ist_time.timestamp())
#     end_utc_time = end_ist_time.astimezone(utc_timezone)
#     end_utc_str = end_utc_time.strftime(format_data)
#     calc = TRINO_ANALYSE(start_utc_str,end_utc_str,prom_con_obj=configuration('longevity_nodes.json'))
#     trino_queries = calc.fetch_trino_results(parent.trino_details_commands)
#     print(trino_queries)