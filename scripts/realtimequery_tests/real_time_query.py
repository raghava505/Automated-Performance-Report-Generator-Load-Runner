from typing import ItemsView
from api_func import *
from log_config import *
from validation import TestResult
from configs import *
from pathlib import Path
import sys
from datetime import datetime, timedelta
from connect_nodes import Host
import re 
import pymongo



PROJECT_ROOT = Path(__file__).resolve().parent

LOG_PATH = str(PROJECT_ROOT) + "/logs"


def add_time(curr_time, hours=0, minutes=0, seconds=0):
    time_to_add = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    new_time = datetime.combine(datetime.today(), curr_time) + time_to_add
    return new_time.time()


def subtract_times(time1, time2):
    dt1 = datetime.combine(datetime.today(), time1)
    dt2 = datetime.combine(datetime.today(), time2)
    result_time = dt1 - dt2
    return result_time

def kill_existing_processes(hostname,rtsim_user,user,process_name,password):
    # print(hostname)
    # print(user)
    # print(password)
    kill_endpoints = "killall {}".format(process_name)
    # kill_endpoints = "sudo -u {} sh -c 'cd /home/{}/go_http_real_time/go_http && sudo killall {}' 2>&1 ".format(rtsim_user,rtsim_user,process_name)
    h = Host(hostname, user, '', password)
    for i in range(5):
        try :
            h.execute_command(kill_endpoints)
        except Exception: 
            pass

    log.info('processes got deleted')

def query_configd(hostname,user,password,operation):
    h = Host(hostname,user, '', password)
    if operation == 'd':
        formatted_command =  (
    "sudo docker exec postgres-configdb bash -c "
    """'PGPASSWORD=pguptycs psql -U postgres configdb -c "delete from assets WHERE host_name LIKE '\\''%REALTIME%'\\''"'"""
    )
    if operation == 'c':
        formatted_command =  (
    "sudo docker exec postgres-configdb bash -c "
    """'PGPASSWORD=pguptycs psql -U postgres configdb -c "SELECT COUNT(*) FROM assets WHERE host_name LIKE '\\''%REALTIME%'\\''"'"""
    )
    return h.execute_command(formatted_command)
    

def run_instance(hostname,rtsim_user,user,process_name,password):
    
    script = "sudo -u {} bash -c 'cd /home/{}/go_http_real_time/go_http && ./BringUpInstancesNewformat.sh' ".format(rtsim_user,rtsim_user)
    h = Host(hostname, user, '', password)
    h.execute_command(script)
    count = "sudo -u {} sh -c 'cd /home/{}/go_http_real_time/go_http && ps -ef | grep {} -c' ".format(rtsim_user,rtsim_user,process_name)
    check_time= 0 
    while check_time <= rt_timeout :
        output = h.execute_command(count)
        log.info('curent process count {}'.format(output.strip()))
        if int(output.strip()) == rtinstance_count+3:
            time.sleep(10)
            break
        time.sleep(10)
        check_time = check_time + 10

    if int(output.strip())  != rtinstance_count+3 :
        test_result.update_error ("processes are failing, current processes count : {}".format(output.strip() ), skip_test = True)
final_data_to_save ={}

