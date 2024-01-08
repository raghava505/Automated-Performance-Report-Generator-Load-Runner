import sys
import time
import pymongo
from datetime import datetime, timedelta
import json
from datetime import datetime
from memory_and_cpu_usages import MC_comparisions
from osquery.add_kafka_topics import kafka_topics
from disk_space import DISK
from input import create_input_form
from capture_charts_data import Charts
from gridfs import GridFS
from trino_queries import TRINO
from elk_errors import Elk_erros
from cloudquery.accuracy import ACCURACY
from osquery.accuracy import osq_accuracy
from kubequery.kube_accuracy import Kube_Accuracy
from kubequery.selfmanaged_accuracy import SelfManaged_Accuracy
from pg_stats import PG_STATS
from cloudquery.db_operations_time import DB_OPERATIONS_TIME
from cloudquery.events_count import EVE_COUNTS
from cloudquery.sts_records import STS_RECORDS
from api_presto_load import fetch_and_extract_csv,fetch_and_save_pdf
import pytz
import os
from create_chart import create_images_and_save

import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-log","--loglevel",type=str)
args = parser.parse_args()

logger = logging.getLogger(__name__)

c_handler = logging.StreamHandler()
c_handler.setLevel(logging.NOTSET)

c_format = logging.Formatter('%(levelname)s - %(message)s')
c_handler.setFormatter(c_format)

# Add handlers to the logger
logger.addHandler(c_handler)

# assuming args.loglevel is bound to the string value obtained from the
# command line argument. Convert to upper case to allow the user to
# specify --log=DEBUG or --log=debug
if not isinstance(args.loglevel, str):
    args.loglevel = "INFO"
    
