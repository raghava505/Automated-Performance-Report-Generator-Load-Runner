from pathlib import Path

#json_directory = ""
PROJECT_ROOT = Path(__file__).resolve().parent

tables = ['vulnerabilities_scanned_images', 'vulnerabilities','process_events','socket_events', 'process_file_events','dns_lookup_events','containers','docker_images','crio_images']


vsi_data = {"VulnerabilitiesScannedImages_Count":0, 
             "Vulnerabilities_Count":0, 
             "Compliance_Count":0, 
             "ProcessEvents_Count":0, 
             "SocketEvents_Count":0, 
             "ProcessFileEvents_Count":0, 
             "DnsLookupEvents_Count":0, 
             "Containers_Count":0,
             "DockerImages_Count":0,
             "CrioImages_Count":0}

asset_count = 100
# sim_nodes = ['s13sim1','s13sim2','s13sim3','s13sim4']

ports = [28001 ,28002]
# In Minutes
deltaTime = 70 

key_mapping = {
    'VulnerabilitiesScannedImages_Count': 'vulnerabilities_scanned_images',
    'Vulnerabilities_Count': 'vulnerabilities',
    'Compliance_Count': 'compliance',
    'ProcessEvents_Count': 'process_events',
    'SocketEvents_Count': 'socket_events',
    'ProcessFileEvents_Count': 'process_file_events',
    'DnsLookupEvents_Count': 'dns_lookup_events',
    'Containers_Count': 'containers',
    "DockerImages_Count":"docker_images",
    "CrioImages_Count":"crio_images"}