import sys
import time
import pymongo
import json
from gridfs import GridFS
from bson import ObjectId
import concurrent.futures
from config_vars import *
from input import create_input_form
from extract_stack_details import extract_ram_cores_storage_details
from load_params import Load_Params
from add_kafka_topics import kafka_topics
from disk_space import diskspace_usage_class
from trino_queries_analysis import trino_queries_class
from active_conn_by_apps import num_active_conn_class
from osquery.accuracy import osq_accuracy
from kubequery.kube_accuracy import Kube_Accuracy
from kubequery.selfmanaged_accuracy import SelfManaged_Accuracy
from cloudquery.accuracy import cloud_accuracy
from pg_stats import pg_stats_class
from cloudquery.db_operations_time import DB_OPERATIONS_TIME
from cloudquery.events_count import events_count_class
from cloudquery.sts_records import STS_RECORDS
from elk_errors import elk_errors_class
from compaction_status import CompactionStatus
from memory_and_cpu_usages import mem_cpu_usage_class
from extract_and_preprocess_resource_utilizations import complete_resource_usages
from capture_charts_data import Charts
from create_chart import create_images_and_save
from pg_badger import return_pgbadger_results,get_and_save_pgb_html
from helper import fetch_and_save_pdf,fetch_and_extract_csv
from pgbouncer_connections import pgbouncer_conn_class
from generalised_postgres_mon_queries import postgres_monitoring_stats_class