numeric_level = getattr(logging, args.loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' %(args.loglevel))

if __name__ == "__main__":
    
    logger.setLevel(numeric_level)
    logger.info("Seting Log Level to => %s" %(args.loglevel))
    
    variables , prom_con_obj,load_cls =create_input_form()
    if not variables or not prom_con_obj : 
        print("Received NoneType objects, terminating the program ...")
        sys.exit()
        
    f_handler = logging.FileHandler('./logs/%s.log' %(variables["load_name"]))
    f_handler.setLevel(logging.DEBUG)
    
    f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    
    logger.addHandler(f_handler)
        
    TEST_ENV_FILE_PATH   = prom_con_obj.test_env_file_path
    print("Test environment file path is : " + TEST_ENV_FILE_PATH)
    #---------------------start time and endtime (timestamps) for prometheus queries-------------------
    s_at = time.perf_counter()
    format_data = "%Y-%m-%d %H:%M"
    start_time = datetime.strptime(variables["start_time_str_ist"], format_data)
    end_time = start_time + timedelta(hours=variables["load_duration_in_hrs"])

    start_time_str = variables["start_time_str_ist"]
    end_time_str = end_time.strftime(format_data)

    ist_timezone = pytz.timezone('Asia/Kolkata')
    utc_timezone = pytz.utc

    start_ist_time = ist_timezone.localize(datetime.strptime(start_time_str, '%Y-%m-%d %H:%M'))
    start_timestamp = int(start_ist_time.timestamp())
    start_utc_time = start_ist_time.astimezone(utc_timezone)

    end_ist_time = ist_timezone.localize(datetime.strptime(end_time_str, '%Y-%m-%d %H:%M'))
    end_timestamp = int(end_ist_time.timestamp())
    end_utc_time = end_ist_time.astimezone(utc_timezone)

    print("------ starttime and endtime strings in IST are : ", start_time_str , end_time_str)
    print("------ starttime and endtime strings in UTC are : ", start_utc_time , end_utc_time)
    print("------ starttime and endtime unix time stamps based on ist time are : ", start_timestamp , end_timestamp)
    #-------------------------------------------------------------------------------------------------
    with open(TEST_ENV_FILE_PATH , 'r') as file:
        test_env_json_details = json.load(file)
    skip_fetching_data=False
    domain = test_env_json_details['domain']
    extension = test_env_json_details['extension']
    #---------------------Check for previous runs------------------------------------
    mongo_connection_string=prom_con_obj.mongo_connection_string
    client = pymongo.MongoClient(mongo_connection_string)
    database_name = variables['load_type']+"_LoadTests"
    collection_name = variables["load_name"]
    db=client[database_name]
    collection = db[collection_name]

    documents_with_same_load_time_and_stack = collection.find({"load_details.sprint":variables['sprint'] ,"load_details.stack":test_env_json_details["stack"] , "load_details.load_start_time_ist":f"{variables['start_time_str_ist']}" , "load_details.load_duration_in_hrs":variables['load_duration_in_hrs']})
    if len(list(documents_with_same_load_time_and_stack)) > 0:
        print(f"ERROR! A document with load time ({variables['start_time_str_ist']}) - ({end_time_str}) on {test_env_json_details['stack']} for this sprint for {database_name}-{collection_name} load is already available.")
        skip_fetching_data=True
    if skip_fetching_data == False:
        run=1
        documents_with_same_sprint = list(collection.find({"load_details.sprint":variables['sprint']}))
        if len(documents_with_same_sprint)>0:
            max_run = 0
            for document in documents_with_same_sprint :
                max_run = max(document['load_details']['run'] , max_run)
            run=max_run+1
            print(f"you have already saved the details for this load in this sprint, setting run value to {run}")
        #-------------------------disk space--------------------------
        disk_space_usage_dict=None
        if variables["load_name"] != "ControlPlane":
            print("Performing disk space calculations ...")
            calc = DISK(start_timestamp=start_timestamp,end_timestamp=end_timestamp,prom_con_obj=prom_con_obj)
            disk_space_usage_dict=calc.make_calculations()
        #--------------------------------- add kafka topics ---------------------------------------
        kafka_topics_list=None
        if variables["load_type"] in ["Osquery","osquery_cloudquery_combined","all_loads_combined"]:
            print("Fetching kafka topics ...")
            kafka_obj = kafka_topics(prom_con_obj=prom_con_obj)
            kafka_topics_list = kafka_obj.add_topics_to_report()

        #-------------------------Trino Queries--------------------------
        trino_queries=None
        if variables["load_type"] != "KubeQuery":
            print("Performing trino queries ...")
            calc = TRINO(curr_ist_start_time=variables["start_time_str_ist"],curr_ist_end_time=end_time_str,prom_con_obj=prom_con_obj)
            trino_queries = calc.fetch_trino_queries()
        #-------------------------API LOAD--------------------------
        api_load_result_dict=None
        presto_load_result_dict=None
        if 'api_presto_load_reports_node_ip' in test_env_json_details:
            print(f"Looking for api load  and presto load csv files in {test_env_json_details['api_presto_load_reports_node_ip']}")
            stack_starttime_string=str(test_env_json_details['stack']).lower() + "-" + str(variables["start_time_str_ist"])
            api_load_csv_path = os.path.join(prom_con_obj.api_loads_folder_path , stack_starttime_string+".csv")
            benchto_load_csv_path=os.path.join(prom_con_obj.presto_loads_folder_path, stack_starttime_string, "benchto.csv")
            benchto_load_pdf_path=os.path.join(prom_con_obj.presto_loads_folder_path , stack_starttime_string, "Benchto.pdf")
            print("CSV file path for API/Jmeter load : " , api_load_csv_path)
            api_load_result_dict = fetch_and_extract_csv(api_load_csv_path,test_env_json_details['api_presto_load_reports_node_ip'],prom_con_obj)
            print("CSV file path for Presto/benchto load : " , benchto_load_csv_path)
            presto_load_result_dict = fetch_and_extract_csv(benchto_load_csv_path,test_env_json_details['api_presto_load_reports_node_ip'],prom_con_obj)

        else:
            print(f"Skipping API load details because 'api_presto_load_reports_node_ip' is not present in stack json file")

        #-------------------------Osquery Table Accuracies----------------------------
        Osquery_table_accuracies=None
        Osquery_event_accuracies=None
        if variables["load_type"] in ["Osquery","osquery_cloudquery_combined","all_loads_combined"] and variables["load_name"] != "ControlPlane":
            assets_per_cust=int(load_cls.get_load_specific_details(variables['load_name'])['assets_per_cust'])
            input_file = load_cls.get_load_specific_details(variables['load_name'])['input_file']
            alert_rules_triggered_per_cust=test_env_json_details['alert_rules_per_cust']['triggered']
            event_rules_triggered_per_cust=test_env_json_details['event_rules_per_cust']['triggered']
            print("Calculating Table accuracies for Osquery Load...")
            api_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),f"osquery/api_keys/{domain}.json")
            input_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),f"osquery/testinputfiles/{input_file}")
            print("Printing osquery accuracy calculation details : ")
            print("Assets per customer value : ", assets_per_cust)
            print("Input file path : ", input_file_path)
            print("stack customers file path : ", api_path)
            accuracy_obj= osq_accuracy(start_time_utc=start_utc_time,end_time_utc=end_utc_time,api_path=api_path,domain=domain,endline=1800*variables['load_duration_in_hrs'],assets_per_cust=assets_per_cust,ext=extension,trans=True,hours=variables['load_duration_in_hrs'],input_file=input_file_path)
            Osquery_table_accuracies = accuracy_obj.table_accuracy()
            print("Osquery_table_accuracies : ",Osquery_table_accuracies)
            print("Calculating Events accuracies for Osquery Load ...")
            Osquery_event_accuracies = accuracy_obj.events_accuracy(alert_rules_triggered_per_cust,event_rules_triggered_per_cust)
            print("Osquery_event_accuracies : ",Osquery_event_accuracies)
        

        #-------------------------Kubequery Accuracies----------------------------
        kubequery_accuracies=None
        if variables["load_name"] == "KubeQuery_SingleCustomer" or variables["load_type"] in ["all_loads_combined"]:
            print("Calculating accuracies for KubeQuery ...")
            accuracy = Kube_Accuracy(start_timestamp=start_utc_time,end_timestamp=end_utc_time,prom_con_obj=prom_con_obj,variables=variables)
            kubequery_accuracies = accuracy.accuracy_kubernetes()
            print(json.dumps(kubequery_accuracies, indent=4))

        #-------------------------SelfManaged Accuracies----------------------------
        selfmanaged_accuracies=None
        if variables["load_name"] == "SelfManaged_SingleCustomer" or variables["load_type"] in ["all_loads_combined"]:
            print("Calculating accuracies for SelfManaged ...")
            accuracy = SelfManaged_Accuracy(start_timestamp=start_utc_time,end_timestamp=end_utc_time,prom_con_obj=prom_con_obj,variables=variables)
            selfmanaged_accuracies = accuracy.accuracy_selfmanaged()
            print(json.dumps(selfmanaged_accuracies, indent=4))

        
        #--------------------------------------Events Counts--------------------------------------
        evecount = None
        if variables["load_type"] in ["CloudQuery","osquery_cloudquery_combined","all_loads_combined"]:
            print("Calculating the counts of various events during the load ...")
            calc = EVE_COUNTS(variables=variables)
            evecount = calc.get_events_count()

        #--------------------------------------STS Records-------------------------------------------
        sts = None
        # if variables["load_name"] == "AWS_MultiCustomer":
        #     print("Calculating STS Records ...")
        #     calc = STS_RECORDS(start_timestamp=start_utc_time,end_timestamp=end_utc_time,prom_con_obj=prom_con_obj,variables=variables)
        #     sts = calc.calc_stsrecords()


        #-----------------------------Processing Time for Db Operations------------------------------
        db_op = None
        if variables["load_type"] in ["CloudQuery","osquery_cloudquery_combined","all_loads_combined"]:
            print("Processing time for Db Operations ...")
            calc = DB_OPERATIONS_TIME(start_timestamp=start_timestamp,end_timestamp=end_timestamp,prom_con_obj=prom_con_obj)
            db_op=calc.db_operations()

        #-------------------------------PG Stats Calculations -------------------------------------
        pg_stats = None
        print("Calculating Postgress Tables Details ...")
        pgtable = PG_STATS(start_timestamp,end_timestamp,variables["load_duration_in_hrs"],prom_con_obj)
        pg_stats = pgtable.process_output()

        #--------------------------------Elk Erros------------------------------------------------
        elk_errors = None
        print("Fetching Elk Errors ...")
        elk = Elk_erros(start_timestamp=start_timestamp,end_timestamp=end_timestamp,prom_con_obj=prom_con_obj)
        elk_errors = elk.fetch_errors()
        
        #--------------------------------cpu and mem node-wise---------------------------------------
        print("Fetching resource usages data ...")
        comp = MC_comparisions(start_timestamp=start_timestamp,end_timestamp=end_timestamp,prom_con_obj=prom_con_obj)
        mem_cpu_usages_dict,overall_usage_dict=comp.make_comparisions(load_cls.application_level_usage_app_names_for_table , load_cls.common_app_names)
        
        #-------------------------Cloudquery Accuracies----------------------------
        cloudquery_accuracies=None
        if variables["load_type"] in ["CloudQuery","osquery_cloudquery_combined","all_loads_combined"]:
            print("Calculating accuracies for cloudquery ...")
            accu= ACCURACY(start_timestamp=start_utc_time,end_timestamp=end_utc_time,prom_con_obj=prom_con_obj,variables=variables)
            cloudquery_accuracies = accu.calculate_accuracy()
        
        #--------------------------------Capture charts data---------------------------------------
        all_gridfs_fileids=[]
        try:
            fs = GridFS(db)
            print("Fetching charts data ...")
            charts_obj = Charts(start_timestamp=start_timestamp,end_timestamp=end_timestamp,prom_con_obj=prom_con_obj,
                    add_extra_time_for_charts_at_end_in_min=variables["add_extra_time_for_charts_at_end_in_min"],fs=fs)
            complete_charts_data_dict,all_gridfs_fileids=charts_obj.capture_charts_and_save(load_cls.get_all_chart_queries())
            print("Saved charts data successfully !")
            #--------------------------------take screenshots---------------------------------------
            # print("Capturing compaction status screenshots  ...")
            # cp_obj = take_screenshots(start_time=start_time,end_time=end_time,fs=fs,elk_url=test_env_json_details["elk_url"])
            # compaction_status_image=cp_obj.get_compaction_status()
            #-------------------------- Saving the json data to mongo -------------------------
            print("Saving data to mongoDB ...")
            load_details =  {
                "stack":test_env_json_details["stack"],
                "stack_url":test_env_json_details["stack_url"],
                "clusters":test_env_json_details["clusters"],
                "SU":test_env_json_details["SU"],
                "sprint": variables['sprint'],
                "build": variables['build'],
                "load_name":f"{variables['load_name']}",
                "load_type":f"{variables['load_type']}",
                "load_duration_in_hrs":variables['load_duration_in_hrs'],
                "load_start_time_ist" : f"{variables['start_time_str_ist']}",
                "load_end_time_ist" : f"{end_time_str}",
                "run":run,
                }
            # with open(f"{prom_con_obj.base_stack_config_path}/load_specific_details.json" , 'r') as file:
            #     load_specific_details = json.load(file)
            try:
                load_details.update(load_cls.get_load_specific_details(variables['load_name']))
            except:
                print(f"WARNING : Load specific details for {variables['load_name']} in {load_cls} is not found!")

            final_data_to_save = {
                "load_details":load_details,
                "test_environment_details":test_env_json_details
            }

            final_data_to_save.update(overall_usage_dict)

            if disk_space_usage_dict:
                final_data_to_save.update({"disk_space_usages":disk_space_usage_dict})
            if kafka_topics_list:
                final_data_to_save.update({"kafka_topics":kafka_topics_list})
            if evecount:
                final_data_to_save.update({"Cloudquery Event Counts":evecount})
            if sts:
                final_data_to_save.update({"STS Records":sts})
            if trino_queries:
                final_data_to_save.update({"Trino_queries":trino_queries})
            if cloudquery_accuracies:
                final_data_to_save.update({"Cloudquery Table Accuracies":cloudquery_accuracies})
            if db_op:
                final_data_to_save.update({"Cloudquery Db Operations Processing Time":db_op})
            if kubequery_accuracies:
                final_data_to_save.update({"Kubequery Table Accuracies":kubequery_accuracies})
            if selfmanaged_accuracies:
                final_data_to_save.update({"Selfmanaged Table Accuracies":selfmanaged_accuracies})
            if pg_stats:
                final_data_to_save.update({"PG Stats":pg_stats})
            if elk_errors:
                final_data_to_save.update({"ELK Errors":elk_errors})
            if Osquery_table_accuracies:
                final_data_to_save.update({"Osquery Table Accuracies":Osquery_table_accuracies})
            if Osquery_event_accuracies:
                final_data_to_save.update({"Osquery Event Accuracies":Osquery_event_accuracies})
            if api_load_result_dict:
                final_data_to_save.update({"API Load details":api_load_result_dict})
            if presto_load_result_dict:
                final_data_to_save.update({"Presto Load details":presto_load_result_dict})

            final_data_to_save.update({"charts":complete_charts_data_dict})
            final_data_to_save.update(mem_cpu_usages_dict)
            final_data_to_save.update({"observations":load_cls.get_dictionary_of_observations()})
            # all_gridfs_referenced_ids=all_gridfs_fileids[:]
            # final_data_to_save.update({"all_gridfs_referenced_ids":all_gridfs_referenced_ids})
            inserted_id = collection.insert_one(final_data_to_save).inserted_id
            print(f"Document pushed to mongo successfully into database:{database_name}, collection:{collection_name} with id {inserted_id}")
            #---------------CREATING GRAPHS-----------------
            try:
                print("Generating graphs from the saved data ...")
                BASE_GRAPHS_PATH = os.path.join(os.path.dirname(prom_con_obj.ROOT_PATH),'graphs')
                path=f"{BASE_GRAPHS_PATH}/{database_name}/{collection_name}/{inserted_id}"
                os.makedirs(path,exist_ok=True)
                create_images_and_save(path,inserted_id,collection,fs,variables["load_duration_in_hrs"])
                try:
                    test_title = "Test title : "+str(load_cls.get_load_specific_details(variables['load_name'])['test_title'])
                except:
                    test_title=""
                create_images_and_save(path,inserted_id,collection,fs,variables["load_duration_in_hrs"],variables=variables,end_time_str=end_time_str,run=run,stack=test_env_json_details["stack"],test_title=test_title)
                print("Done!")
            except Exception as e:
                print(f"Error while generating graphs into {path} : {str(e)}")
            try:
                #---------------FETCHING PDFS-----------------
                if presto_load_result_dict:
                    print(f"Fetching presto load charts pdf from {test_env_json_details['api_presto_load_reports_node_ip']}:{benchto_load_csv_path}")
                    BASE_PDFS_PATH = os.path.join(os.path.dirname(prom_con_obj.ROOT_PATH),'pdfs')
                    presto_load_local_pdf_path=f"{BASE_PDFS_PATH}/{database_name}/{collection_name}/{inserted_id}/Presto Load Charts pdf.pdf"
                    print(f'Saving the presto load pdf to {presto_load_local_pdf_path}')
                    os.makedirs(os.path.dirname(presto_load_local_pdf_path),exist_ok=True)
                    fetch_and_save_pdf(benchto_load_pdf_path,test_env_json_details['api_presto_load_reports_node_ip'],prom_con_obj,presto_load_local_pdf_path)
            except Exception as e:
                print(f"Error while fetching pdfs : {str(e)}")

        except Exception as e:
            print(f"ERROR : Failed to insert document into database {database_name}, collection:{collection_name} , {str(e)}")
            print("Deleting stored chart data ...")
            for file_id in all_gridfs_fileids:
                print("deleting ", file_id)
                fs.delete(file_id=file_id)
        finally:
            f3_at = time.perf_counter()
            print(f"Collecting the report data took : {round(f3_at - s_at,2)} seconds in total")
            client.close()
    