def query(rq_payload,l) :
    current_time = datetime.utcnow().time()

    current_datetime_utc = datetime.utcnow()
    formatted_cdatetime = current_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')
    c_time = str(formatted_cdatetime)
    api_path = str(PROJECT_ROOT)  + '/API_keys/api_key_{}.json'.format(domain)
    stack_keys = open_js_safely(api_path)
    mrealtime_query_api = query_api.format(stack_keys['domain'],stack_keys['domainSuffix'],stack_keys['customerId'])

    output = post_api(api_path,mrealtime_query_api,rq_payload)
    query_job_id1 = output['id']
    log.info('Query{} job id :{}'.format(l,query_job_id1))
    actual_assets=0
    if output['status'] != 'FINISHED':
        while output['status'] not in ['FINISHED', 'ERROR']:        
            new_gq_api= mrealtime_query_api+'/'+query_job_id1
            output=get_api(api_path,new_gq_api)
            time.sleep(30)
            if int(output['queryJobAssetCounts']['total'] + output['queryJobAssetCounts']['running'] + output['queryJobAssetCounts']['error']+ output['queryJobAssetCounts']['queued'] + output['queryJobAssetCounts']['cancelled']) ==0:
                actual_assets = assets
                time.sleep(95)
                break 

            while datetime.utcnow().time() <= add_time(current_time, hours=0, minutes=10):
                output=get_api(api_path,new_gq_api)
                time.sleep(60)
                if float(output['queryJobAssetCounts']['finished'])>= buffer_asset_count:
                    time.sleep(90)
                    output=get_api(api_path,new_gq_api)
                    actual_assets = int(output['queryJobAssetCounts']['finished'])
                    break
                
            if float(output['queryJobAssetCounts']['finished'])<buffer_asset_count:
                actual_assets = int(output['queryJobAssetCounts']['finished'])
                test_result.update_error( 'live assets are  and not responding to RT query : {}'.format(output['queryJobAssetCounts']))

            break
        log.info('Query{} status :{}'.format(l,output['status'] ))
        time.sleep(10)
    


    if output['status'] == 'ERROR':
        test_result.update_error('realtime query{} status is ERROR'.format(l))
    if output ['status'] == 'FINISHED':
        
        if int(output['queryJobAssetCounts']['total'] + output['queryJobAssetCounts']['running'] + output['queryJobAssetCounts']['error']+ output['queryJobAssetCounts']['queued'] + output['queryJobAssetCounts']['cancelled']) ==0:
            actual_assets = assets
            test_result.update_success('All the live assets are responding to RT query{}'.format(l))
            
        else :
            test_result.update_warning(' live assets are  and not responding to RT query{} : {}'.format(l,output['queryJobAssetCounts']))

    log.info('the assets that are responding out of {} are {} for query{}'.format(assets, actual_assets,l))
    
    end_time = datetime.utcnow().time()
    # e_time = datetime.strptime(str(end_time), "%H:%M:%S.%f").strftime("%H:%M:%S")
    end_datetime_utc = datetime.utcnow()
    formatted_edatetime = end_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')
    e_time = str(formatted_edatetime)
    time_taken = subtract_times(end_time,current_time)
    t_time = datetime.strptime(str(time_taken), "%H:%M:%S.%f").strftime("%H:%M:%S")
    test_result.update_success('{} time is taken  to complete the Query{} and store the results'.format(time_taken,l))
    time.sleep(30)
    total_records_hdfs = """select count(*) from realtime_query_data where query_job_id = '%s'""" % query_job_id1

    total_records_pg = " select count(*) from pg.public.query_job_results where CAST(query_job_id as VARCHAR)  = '%s' ; " % query_job_id1

    total_records = " select  count(*) from query_job_results_view where query_job_id  = '%s';" % query_job_id1

    query_command_total = 'sudo TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --server https://localhost:5665 --user uptycs --catalog uptycs --schema upt_{} --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/cloud/config/wildcard.jks --insecure --execute "{};" '.format(domain ,total_records)
    query_command_pg = 'sudo TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --server https://localhost:5665 --user uptycs --catalog uptycs --schema upt_{} --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/cloud/config/wildcard.jks --insecure --execute "{};" '.format(domain ,total_records_pg)
    query_command_hdfs = 'sudo TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --server https://localhost:5665 --user uptycs --catalog uptycs --schema upt_{} --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/cloud/config/wildcard.jks --insecure --execute "{};" '.format(domain ,total_records_hdfs)
    
    g = Host(prestonode_ip, prestonode_user, '', presto_password)
    pg = g.execute_command(query_command_pg)
    pg=pg[1:-2]
    # pg_s =str(pg)

    hdfs = g.execute_command(query_command_hdfs)
    hdfs=hdfs[1:-2]
    # hdfs_s=str(hdfs)
    total = g.execute_command(query_command_total)
    total=total[1:-2]
    # total_s=str(total)

    time_hdfs_records ="select date_diff('second', min(upt_server_time), max(upt_server_time)) AS time_interval from realtime_query_data where query_job_id = '%s';" % query_job_id1
    time_command_hdfs = 'sudo TRINO_PASSWORD=prestossl /opt/uptycs/cloud/utilities/trino-cli --server https://localhost:5665 --user uptycs --catalog uptycs --schema upt_{} --password --truststore-password sslpassphrase --truststore-path /opt/uptycs/cloud/config/wildcard.jks --insecure --execute "{};" '.format(domain ,time_hdfs_records)
    hdfs_records_time = g.execute_command(time_command_hdfs)
    hdfs_records_time= hdfs_records_time.replace('"', '')
    print(hdfs_records_time)
    print(type(hdfs_records_time))
    hdfs_records_time_s = str(hdfs_records_time)
    hdfs_records_time_s = hdfs_records_time_s.strip()
    actual_records = actual_assets * records_per_asset
    config_records =0 
    hdfs_records =0 
    if actual_records <= 10000 :
        config_records = actual_records
    if actual_records > 10000:
        y = 0 
        while y <= 10000:
            y = y +  records_per_asset
        if y > 10000:
            config_records = y - records_per_asset
            hdfs_records = actual_records - config_records
    c=0

    if int(pg) == config_records:
        c=c+1
        log.info('config records : {} for query{}'.format(pg,l))
        test_result.update_success('records count stored in config - matched in query{}'.format(l))
    else :
        test_result.update_error('count did not match for query{}. The recordes in pg : {} ,Expected count :{}'.format(l,pg,config_records))
    time.sleep(70)
    if int(hdfs) ==hdfs_records:
        c=c+1
        log.info('hdfs records : {} for query{}'.format(hdfs,l))
        test_result.update_success('records count stored in hdfs - matched query{}'.format(l))
    else :
        test_result.update_error('count did not match for query{}. The recordes in hdfs : {} ,Expected count :{}'.format(l,hdfs,hdfs_records) )
    if int(total) == actual_records :
        c=c+1
        log.info('total records : {} for query{}'.format(total,l))
        test_result.update_success('total records count - matched query{}'.format(l))
    else :
        test_result.update_error('count did not match for query{}.The recordes in total : {} ,Expected count : {}'.format(l,total,actual_records))

    if c==3:
        result = 'FINISHED'
    else :
        result = 'FAILED'
    final_data_to_save['Query{}'.format(l)] = {
        'query' : rq_payload['query'],
        'Number of Assets Responded': actual_assets,
        'Test Start Time': c_time,
        'Test End Time': e_time,
        'Records in configdb': {'actual': pg,'expected':config_records},
        'Records in HDFS': {'actual':hdfs ,'expected':hdfs_records},
        'Total Records': {'actual':total ,'expected':actual_records},
        'Time taken for RT query to get completed': t_time,
        'Time taken for all the records to get ingested in seconds': hdfs_records_time_s,
        'Automation run Status ':result
    }