if __name__ == "__main__":
    s_at = time.perf_counter()
    variables , stack_obj,load_cls = create_input_form()
    try:
        if not variables or not stack_obj or not load_cls : 
            print("Received NoneType objects, terminating the program ...")
            sys.exit()
        
        apiload_remote_directory_name=variables["apiload_remote_directory_name"]
        hours=variables["load_duration_in_hrs"]
        start_time_str_ist= variables['start_time_str_ist']
        sprint = variables['sprint']

        #---------------------opening stack file-------------------
        with open(stack_obj.test_env_file_path , 'r') as file:
            test_env_json_details = json.load(file)
        skip_fetching_data=False

        stack = test_env_json_details["stack"]
        domain = test_env_json_details['domain']
        extension = str(test_env_json_details['suffix']).split('.')[1]
        
        #---------------------Check for previous runs------------------------------------
        client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
        database_name = variables['load_type']+"_LoadTests_New"
        collection_name = variables["load_name"]
        db=client[database_name]
        collection = db[collection_name]

        documents_with_same_load_time_and_stack = collection.find({"load_details.data.sprint":sprint ,"load_details.data.stack":stack , "load_details.data.load_start_time_ist":f"{start_time_str_ist}" , "load_details.data.load_duration_in_hrs":hours})
        if len(list(documents_with_same_load_time_and_stack)) > 0:
            stack_obj.log.error(f"A document with load time ({start_time_str_ist}) - ({stack_obj.end_time_str_ist}) on {stack} for this sprint for {database_name}-{collection_name} load is already available.")
            skip_fetching_data=True
        if skip_fetching_data == False:
            run=1
            documents_with_same_sprint = list(collection.find({"load_details.data.sprint":sprint}))
            if len(documents_with_same_sprint)>0:
                max_run = 0
                for document in documents_with_same_sprint :
                    max_run = max(document['load_details']['data']['run'] , max_run)
                run=max_run+1
                stack_obj.log.warning(f"you have already saved the details for this load in this sprint, setting run value to {run}")

            # if 'elastic_node_ip' in test_env_json_details and 'pgbadger_reports_mount' in test_env_json_details:
            #     stack_obj.log.info("\n****** \nChecking health of PGbadger ... \n\n")
            #     status,link=get_and_save_pgb_html(stack_obj,test_env_json_details['elastic_node_ip'],"curr_pgbad_html_path","pgbadger_tail_path",test_env_json_details['pgbadger_reports_mount'],check=True)
            #     if not status:
            #         stack_obj.log.error("PGBadger seems to be not working in your stack. Please try to generate a pgbadger report manually to check if working fine.")
            #         stack_obj.log.info(f"Here is the sample report generated through automation just now : {link}")
            #         user_decision = input("Continue without pgbadger details in the report? (y/n) : ")
            #         if user_decision == "y":
            #             pass
            #         else:
            #             stack_obj.log.info("Terminating program ...")
            #             sys.exit()
            #     else:
            #         stack_obj.log.info("\nCHECK PASSED : PGbadger is in good condition \n ****** !")
            
            load_details =  {
                "stack":stack,
                "stack_url":str(domain)+"."+str(test_env_json_details["suffix"]),
                "architecture":test_env_json_details["architecture"],
                "sprint": sprint,
                "build": variables['build'],
                "load_name":variables['load_name'],
                "load_type":variables['load_type'],
                "load_duration_in_hrs":hours,
                "load_start_time_utc" : stack_obj.start_time_str_utc,
                "load_end_time_utc" : stack_obj.end_time_str_utc,
                "load_start_time_ist" : start_time_str_ist,
                "load_end_time_ist" : stack_obj.end_time_str_ist,
                "run":run,
                }
            try:
                load_details.update(load_cls.get_load_specific_details(variables['load_name']))
            except:
                stack_obj.log.warning(f"Load specific details for {variables['load_name']} in {load_cls} is not found!")

            # get necessary load parameters
            # if variables["load_name"] in ["KubeQuery_SingleCustomer","SelfManaged_SingleCustomer","KubeQuery_and_SelfManaged_Combined"] or variables["load_type"] in ["all_loads_combined"]:
            #     load_params = Load_Params(stack_obj=stack_obj,domain=domain)
            #     load_name = variables["load_name"]
            #     params = {
            #         "KubeQuery_SelfManaged_Load_Details" : load_params.get_load_params(load_name=load_name)
            #     }
            #     stack_obj.log.info(f"kube load params : {json.dumps(params, indent=4)}")

            #     try:
            #         if params:
            #             if "KubeQuery Load Details" in load_details:
            #                 load_details["KubeQuery Load Details"].update(params)
            #             else:
            #                 load_details.update(params)
            #     except Exception as err:
            #         stack_obj.log.error(f"load_details.update(params) => {err}")
            
            header_data = {
                "load_details":{"format":"mapping","schema":{"page":"Summary"},"data":load_details},
                "Test environment details": None,
                "observations":load_cls.get_observations(),
                "Bugs raised":load_cls.get_bugs_raised(),
                "new_format":True
            }
            complete_resource_details = None
            accuracies = {}
            middle_data = None
            trino_queries_analyse_results=None
            memory_usages=None
            cpu_usages=None
            footer_data = {}

            def calculate_resource_utilizations_thread(stack_obj, load_cls):
                stack_obj.log.info("******* [NEW] Calculating complete resource utilizations ...")
                resource_obj = complete_resource_usages(stack_obj, include_nodetypes=load_cls.hostname_types)
                return resource_obj.get_complete_result()
            
            

            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit the resource utilization calculation task
                future_resource_usages = executor.submit(calculate_resource_utilizations_thread, stack_obj, load_cls)


                complete_resource_details = future_resource_usages.result()


                if complete_resource_details:
                    memory_usages = complete_resource_details.pop("memory_usages", None)
                if complete_resource_details:
                    cpu_usages = complete_resource_details.pop("cpu_usages", None)

            if memory_usages:footer_data.update({"memory_usages":memory_usages})
            if cpu_usages:footer_data.update({"cpu_usages":cpu_usages})
 #--------------------------------Capture charts data---------------------------------------
            
            stack_obj.log.info("******* Fetching charts data ...")
            # footer_data.update({"all_gridfs_referenced_ids":all_gridfs_fileids})
            
            #--------------------------------Saving report data to mongodb---------------------------------------
            stack_obj.log.info("******* Saving report data to mongodb ...")
            final_data_to_save= {}
            final_data_to_save.update(header_data)
            if complete_resource_details: final_data_to_save.update(complete_resource_details)
            if accuracies:final_data_to_save.update(accuracies)
            if middle_data:final_data_to_save.update(middle_data)
            if trino_queries_analyse_results:final_data_to_save.update({"Trino Queries Analysis":trino_queries_analyse_results})
            if footer_data:final_data_to_save.update(footer_data)


            inserted_id = collection.insert_one(final_data_to_save).inserted_id


            f3_at = time.perf_counter()
            stack_obj.log.info(f"------------------------------ Collecting the report data took : {round(f3_at - s_at,2)} seconds in total")
            client.close()
    except Exception as e:
        stack_obj.log.exception(e)
        raise RuntimeError from e