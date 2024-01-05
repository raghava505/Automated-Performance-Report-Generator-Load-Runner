import paramiko
import pandas as pd
import os


def fetch_and_extract_csv(remote_csv_path,reports_node_ip,prom_com_obj):
    if remote_csv_path == None or remote_csv_path == "":
        return None
    
    current_directory = os.path.dirname(os.path.abspath(__file__))
    relative_path = "api_load.csv"
    local_csv_path = os.path.join(current_directory, relative_path)
    
    try:
        # Use SCP to copy the file from the remote host to the local machine
        with paramiko.Transport((reports_node_ip, 22)) as transport:
            transport.connect(username=prom_com_obj.abacus_username, password=prom_com_obj.abacus_password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.get(remote_csv_path, local_csv_path)
            print(f"Fetched csv file successfully: {remote_csv_path}")
            sftp.close()

        df = pd.read_csv(local_csv_path)
        load_dict = df.to_dict(orient='records')
        # print("Printing API Load data")
        # print(api_load_dict)
        print("Extracting csv file...")
        return load_dict 
    
    except Exception as e:
        print(e)
        return None

def fetch_and_save_pdf(remote_pdf_path,reports_node_ip,prom_com_obj , local_pdf_path):
    if remote_pdf_path == None or remote_pdf_path == "":
        return None
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Use SCP to copy the file from the remote host to the local machine
        with paramiko.Transport((reports_node_ip, 22)) as transport:
            transport.connect(username=prom_com_obj.abacus_username, password=prom_com_obj.abacus_password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.get(remote_pdf_path, local_pdf_path)
            print(f"Fetched PDF file successfully: {remote_pdf_path}")
            sftp.close()
    
    except Exception as e:
        print("Error while fetching the pdf : " ,e)