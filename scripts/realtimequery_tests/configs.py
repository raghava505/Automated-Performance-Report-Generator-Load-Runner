
domain = 'longevity'
URL = 'https://{}{}'

GO_API_PORT = 9009
USER = 'donkey'
HOME_PATH = '/home/donkey/'

# protectum_stack 
pnodes_list = ['protectum-pnode11a', 'protectum-pnode2a', 'protectum-pnode3a']
dnodes_list = ['protectum-dnode1a', 'protectum-dnode2a', 'protectum-dnode3a']
pgnodes_list = ['protectum-configdb1a', 'protectum-configdb2a', 'protectum-configdb3a']
monitor_node_name = 'protectum-monitor1a'
nodes_list = pnodes_list + dnodes_list + pgnodes_list
protecum_sim =['protectum-simulator1a']

# #protectu_stack
# pnodes_list = ['baseprotectu-pnode1a','baseprotectu-pnode2a','baseprotectu-pnode3a']
# dnodes_list =  ['baseprotectu-dnode4a','baseprotectu-dnode5a','baseprotectu-dnode6a']
# pgnodes_list =['baseprotectu-configdb1a','baseprotectu-configdb2a','baseprotectu-configdb3a']
# monitor_node_name =  'baseprotectu-monitor1a'
# nodes_list = pnodes_list + dnodes_list + pgnodes_list

disk_per = 25
pg_lag_threshold=1000

account_status_api = {}
account_status_api['aws'] = 'https://{}{}/public/api/customers/{}/cloud/aws/status?filters=%7B%22organizationId%22%3A%7B%22equals%22%3Anull%7D%7D&hideServices=true'
account_status_api['gcp'] = 'https://{}{}/public/api/customers/{}/cloud/gcp/status?filters=%7B%22organizationId%22%3A%7B%22equals%22%3Anull%7D%7D&hideServices=true'
account_status_api['azure'] = 'https://{}{}/public/api/customers/{}/cloud/azure/status?filters=%7B%22organizationId%22%3A%7B%22equals%22%3Anull%7D%7D&hideServices=true'
data_collection_api = 'https://{}{}/public/api/customers/{}/cloud/aws/dashboards/dashboardQuery?refresh=true'
new_dc_api= 'https://{}{}/public/api/customers/{}/cloud/aws/dashboards/dashboardQuery?queryJobId='
payload_data_collection = {"apiName":"lastIngestedTimeForTable","uptTableName":"aws_cloudtrail_events","inactivityDurationMinutes":"300"}
query_api = 'https://{}{}/public/api/customers/{}/queryJobs'


gq_payload = {"queryId":"1cbde4db-404a-45e6-baac-0d9032c2cc0c","query":"select * from processes where upt_day = 20231025 limit 10\n\n\n\n\n\n\n\n\n\n","type":"global","filters":{},"parameters":[],"parameterValues":{},"agentType":"asset"}
result_gq_api ='https://{}{}/public/api/customers/{}/queryJobs/{}/results'
build_api = 'https://{}{}/public/api/version'

rq_payload1 = {"query":"select * from processes","type":"realtime","filters":{"live":True,"hostName":"REALTIME"},"parameters":[],"parameterValues":{},"agentType":"asset"}
rq_payload2 = {"query":"select * from compliance","type":"realtime","filters":{"live":True,"hostName":"REALTIME"},"parameters":[],"parameterValues":{},"agentType":"asset"}
rq_payload3 = {"query":"select * from upt_api_audit_logs","type":"realtime","filters":{"live":True,"hostName":"REALTIME"},"parameters":[],"parameterValues":{},"agentType":"asset"}
rq_payload4 = {"query":"select count(*) as count from vulnerabilities","type":"realtime","filters":{"live":True,"hostName":"REALTIME"},"parameters":[],"parameterValues":{},"agentType":"asset"}
rq_payloads = [rq_payload1,rq_payload2,rq_payload3,rq_payload4]

tables = ['dns_lookup_events' , 'process_events' ,'process_open_files','process_open_sockets','processes']

rt_timeout = 600
rt_sims = ['192.168.149.56','192.168.149.57'] 
rtsim_user = 'abacus'
user= 'abacus'
prestonode_ip ='192.168.148.11'
prestonode_user= 'abacus'
rtuser_password= 'abacus'
presto_password = 'abacus'
rtinstance_count = 15
clients_in_instance = 100
assets = rtinstance_count*clients_in_instance * len(rt_sims)
buffer_asset_count = 0.9 * assets
records_per_asset = 500
total_recordes = assets * records_per_asset
pgrt_user = 'abacus'
pgrt_hostip = '192.168.150.14'
pgrt_password = 'abacus'



