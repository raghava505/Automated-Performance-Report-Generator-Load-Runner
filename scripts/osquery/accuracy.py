import json
import requests
import time
from datetime import datetime, timedelta, timezone
import threading
import re
import jwt
from urllib3.exceptions import InsecureRequestWarning 
import pandas as pd
import math
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_results(url, job_id, headers,stack_obj):
    job_url = '%s/%s' % (url, job_id)
    resp = requests.get(job_url, headers=headers, verify=False)
    status_data = json.loads(resp.content)
    #print(status_data)
    time.sleep(2)
    #print("get results fun")
    while status_data['status'] in ['RUNNING', 'QUEUED'] or status_data['error'] is None:
        if status_data['status'] == 'FINISHED':
            results = requests.get(job_url + '/results', headers=headers, verify=False)
            if results.ok:
                res_1=json.loads(results.text)

                #print("\n\n\n" ,res_1,"\n\n\n")
                resp_data = json.loads(results.content)
                #print(resp_data)
                data = {'items': resp_data['items'],
                        'columns': status_data['columns'],'queryStats':resp_data['queryStats']}
                requests.delete(job_url, headers=headers, verify=False)
                return data
            else:
                stack_obj.log.error('Error fetching results: ', results.content)
                break
        elif status_data['error'] is not None:
            stack_obj.log.error('Error occurred in query job: ', str(status_data))
            requests.delete(job_url, headers=headers, verify=False)
            return
        else:
            #print("get ")
            resp = requests.get(job_url, headers=headers, verify=False)
            status_data = json.loads(resp.content)
            #print("after get")
            #print(resp.content)
            time.sleep(1)
            continue
    stack_obj.log.error('queryJob failed execute')
    stack_obj.log.error('Query job failed: ', str(status_data))

def generate_headers(key, secret):
    header={}
    utcnow=datetime.utcnow()
    #print("gen headers")
    date=utcnow.strftime("%a, %d %b %Y %H:%M:%S GMT")
    exp_time = time.time() + 3600
    try:
        authVar = jwt.encode({'iss':key, 'exp': exp_time},secret).decode("utf-8")
    except:
        authVar = jwt.encode({'iss':key, 'exp': exp_time},secret)
    authorization="Bearer %s" % (authVar)
    header['date']=date
    header['authorization']=authorization
    header['Content-type']="application/json"
    return header

def send_query(api_conf, query_str, url_ext,stack_obj):
    query_type = 'global'
    #data = json.load(open(api_conf))
    data=api_conf
    headers = generate_headers(data['key'], data['secret'])
    #print("query_str is "+query_str)
    try:
        url = "https://%s.uptycs.%s/public/api/customers/%s/queryJobs" % (
        data['domain'], url_ext, data['customerId'])
    except:
        url = "https://%s.uptycs.%s/public/api/customers/%s/queryJobs" % (
        data['domain'], url_ext, data['customer_id'])
    payload = {'query': query_str, 'type': query_type, 'filters': {}, 'parameters': [],
               'parameterValues': {}
               }
    if query_type == 'realtime':
        payload['filters']['live'] = True
    json_payload = json.dumps(payload)
    resp = requests.post(url, headers=headers,
                         data=json_payload, verify=False)
    if resp.ok:
        return get_results(url, json.loads(resp.content)['id'], headers,stack_obj)
    else:
        #print(resp.content)
        return

def http_query(config, query_str, url_ext,stack_obj):
    attempts = 0
    while attempts < 10:
        try:
            #print("query is "+ query_str)
            resp_json = send_query(config, query_str, url_ext,stack_obj)
            if resp_json and 'queryStats' in resp_json:
                queryStats=resp_json["queryStats"]
            stack_obj.log.info(resp_json)
            record=0
            if resp_json and 'items' in resp_json:
                res = resp_json['items']
                resp_json = {}
                counter = 0
                for item in res:
                    resp_json[counter] = item['rowData']
                    counter += 1
                    record=item['rowData']["_col0"]
            stack_obj.log.info(query_str)
            return record
        except Exception as e:
           stack_obj.log.error('Unsuccessful global query: ',e)
           attempts += 1
           time.sleep(30)
    raise Exception('Unsuccessful http query 10 time in a row: %s' % query_str)

