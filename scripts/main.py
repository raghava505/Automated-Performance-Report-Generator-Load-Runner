import sys
import time
import pymongo
import json
from gridfs import GridFS
from bson import ObjectId

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
        database_name = variables['load_type']+"_LoadTests"
        collection_name = variables["load_name"]
        db=client[database_name]
        collection = db[collection_name]

        documents_with_same_load_time_and_stack = collection.find({"load_details.sprint":sprint ,"load_details.stack":stack , "load_details.load_start_time_ist":f"{start_time_str_ist}" , "load_details.load_duration_in_hrs":hours})
        if len(list(documents_with_same_load_time_and_stack)) > 0:
            stack_obj.log.error(f"A document with load time ({start_time_str_ist}) - ({stack_obj.end_time_str_ist}) on {stack} for this sprint for {database_name}-{collection_name} load is already available.")
            skip_fetching_data=True
        if skip_fetching_data == False:
            run=1
            documents_with_same_sprint = list(collection.find({"load_details.sprint":sprint}))
            if len(documents_with_same_sprint)>0:
                max_run = 0
                for document in documents_with_same_sprint :
                    max_run = max(document['load_details']['run'] , max_run)
                run=max_run+1
                stack_obj.log.warning(f"you have already saved the details for this load in this sprint, setting run value to {run}")

            if 'elastic' in test_env_json_details and 'pgbadger_reports_mount' in test_env_json_details:
                stack_obj.log.info("\n\n****** \nChecking health of PGbadger ... \n\n")
                status,link=get_and_save_pgb_html(stack_obj,test_env_json_details['elastic'],"curr_pgbad_html_path","pgbadger_tail_path",test_env_json_details['pgbadger_reports_mount'],check=True)
                if not status:
                    stack_obj.log.error("PGBadger seems to be not working in your stack. Please try to generate a pgbadger report manually to check if working fine.")
                    stack_obj.log.info(f"Here is the sample report generated through automation just now : {link}")
                    user_decision = input("Continue without pgbadger details in the report? (y/n) : ")
                    if user_decision == "y":
                        pass
                    else:
                        stack_obj.log.info("Terminating program ...")
                        sys.exit()
                else:
                    stack_obj.log.info("\nCHECK PASSED : PGbadger is in good condition \n ****** !")
            
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
            if variables["load_name"] in ["KubeQuery_SingleCustomer","SelfManaged_SingleCustomer","KubeQuery_and_SelfManaged_Combined"] or variables["load_type"] in ["all_loads_combined"]:
                load_params = Load_Params(connection_object=stack_obj)
                load_name = variables["load_name"]
                params = {
                    "KubeQuery_SelfManaged_Load_Details" : load_params.get_load_params(load_name=load_name)
                }
                stack_obj.log.info(f"kube load params : {json.dumps(params, indent=4)}")

                try:
                    if params:
                        if "KubeQuery Load Details" in load_details:
                            load_details["KubeQuery Load Details"].update(params)
                        else:
                            load_details.update(params)
                except Exception as err:
                    stack_obj.log.error(f"load_details.update(params) => {err}")
            
            final_data_to_save = {
                "load_details":load_details,
                "Test environment details": extract_ram_cores_storage_details(stack_obj)
            }

            #-------------------------real time query test details--------------------------
            if domain=="longevity" and variables["load_type"] in ["all_loads_combined"]: 
                from realtimequery_tests.real_time_query import realtime_query
                stack_obj.log.info(f"Performing realtime query test on stack '{stack}' ...")
                realtime_query_results=realtime_query()
                if realtime_query_results:final_data_to_save.update({"Realtimequery test results":realtime_query_results})
            #-------------------------disk space--------------------------
            if variables["load_name"] != "ControlPlane":
                stack_obj.log.info("******* Calculating disk space usages ...")
                calc = diskspace_usage_class(stack_obj=stack_obj)
                disk_space_usage_dict=calc.make_calculations()
                if disk_space_usage_dict:final_data_to_save.update({"disk_space_usages":disk_space_usage_dict})
            #--------------------------------- add kafka topics ---------------------------------------
            stack_obj.log.info("******* Fetching kafka topics ...")
            kafka_obj = kafka_topics(stack_obj)
            kafka_topics_list = kafka_obj.add_topics_to_report()
            if kafka_topics_list:final_data_to_save.update({"kafka_topics":kafka_topics_list})
            #---------------No.of Active connections by application---------------
            stack_obj.log.info("******* Fetching active connection details ...")
            active_conn_obj = num_active_conn_class(stack_obj=stack_obj)
            active_conn_results = active_conn_obj.get_avg_active_conn()
            if active_conn_results:final_data_to_save.update({"Number of active connections group by application on master":active_conn_results})
            #-------------------------Trino Queries--------------------------
            stack_obj.log.info("******* Performing trino queries analysis ...")
            trino_obj = trino_queries_class(stack_obj=stack_obj)
            trino_queries_analyse_results = trino_obj.fetch_trino_results()
            if trino_queries_analyse_results:final_data_to_save.update({"Trino Queries Analysis":trino_queries_analyse_results})
            #-------------------------Presto LOAD--------------------------
            if 'prestoload_simulator_ip' in test_env_json_details:
                stack_obj.log.info(f"------------------------------ Looking for presto load csv files in {test_env_json_details['prestoload_simulator_ip']}")
                stack_starttime_string=str(stack).lower() + "-" + str(start_time_str_ist)
                benchto_load_csv_path=os.path.join(PRESTO_LOADS_FOLDER_PATH, stack_starttime_string, "benchto.csv")
                benchto_load_pdf_path=os.path.join(PRESTO_LOADS_FOLDER_PATH , stack_starttime_string, "Benchto.pdf")
                stack_obj.log.info(f"CSV file path for Presto/benchto load : {benchto_load_csv_path}")
                presto_load_result_dict = fetch_and_extract_csv(benchto_load_csv_path,test_env_json_details['prestoload_simulator_ip'],stack_obj)
                if presto_load_result_dict:final_data_to_save.update({"Presto Load details":presto_load_result_dict})
            else:
                stack_obj.log.warning(f"------------------------------ Skipping presto load details because 'prestoload_simulator_ip' is not present in stack json file")
            #-------------------------(OLD) API load--------------------------
            if 'apiload_simulator_ip' in test_env_json_details:
                stack_obj.log.info(f"------------------------------ Looking for api load (old way) csv files in {test_env_json_details['apiload_simulator_ip']}")
                stack_starttime_string=str(stack).lower() + "-" + str(start_time_str_ist)
                api_load_csv_path = os.path.join(API_LOADS_FOLDER_PATH_TEMP , stack_starttime_string+".csv")
                stack_obj.log.info(f"CSV file path for API/Jmeter load : {api_load_csv_path}")
                api_load_result_dict = fetch_and_extract_csv(api_load_csv_path,test_env_json_details['apiload_simulator_ip'],stack_obj)
                if api_load_result_dict:final_data_to_save.update({"API Load details":api_load_result_dict})
            else:
                stack_obj.log.warning(f"------------------------------ Skipping (old) API load details because 'apiload_simulator_ip' is not present in stack json file")
            #-------------------------Osquery Table Accuracies----------------------------
            if variables["load_type"] in ["Osquery","osquery_cloudquery_combined","all_loads_combined"] and variables["load_name"] != "ControlPlane":
                assets_per_cust=int(load_cls.get_load_specific_details(variables['load_name'])["RuleEngine and ControlPlane Load Details"]['assets_per_cust'])
                input_file = load_cls.get_load_specific_details(variables['load_name'])["RuleEngine and ControlPlane Load Details"]['input_file']
                alert_rules_triggered_per_cust=test_env_json_details['alert_rules_per_cust']['triggered']
                event_rules_triggered_per_cust=test_env_json_details['event_rules_per_cust']['triggered']
                stack_obj.log.info(f"------------------------------ Calculating Table accuracies for Osquery Load ...")
                api_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),f"osquery/api_keys/{domain}.json")
                input_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),f"osquery/testinputfiles/{input_file}")
                stack_obj.log.info(f"Assets per customer value : {assets_per_cust}")
                stack_obj.log.info(f"Input file path : {input_file_path}")
                stack_obj.log.info(f"stack customers file path : {api_path}")
                osq_accuracy_obj= osq_accuracy(stack_obj,api_path=api_path,domain=domain,assets_per_cust=assets_per_cust,ext=extension,trans=True,input_file=input_file_path)
                Osquery_table_accuracies = osq_accuracy_obj.table_accuracy()
                stack_obj.log.info(f"Osquery_table_accuracies : {json.dumps(Osquery_table_accuracies,indent=4)}")
                if Osquery_table_accuracies:final_data_to_save.update({"Osquery Table Accuracies":Osquery_table_accuracies})
                if input_file != "inputFile6tab_12rec.log":
                    stack_obj.log.info("******* Calculating Events/Alerts accuracies for Osquery Load ...")
                    Osquery_event_accuracies = osq_accuracy_obj.events_accuracy(alert_rules_triggered_per_cust,event_rules_triggered_per_cust)
                    stack_obj.log.info(f"Osquery_event_accuracies : {json.dumps(Osquery_event_accuracies,indent=4)}")
                    if Osquery_event_accuracies:final_data_to_save.update({"Osquery Event Accuracies":Osquery_event_accuracies})
            #-------------------------Kubequery Accuracies----------------------------
            if variables["load_name"] in ["KubeQuery_SingleCustomer","KubeQuery_and_SelfManaged_Combined"] or variables["load_type"] in ["all_loads_combined"]:
                stack_obj.log.info("******* Calculating accuracies for KubeQuery Load ...")
                kube_accuracy_obj = Kube_Accuracy(stack_obj=stack_obj)
                kubequery_accuracies = kube_accuracy_obj.accuracy_kubernetes()
                stack_obj.log.info(json.dumps(kubequery_accuracies, indent=2))
                if kubequery_accuracies:final_data_to_save.update({"Kubequery Table Accuracies":kubequery_accuracies})
            #-------------------------SelfManaged Accuracies----------------------------
            if variables["load_name"] in ["SelfManaged_SingleCustomer","KubeQuery_and_SelfManaged_Combined"] or variables["load_type"] in ["all_loads_combined"]:
                stack_obj.log.info("******* Calculating accuracies for SelfManaged Load ...")
                selfmanaged_accuracy_obj = SelfManaged_Accuracy(stack_obj=stack_obj)
                selfmanaged_accuracies = selfmanaged_accuracy_obj.accuracy_selfmanaged()
                stack_obj.log.info(json.dumps(selfmanaged_accuracies, indent=2))
                if selfmanaged_accuracies:final_data_to_save.update({"Selfmanaged Table Accuracies":selfmanaged_accuracies})
            #-------------------------Cloudquery Accuracies----------------------------
            if variables["load_type"] in ["CloudQuery","osquery_cloudquery_combined","all_loads_combined"]:
                stack_obj.log.info("******* Calculating accuracies for cloudquery Load...")
                cloud_accuracy_obj= cloud_accuracy(stack_obj=stack_obj,variables=variables)
                cloudquery_accuracies = cloud_accuracy_obj.calculate_accuracy()
                if cloudquery_accuracies:final_data_to_save.update({"Cloudquery Table Accuracies":cloudquery_accuracies})
            #-------------------------Azure Load Accuracies----------------------------
            if variables["load_name"] == "Azure_MultiCustomer" or variables["load_type"] in ["all_loads_combined"]:
                stack_obj.log.info("******* Calculating accuracies for Azure Load ...")
            #--------------------------------------Events Counts--------------------------------------
            if variables["load_type"] in ["CloudQuery","osquery_cloudquery_combined","all_loads_combined"]:
                stack_obj.log.info("******* Calculating the counts of various events during the load ...")
                calc = events_count_class(variables=variables,stack_obj=stack_obj)
                evecount = calc.get_events_count()
                if evecount:final_data_to_save.update({"Cloudquery Event Counts":evecount})
            #--------------------------------------STS Records-------------------------------------------
            # if variables["load_name"] == "AWS_MultiCustomer":
            #     print("Calculating STS Records ...")
            #     calc = STS_RECORDS(start_timestamp=stack_obj.start_time_UTC,end_timestamp=stack_obj.end_time_UTC,stack_obj=stack_obj,variables=variables)
            #     sts = calc.calc_stsrecords()
            #     if sts:final_data_to_save.update({"STS Records":sts})
            #-----------------------------Processing Time for Db Operations------------------------------
            if variables["load_type"] in ["CloudQuery","osquery_cloudquery_combined","all_loads_combined"]:
                stack_obj.log.info("******* Processing time for Db Operations ...")
                calc = DB_OPERATIONS_TIME(stack_obj=stack_obj)
                db_op=calc.db_operations()
                if db_op:final_data_to_save.update({"Cloudquery Db Operations Processing Time":db_op})
            #--------------------------------Elk Erros------------------------------------------------
            if "elastic" in test_env_json_details:
                stack_obj.log.info("******* Fetching Elk Errors ...")
                elk = elk_errors_class(stack_obj=stack_obj,elastic_ip=test_env_json_details['elastic'])
                elk_errors = elk.fetch_errors()
                if elk_errors:final_data_to_save.update({"ELK Errors":elk_errors})
            #-------------------------Compaction Status----------------------------
            if "elastic" in test_env_json_details:
                stack_obj.log.info("******* Fetching Compaction Status details...")
                compaction = CompactionStatus(stack_obj=stack_obj,elastic_ip=test_env_json_details['elastic'])
                compaction_status = compaction.execute_query()
                if compaction_status:final_data_to_save.update({"Compaction Status":compaction_status})
            #-------------------------------PG Stats Calculations -------------------------------------
            stack_obj.log.info("******* Calculating Postgress Tables Details ...")
            pgtable = pg_stats_class(stack_obj=stack_obj)
            pg_stats = pgtable.process_output()
            if pg_stats:final_data_to_save.update({"PG Stats":pg_stats})
            #--------------------------------cpu and mem node-wise---------------------------------------
            stack_obj.log.info("******* Calculating resource utilizations ...")
            comp = mem_cpu_usage_class(stack_obj=stack_obj,include_nodetypes=load_cls.hostname_types)
            mem_cpu_usages_dict,overall_usage_dict=comp.make_comparisions(load_cls.common_app_names,load_cls.common_pod_names)
            if overall_usage_dict:final_data_to_save.update(overall_usage_dict)
            if mem_cpu_usages_dict:final_data_to_save.update(mem_cpu_usages_dict)
            #--------------------------------complete resource extraction---------------------------------------
            stack_obj.log.info("******* [NEW] Calculating complete resource utilizations ...")
            resource_obj=complete_resource_usages(stack_obj,include_nodetypes=load_cls.hostname_types)
            complete_resource_details=resource_obj.get_complete_result()
            if complete_resource_details:final_data_to_save.update(complete_resource_details)
            #------------------------------- (NEW) API load report link--------------------------------------------------
            if apiload_remote_directory_name and 'apiload_simulator_ip' in test_env_json_details and apiload_remote_directory_name!="":
                final_data_to_save.update({"Api load report link":os.path.join(f"http://{test_env_json_details['apiload_simulator_ip']}:{API_REPORT_PORT}",apiload_remote_directory_name,f"index.html")})
            #------------------------------- observations --------------------------------------------------
            final_data_to_save.update({"observations":load_cls.get_dictionary_of_observations()})
            #--------------------------------Capture charts data---------------------------------------
            try:
                step_factor=hours/10 if hours>10 else 1
                fs = GridFS(db)
                stack_obj.log.info("******* Fetching charts data ...")
                charts_obj = Charts(stack_obj=stack_obj,fs=fs)
                complete_charts_data_dict,all_gridfs_fileids=charts_obj.capture_charts_and_save(load_cls.get_all_chart_queries(),step_factor=step_factor)
                stack_obj.log.info("charts data fetched successfully !")
                if complete_charts_data_dict:final_data_to_save.update({"charts":complete_charts_data_dict})

                # final_data_to_save.update({"all_gridfs_referenced_ids":all_gridfs_fileids})
                
                #--------------------------------Saving report data to mongodb---------------------------------------
                stack_obj.log.info("******* Saving report data to mongodb ...")
                inserted_id = collection.insert_one(final_data_to_save).inserted_id
                stack_obj.log.info(f"Document pushed to mongo successfully into database:{database_name}, collection:{collection_name} with id {inserted_id}")
                #---------------CREATING GRAPHS-----------------
                graphs_path=f"{BASE_GRAPHS_PATH}/{database_name}/{collection_name}/{inserted_id}"
                os.makedirs(graphs_path,exist_ok=True)
                try:
                    stack_obj.log.info("******* Generating graphs from the saved charts data ...")
                    try:
                        test_title = "Test title : "+str(load_cls.get_load_specific_details(variables['load_name'])['test_title'])
                    except:
                        test_title=""
                    create_images_and_save(graphs_path,inserted_id,collection,fs,variables=variables,end_time_str=stack_obj.end_time_str_ist,run=run,stack=stack,test_title=test_title,step_factor=step_factor,stack_obj=stack_obj)
                    stack_obj.log.info("Done!")
                except Exception as e:
                    stack_obj.log.error(f"Error while generating graphs into {graphs_path} : {str(e)}")

                # ----------------CREATING PG BADGER GRAPHS--------------
                # try:
                #     print("Capturing details from PG Badger ... ")
                #     pg_badger_result=None
                #     category_name="PG Badger Charts"
                #     pg_badger_images_path = os.path.join(graphs_path,category_name)
                #     os.makedirs(pg_badger_images_path,exist_ok=True)
                #     pg_badger_result = return_pgbadger_results(stack_obj.start_time_UTC,stack_obj.end_time_UTC,test_env_json_details['elastic'],pg_badger_images_path)
                #     collection.update_one({"_id": ObjectId(inserted_id)}, {"$set": {f"charts.{category_name}": pg_badger_result}})
                # except Exception as e:
                #     print(f"ERROR occured while processing pg badger details : {e}")

                try:
                    stack_obj.log.info("******* Generating PGBadger reports ...")
                    pgbadger_tail_path=f"{database_name}/{collection_name}/{inserted_id}/pgbadger_reports"
                    curr_pgbad_html_path=f"{BASE_HTMLS_PATH}/{pgbadger_tail_path}"
                    stack_obj.log.info(f'Saving the html page to {curr_pgbad_html_path}')
                    os.makedirs(curr_pgbad_html_path,exist_ok=True)
                    pgbadger_links,extracted_tables=get_and_save_pgb_html(stack_obj,test_env_json_details['elastic'],curr_pgbad_html_path,pgbadger_tail_path,test_env_json_details['pgbadger_reports_mount'])
                    collection.update_one({"_id": ObjectId(inserted_id)}, {"$set": {f"Pgbadger downloaded report links": pgbadger_links}})
                    if extracted_tables!={}:
                        stack_obj.log.info("Empty extracted tables dictionary found !")
                        collection.update_one({"_id": ObjectId(inserted_id)}, {"$set": {f"Postgres Queries Analysis": extracted_tables}})

                except Exception as e:
                    stack_obj.log.error(f"error occured while processing pg badger reports : {e}")

                #---------------FETCHING PDFS-----------------
                try:
                    if presto_load_result_dict:
                        stack_obj.log.info(f"------------------------------ Fetching presto load charts pdf from {test_env_json_details['prestoload_simulator_ip']}:{benchto_load_csv_path}")
                        presto_load_local_pdf_path=f"{BASE_PDFS_PATH}/{database_name}/{collection_name}/{inserted_id}/Presto Load Charts pdf.pdf"
                        stack_obj.log.info(f'Saving the presto load pdf to {presto_load_local_pdf_path}')
                        os.makedirs(os.path.dirname(presto_load_local_pdf_path),exist_ok=True)
                        fetch_and_save_pdf(benchto_load_pdf_path,test_env_json_details['prestoload_simulator_ip'],presto_load_local_pdf_path,stack_obj)
                except Exception as e:
                    stack_obj.log.error(f"error while fetching pdfs : {str(e)}")

            except Exception as e:
                stack_obj.log.error(f"Failed to insert document into database {database_name}, collection:{collection_name} , {str(e)}")
                stack_obj.log.info("******* Deleting stored chart data ...")
                for file_id in all_gridfs_fileids:
                    stack_obj.log.info(f"deleting {file_id}")
                    fs.delete(file_id=file_id)
            finally:
                f3_at = time.perf_counter()
                stack_obj.log.info(f"------------------------------ Collecting the report data took : {round(f3_at - s_at,2)} seconds in total")
                client.close()
    except Exception as e:
        stack_obj.log.exception(e)
        raise RuntimeError from e