from pathlib import Path

#json_directory = ""
PROJECT_ROOT = Path(__file__).resolve().parent

tables = ['vulnerabilities_scanned_images', 'vulnerabilities','process_events','socket_events', 'process_file_events','dns_lookup_events','containers','docker_images','crio_images']


vsi_data = {"VulnerabilitiesScannedImages_Count": 2000, 
             "Vulnerabilities_Count": 30000000, 
             "Compliance_Count":0, 
             "ProcessEvents_Count": 4000000, 
             "SocketEvents_Count": 4000000, 
             "ProcessFileEvents_Count": 4000000, 
             "DnsLookupEvents_Count": 4000000, 
             "Containers_Count": 6000000,
             "DockerImages_Count": 6000000,
             "CrioImages_Count": 6000000}

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