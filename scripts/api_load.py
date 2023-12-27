import paramiko
import pandas as pd
import os


class API_LOAD:
    def fetch_api_load_dict(self, api_load_csv_file_path,api_load_reports_node_ip,prom_com_obj):
        if api_load_csv_file_path == None or api_load_csv_file_path == "":
            return None
        
        remote_csv_path = api_load_csv_file_path

        # Assuming this code is in a script in the same directory as the CSV file
        current_directory = os.path.dirname(os.path.abspath(__file__))
        relative_path = "api_load.csv"
        local_csv_path = os.path.join(current_directory, relative_path)
        
        try:
            # Use SCP to copy the file from the remote host to the local machine
            with paramiko.Transport((api_load_reports_node_ip, 22)) as transport:
                transport.connect(username=prom_com_obj.abacus_username, password=prom_com_obj.abacus_password)
                sftp = paramiko.SFTPClient.from_transport(transport)
                sftp.get(remote_csv_path, local_csv_path)
                sftp.close()

            df = pd.read_csv(local_csv_path)
            api_load_dict = df.to_dict(orient='records')
            print("Printing API Load data")
            print(api_load_dict)
            return api_load_dict 
        
        except Exception as e:
            print(e)
            return None

# output = API_LOAD().fetch_api_load_dict(configuration().api_loads_folder_path + "2023-12-19 12:20.csv")
# print(output)