class osq_accuracy:
    def __init__(self,stack_obj,api_path,domain,assets_per_cust,ext,trans,input_file):
        start_time_utc=stack_obj.start_time_UTC
        end_time_utc=stack_obj.end_time_UTC
        format_data = "%Y-%m-%d %H:%M"
        start_time = start_time_utc - timedelta(minutes=20)
        self.start_time = start_time.strftime(format_data)
        end_time = end_time_utc + timedelta(minutes=40) #+ timedelta(hours=4)
        self.end_time = end_time.strftime(format_data)
        self.api_path=api_path
        self.domain=domain
        self.hours=stack_obj.hours
        self.endline=1800*self.hours
        self.assets_per_cust=assets_per_cust
        self.ext=ext
        self.trans=trans
        self.input_file=input_file
        self.stack_obj=stack_obj

        self.upt_day="".join(str(start_time_utc.strftime("%Y-%m-%d")).split('-'))
        self.stack_obj.log.info(f"Start time string in utc : {self.start_time}")
        self.stack_obj.log.info(f"End time string in utc : {self.end_time}")
        self.stack_obj.log.info(f"upt day : {self.upt_day}")
    def api_keys(self):
        with open(self.api_path,'r') as c:
            api_config=json.load(c)
            c.close()
        return api_config
    def get_utc_days_involved(self):
        time_format='%Y-%m-%d %H:%M'
        start_utc = datetime.strptime(self.start_time, time_format)
        end_utc = datetime.strptime(self.end_time, time_format)
        days_involved = 0
        current_date = start_utc.date()
        while current_date < end_utc.date():
            days_involved += 1
            current_date += timedelta(days=1)
        return days_involved
    def expected_events(self):
        input_lines =self.endline
        dns_lookup_events = {'dns_lookup_events-builder-added':0, 'dns_lookup_events_1-builder-added':0, 'dns_lookup_events_2-builder-added':0, 'dns_lookup_events_3-builder-added':0, 'dns_lookup_events_4-builder-added':0,'dns_lookup_events_5-builder-added':0,'dns_lookup_events_6-builder-added':0}
        process_events = {'process_events-builder-added':0, 'process_events_1-builder-added':0, 'process_events_2-builder-added':0, 'process_events_3-builder-added':0, 'process_events_4-builder-added':0, 'process_events_5-builder-added':0, 'process_events_6-builder-added':0, 'process_events_7-builder-added':0, 'process_events_8-builder-added':0, 'process_events_9-builder-added':0, 'process_events_10-builder-added':0}
        socket_events = {'socket_events-builder-added':0, 'socket_events_1-builder-added':0, 'socket_events_2-builder-added':0, 'socket_events_3-builder-added':0, 'socket_events_4-builder-added':0, 'socket_events_5-builder-added':0, 'socket_events_6-builder-added':0,'socket_events_7-builder-added':0}
        process_file_events = {'process_file_events-builder-added':0, 'process_file_events_3-builder-added':0, 'process_file_events_4-builder-added':0, 'process_file_events_5-builder-added':0, 'process_file_events_6-builder-added':0, 'process_file_events_7-builder-added':0, 'process_file_events_8-builder-added':0, 'process_file_events_9-builder-added':0, 'process_file_events_10-builder-added':0}
        req_tables = ['process_events', 'process_file_events', 'socket_events', 'dns_lookup_events']
        increment=self.assets_per_cust
        with open(self.input_file, "r") as fin:
            line_no = 1
            for line in fin:
                if line_no % 2 == 0 and line_no <= input_lines: 
                    lines = json.loads(line)
                    #print(line)
                    #print(len(lines["data"]))
                    for table_details in lines["data"]:
                        #print(table_details)
                        if table_details['name'] == 'process_events':
                            # index1 = table_details['columns']['auid']
                            # index2 = table_details['columns']['uid']
                            #rows = table_details['rows']
                            # if index1 == '0' or index2 == '0':
                            if ("auid" in table_details['columns'] and table_details['columns']['auid'] == '0') or ( 'uid' in table_details['columns'] and table_details['columns']['uid'] == '0'):
                                process_events['process_events-builder-added'] += increment
                            if '/bin/sh' in table_details['columns']['path']:
                                if '/bin/mysql' in table_details['columns']['ancestor_list']:
                                    process_events['process_events_5-builder-added'] += increment
                                if '/bin/php' in table_details['columns']['ancestor_list']:
                                    process_events['process_events_1-builder-added'] += increment
                                if '/bin/awk' in table_details['columns']['ancestor_list']:
                                    process_events['process_events_10-builder-added'] += increment
                            if '/proc/' in table_details['columns']['cmdline']:
                                process_events['process_events_2-builder-added'] += increment
                            if 'base64' in table_details['columns']['cmdline']:
                                process_events['process_events_3-builder-added'] += increment
                            if ('bin/osascript' in table_details['columns']['path']) or ('shell' in table_details['columns']['cmdline']):
                                process_events['process_events_4-builder-added'] += increment
                            if table_details['columns']['exe_name'] == 'wmic.exe':
                                process_events['process_events_7-builder-added'] += increment
                            # if table_details['columns']['version_info'] == "Net Command":
                            if "version_info" in table_details['columns'] and table_details['columns']['version_info'] == "Net Command":
                                process_events['process_events_8-builder-added'] += increment
                            if 'rmmod' in table_details['columns']['cmdline']:
                                process_events['process_events_9-builder-added'] += increment
                        if table_details['name'] == 'socket_events':
                            if (table_details['columns']['action'] == 'connect') and (table_details['columns']['family'] == '2') and (table_details['columns']['type'] == '2') and (table_details['columns']['exe_name'] == 'node'):
                                socket_events['socket_events-builder-added'] += increment
                                socket_events['socket_events_1-builder-added'] += increment
                                socket_events['socket_events_2-builder-added'] += increment
                            if (table_details['columns']['action'] == 'connect') and (table_details['columns']['family'] == '2') and (table_details['columns']['type'] == '2') and (table_details['columns']['remote_address'] == '169.254.169.254') and (table_details['columns']['is_container_process'] == '1'):
                                socket_events['socket_events_3-builder-added'] += increment
                            if (table_details['columns']['action'] == 'connect') and (table_details['columns']['cmdline'] == '-e') and (table_details['columns']['path'] == '/usr/bin/ruby'):
                                socket_events['socket_events_4-builder-added'] += increment
                            if "9.5.4.3" in table_details['columns']['remote_address'] or "169.254.169.254" in table_details['columns']['remote_address']:
                                socket_events['socket_events_5-builder-added'] += increment
                            if "9.5.4.3" in table_details['columns']['remote_address']:
                                socket_events['socket_events_6-builder-added'] += increment
                            if "ruby" in table_details["columns"]["path"]:
                                socket_events['socket_events_7-builder-added'] += increment

                        if table_details['name'] == 'dns_lookup_events':
                            #print(table_details["columns"])
                            index = table_details['columns']['question']
                            index1=table_details['columns']['answer']
                            last_part = index1.split('.')[-1]
                            #print(last_part)
                            num_list=re.findall("[0-9]", last_part)
                            #rows = table_details['rows']
                            #for row in rows:
                            if 'malware' in index:
                                dns_lookup_events['dns_lookup_events_1-builder-added'] += increment
                                dns_lookup_events['dns_lookup_events_2-builder-added'] += increment
                            if 'dga' in index:
                                dns_lookup_events['dns_lookup_events_3-builder-added'] += increment
                            if 'phishing' in index:
                                dns_lookup_events['dns_lookup_events_4-builder-added'] += increment
                            if 'coinminer' in index:
                                dns_lookup_events['dns_lookup_events-builder-added'] += increment  
                            if  len(last_part) == len(num_list):
                                dns_lookup_events['dns_lookup_events_6-builder-added'] += increment     
                            if len(index)>7:
                                dns_lookup_events['dns_lookup_events_5-builder-added'] += increment
                                
            

                        if table_details['name'] == 'process_file_events':
                            #rows = table_details['rows']
                            #for row in rows:
                            if (table_details['columns']['path'] == '/etc/passwd') and (table_details['columns']['operation'] == 'open') and (table_details['columns']['flags'] == 'O_WRONLY'):
                                process_file_events['process_file_events_3-builder-added'] += increment
                                process_file_events['process_file_events_4-builder-added'] += increment
                            if (table_details['columns']['operation'] == 'chmod') and (table_details['columns']['flags'] == 'S_ISUID'):
                                process_file_events['process_file_events-builder-added'] += increment
                            if (table_details['columns']['operation'] == 'rename') and (table_details['columns']['dest_path'] == '/.'):
                                process_file_events['process_file_events_5-builder-added'] += increment
                            if table_details['columns']['operation'] == 'chown32':
                                process_file_events['process_file_events_6-builder-added'] += increment
                            if (table_details['columns']['operation'] == 'write') and (table_details['columns']['executable'] == 'System') and (('.exe' in table_details['columns']['path']) or ('4D5A9000' in table_details['columns']['magic_number'])):
                                process_file_events['process_file_events_7-builder-added'] += increment
                            if (table_details['columns']['operation'] == 'rename'):
                                process_file_events['process_file_events_8-builder-added'] += increment
                            if ('/etc/ld.so.conf' in table_details['columns']['path']) and (table_details['columns']['operation'] == 'open') and (table_details['columns']['flags'] == 'O_WRONLY'):
                                process_file_events['process_file_events_9-builder-added'] += increment
                            if (table_details['columns']['path'] == '/etc/passwd') and (table_details['columns']['operation'] == 'open') and (table_details['columns']['is_container_process'] == '0'):
                                process_file_events['process_file_events_10-builder-added'] += increment

                else:
                    pass 
                line_no += 1  
            dict1 = {}
            dict1.update(dns_lookup_events)
            dict1.update(process_events)
            dict1.update(socket_events)
            dict1.update(process_file_events)
            if not self.trans:
                transformations=["dns_lookup_events_5-builder-added","dns_lookup_events_6-builder-added","dns_lookup_events_7-builder-added","socket_events_7-builder-added","socket_events_8-builder-added"]
                keys=dict1.keys()
                for events in keys:
                   if events in transformations:
                       dict1[events]=0        
            return dict1
    def get_expected_tables(self,endline):
        with open(self.input_file, "r") as fin:
            line_no = 1
            count=0
            output_log={}
            #lines_1 = fin.readlines()
            #print(f"no of inputfile lines {len(lines_1)}")
            for line in fin:
                #print(line)
                if line_no % 2 == 0 and line_no <= endline: 
                    lines = json.loads(line)
                    count=count+1
                    for table_details in lines["data"]:
                        if table_details['name'] in  output_log:
                            output_log[table_details['name']]=output_log[table_details['name']]+1
                        else:
                            output_log[table_details['name']]=1
                line_no=line_no+1
            self.stack_obj.log.info(f"calculated expected for tables from {count} messages in  {line_no} lines ")
        return output_log
    def run_table_accuracy(self,query,table,accuracy,expected,api):
        actual=http_query(api, query,self.ext,self.stack_obj)
        expect=expected[table]*(self.assets_per_cust)
        accuracy[table]={"actual":actual,"expected":expect,"accuracy":round((actual/expect)*100,2)}
    def table_accuracy(self,cust=0):
        api_config=self.api_keys()
        expected_tables=self.get_expected_tables(self.endline)
        self.stack_obj.log.info(expected_tables)
        if cust==0:
            api=api_config[self.domain]
        else:
            api=api_config[self.domain+str(cust)]
        
        expected_tables["process_open_sockets"]={}
        expected_tables["process_open_sockets"]=expected_tables["process_open_sockets_remote"]+expected_tables["process_open_sockets_local"]
        thread_list=[]
        accuracy={}
        tables=["processes","process_open_files","load_average","interface_details","dns_lookup_events","process_open_sockets","process_file_events","process_events","socket_events","sensitive_scan_events"]
        for table in tables:
            query="select count(*) from {} where upt_day>={} and upt_time >= timestamp '{}' and upt_time < timestamp '{}'".format(table,self.upt_day,self.start_time,self.end_time)
            self.stack_obj.log.info(f"Executing query : {query}")
            t1=threading.Thread(target=self.run_table_accuracy,args=(query,table,accuracy,expected_tables,api))
            t1.start()
            thread_list.append(t1)
        for thread1 in thread_list:
            thread1.join()
        df = pd.DataFrame(accuracy)
        df=df.T
        if df.empty : 
            self.stack_obj.log.info("\n%s",df)
            self.stack_obj.log.warning("empty dataframe found for osquery table accuracies")
            return None
        df = df.reset_index().rename(columns={'index': 'table'})
        self.stack_obj.log.info("\n%s",df)
        return_dict ={
                "format":"table","collapse":True,
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[]
                },
                "data":df.to_dict(orient="records")
            }
        return return_dict
    def events_accuracy(self,alerts_triggered,events_triggered,cust=0):
        api_config=self.api_keys()
        if cust==0:
            api=api_config[self.domain]
        else:
            api=api_config[self.domain+str(cust)]
        events_tables=["upt_alerts","upt_events","upt_detections"]
        expected=self.expected_events()
        accuracy={}
        for table in events_tables:
            if table=="upt_events":
                expect=sum(expected.values())
                if expect>events_triggered*self.hours*100000:
                    expect=events_triggered*self.hours*100000
                query="select count(*) from {} where upt_day>= {} and created_at >= timestamp '{}' and created_at < timestamp '{}' and code like '%-builder-added%'".format(table,self.upt_day,self.start_time,self.end_time)
                self.stack_obj.log.info(f"Executing query : {query}")
                actual = http_query(api, query,self.ext,self.stack_obj)
                self.stack_obj.log.info(actual)
            elif table=="upt_detections":
                expect=0
                query="select count(*) from {} where  created_at >= timestamp '{}' and created_at < timestamp '{}'".format(table,self.start_time,self.end_time)
                self.stack_obj.log.info(f"Executing query : {query}")
                actual = http_query(api, query,self.ext,self.stack_obj)
                self.stack_obj.log.info(actual)
            else:
                utc_days=self.get_utc_days_involved()
                # expect=alerts_triggered*1000*(utc_days+1)
                expect = alerts_triggered * 50 * math.ceil(self.hours)
                query="select count(*) from {} where  created_at >= timestamp '{}' and created_at < timestamp '{}' and code like '%-builder-added%'".format(table,self.start_time,self.end_time)
                self.stack_obj.log.info(f"Executing query : {query}")
                actual = http_query(api, query, self.ext,self.stack_obj)
                self.stack_obj.log.info(actual)
            if table=="upt_detections":
                accuracy[table]={"actual":actual,"expected":expect,"accuracy":0}
            else:
                accuracy[table]={"actual":actual,"expected":expect,"accuracy":(actual/expect)*100}
        df = pd.DataFrame(accuracy)
        df=df.T
        if df.empty : 
            self.stack_obj.log.info("\n%s",df)
            self.stack_obj.log.warning("empty dataframe found for osquery event accuracies")
            return None
        df = df.reset_index().rename(columns={'index': 'table'})
        self.stack_obj.log.info("\n%s",df)
        return_dict ={
                "format":"table","collapse":True,
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[]
                },
                "data":df.to_dict(orient="records")
            }
        return return_dict
        