def realtime_query(domain, test_result):
#     # bringup realtime assets
    for i in rt_sims:
        kill_existing_processes(i,rtsim_user,user,'endpointsim',rtuser_password)
    deleted = query_configd(pgrt_hostip,pgrt_user,pgrt_password,'d')
    delete_count = [int(match.group()) for match in re.finditer(r'\b\d+\b', deleted)][0]
    check_count1 = query_configd(pgrt_hostip,pgrt_user,pgrt_password,'c')
    delete_check = [int(match.group()) for match in re.finditer(r'\b\d+\b',  check_count1)][0]
    if delete_check != 0:
        test_result.update_error ("assets didn't get delted", skip_test = True)
    for i in  rt_sims:
        run_instance(i,rtsim_user,user,'endpointsim',rtuser_password)
    check_count = query_configd(pgrt_hostip,pgrt_user,pgrt_password,'c')
    enroll_check = [int(match.group()) for match in re.finditer(r'\b\d+\b', check_count)][0]
    if enroll_check != assets:
        test_result.update_error ("assets didn't get enrolled",skip_test = True)
   
        
    Stack_URL = URL.formatformat(stack_keys['domain'],stack_keys['domainSuffix'])
    final_data_to_save['Stack Name'] = domain 
    final_data_to_save['Stack URL'] = Stack_URL
    final_data_to_save['Build Number'] = build
    final_data_to_save['Total Asset Count'] = assets
    final_data_to_save['Records Per Asset'] =  records_per_asset
    
    l=1
    for i in rq_payloads:
        query(i,l)
        l=l+1
    mongo_connection_string="mongodb://localhost:27017"
    client = pymongo.MongoClient(mongo_connection_string)
    database_name = 'real_time'
    collection_name = 'real_time_query'
    db=client[database_name]
    collection = db[collection_name]
    collection.insert_one(final_data_to_save).inserted_id

if __name__=="__main__":
    test_result = TestResult()
    realtime_query(domain,test_result)

    log.info(test_result)