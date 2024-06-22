import sys
import time
import pymongo
import json
from memory_and_cpu_usages import MC_comparisions
from osquery.add_kafka_topics import kafka_topics
from disk_space import DISK
from input import create_input_form
from capture_charts_data import Charts
from gridfs import GridFS
from elk_errors import Elk_erros
from cloudquery.accuracy import ACCURACY
from compaction_status import CompactionStatus
from osquery.accuracy import osq_accuracy
from kubequery.kube_accuracy import Kube_Accuracy
from kubequery.selfmanaged_accuracy import SelfManaged_Accuracy
from pg_stats import PG_STATS
from cloudquery.db_operations_time import DB_OPERATIONS_TIME
from cloudquery.events_count import EVE_COUNTS
from cloudquery.sts_records import STS_RECORDS
import os
from create_chart import create_images_and_save
from trino_queries_analysis import TRINO_ANALYSE
from active_conn_by_apps import Active_conn
from bson import ObjectId
from pg_badger import return_pgbadger_results,get_and_save_pgb_html
from extract_and_preprocess_resource_utilizations import resource_usages
from config_vars import *
from load_params import Load_Params
from extract_stack_details import extract_ram_cores_storage_details
from helper import fetch_and_save_pdf,fetch_and_extract_csv

if __name__ == "__main__":
    variables , stack_obj,load_cls = create_input_form()
    if not variables or not stack_obj : 
        print("Received NoneType objects, terminating the program ...")
        sys.exit()
    
    #---------------------logging and opening stack file-------------------
    s_at = time.perf_counter()
   
    with open(stack_obj.test_env_file_path , 'r') as file:
        test_env_json_details = json.load(file)
    skip_fetching_data=False
    stack = test_env_json_details["stack"]
    #---------------------Check for previous runs------------------------------------
    client = pymongo.MongoClient(mongo_connection_string)
    database_name = variables['load_type']+"_LoadTests"
    collection_name = variables["load_name"]
    db=client[database_name]
    collection = db[collection_name]

    documents_with_same_load_time_and_stack = collection.find({"load_details.sprint":variables['sprint'] ,"load_details.stack":stack , "load_details.load_start_time_ist":f"{variables['start_time_str_ist']}" , "load_details.load_duration_in_hrs":variables['load_duration_in_hrs']})
    if len(list(documents_with_same_load_time_and_stack)) > 0:
        print(f"ERROR! A document with load time ({variables['start_time_str_ist']}) - ({stack_obj.end_time_str_ist}) on {stack} for this sprint for {database_name}-{collection_name} load is already available.")
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

        #all result variables
        realtime_query_results=None
        disk_space_usage_dict=None
        kafka_topics_list=None
        active_conn_results=None
        trino_queries_analyse_results=None
        # api_load_result_dict=None
        presto_load_result_dict=None
        Osquery_table_accuracies=None
        Osquery_event_accuracies=None
        kubequery_accuracies=None
        selfmanaged_accuracies=None
        azure_accuracies=None
        evecount = None
        sts = None
        db_op = None
        pg_stats = None
        elk_errors = None
        mem_cpu_usages_dict,overall_usage_dict = None,None
        complete_resource_details=None
        cloudquery_accuracies=None
        complete_charts_data_dict=None
        all_gridfs_fileids=[]
        compaction_status = None
        params = None
        
        api_load_folder_name=str(variables["apiload_remote_directory_name"]).strip()

        #stack details variables
        domain = test_env_json_details['domain']
        extension = str(test_env_json_details['suffix']).split('.')[1]

        # get necessary load parameters
        if variables["load_name"] in ["KubeQuery_SingleCustomer","SelfManaged_SingleCustomer","KubeQuery_and_SelfManaged_Combined"] or variables["load_type"] in ["all_loads_combined"]:
            load_params = Load_Params(connection_object=stack_obj)
            load_name = variables["load_name"]
            params = {
                "KubeQuery_SelfManaged_Load_Details" : load_params.get_load_params(load_name=load_name)
            }
            print(json.dumps(params, indent=4))

        if 'elastic' in test_env_json_details and 'pgbadger_reports_mount' in test_env_json_details:
            print("\n\n------------------------------ \nChecking health of PGbadger ... \n\n")
            status,link=get_and_save_pgb_html(stack_obj,test_env_json_details['elastic'],"curr_pgbad_html_path","pgbadger_tail_path",test_env_json_details['pgbadger_reports_mount'],check=True)
            if not status:
                print("PGBadger seems to be not working in your stack. Please try to generate a pgbadger report manually to check if working fine.")
                print("Here is the sample report generated through automation just now : " , link)
                user_decision = input("Continue without pgbadger details in the report? (y/n) : ")
                if user_decision == "y":
                    pass
                else:
                    print("Terminating program ...")
                    sys.exit()
            else:
                print("\nCHECK PASSED : PGbadger is in good condition !")
                print("--------------------------------------\n")


        #-------------------------real time query test details--------------------------
        # if domain=="longevity" and variables["load_type"] in ["all_loads_combined"]: 
        #     from realtimequery_tests.real_time_query import realtime_query
        #     print(f"Performing realtime query test on stack '{stack}' ...")
        #     realtime_query_results=realtime_query()
        #-------------------------disk space--------------------------
        if variables["load_name"] != "ControlPlane":
            print("Performing disk space calculations ...")
            calc = DISK(stack_obj=stack_obj)
            disk_space_usage_dict=calc.make_calculations()
        #--------------------------------- add kafka topics ---------------------------------------
        if variables["load_type"] in ["Osquery","osquery_cloudquery_combined","all_loads_combined"]:
            print("Fetching kafka topics ...")
            kafka_obj = kafka_topics(stack_obj.execute_kafka_topics_script_in)
            kafka_topics_list = kafka_obj.add_topics_to_report()
        #---------------No.of Active connections by application---------------
        active_conn_obj = Active_conn(stack_obj=stack_obj)
        active_conn_results = active_conn_obj.get_avg_active_conn()
        #-------------------------Trino Queries--------------------------
        print("Fetching Trino queries details ...")
        trino_obj = TRINO_ANALYSE(stack_obj=stack_obj)
        trino_queries_analyse_results = trino_obj.fetch_trino_results()
        #-------------------------Presto LOAD--------------------------
        if 'prestoload_simulator_ip' in test_env_json_details:
            print(f"Looking for presto load csv files in {test_env_json_details['prestoload_simulator_ip']}")
            stack_starttime_string=str(stack).lower() + "-" + str(variables["start_time_str_ist"])
            # api_load_csv_path = os.path.join(api_loads_folder_path , stack_starttime_string+".csv")
            benchto_load_csv_path=os.path.join(presto_loads_folder_path, stack_starttime_string, "benchto.csv")
            benchto_load_pdf_path=os.path.join(presto_loads_folder_path , stack_starttime_string, "Benchto.pdf")
            # print("CSV file path for API/Jmeter load : " , api_load_csv_path)
            # api_load_result_dict = fetch_and_extract_csv(api_load_csv_path,test_env_json_details['prestoload_simulator_ip'])
            print("CSV file path for Presto/benchto load : " , benchto_load_csv_path)
            presto_load_result_dict = fetch_and_extract_csv(benchto_load_csv_path,test_env_json_details['prestoload_simulator_ip'])

        else:
            print(f"Skipping API load details because 'prestoload_simulator_ip' is not present in stack json file")

        #-------------------------Osquery Table Accuracies----------------------------
        if variables["load_type"] in ["Osquery","osquery_cloudquery_combined","all_loads_combined"] and variables["load_name"] != "ControlPlane":
            assets_per_cust=int(load_cls.get_load_specific_details(variables['load_name'])["RuleEngine and ControlPlane Load Details"]['assets_per_cust'])
            input_file = load_cls.get_load_specific_details(variables['load_name'])["RuleEngine and ControlPlane Load Details"]['input_file']
            alert_rules_triggered_per_cust=test_env_json_details['alert_rules_per_cust']['triggered']
            event_rules_triggered_per_cust=test_env_json_details['event_rules_per_cust']['triggered']
            print("Calculating Table accuracies for Osquery Load...")
            api_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),f"osquery/api_keys/{domain}.json")
            input_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),f"osquery/testinputfiles/{input_file}")
            print("Printing osquery accuracy calculation details : ")
            print("Assets per customer value : ", assets_per_cust)
            print("Input file path : ", input_file_path)
            print("stack customers file path : ", api_path)
            accuracy_obj= osq_accuracy(stack_obj,api_path=api_path,domain=domain,assets_per_cust=assets_per_cust,ext=extension,trans=True,input_file=input_file_path)
            Osquery_table_accuracies = accuracy_obj.table_accuracy()
            print("Osquery_table_accuracies : ",Osquery_table_accuracies)
            if input_file != "inputFile6tab_12rec.log":
                print("Calculating Events accuracies for Osquery Load ...")
                Osquery_event_accuracies = accuracy_obj.events_accuracy(alert_rules_triggered_per_cust,event_rules_triggered_per_cust)
                print("Osquery_event_accuracies : ",Osquery_event_accuracies)
        

        #-------------------------Kubequery Accuracies----------------------------
        if variables["load_name"] in ["KubeQuery_SingleCustomer","KubeQuery_and_SelfManaged_Combined"] or variables["load_type"] in ["all_loads_combined"]:
            print("Calculating accuracies for KubeQuery ...")
            accuracy = Kube_Accuracy(stack_obj=stack_obj)
            kubequery_accuracies = accuracy.accuracy_kubernetes()
            print(json.dumps(kubequery_accuracies, indent=2))

        #-------------------------SelfManaged Accuracies----------------------------
        if variables["load_name"] in ["SelfManaged_SingleCustomer","KubeQuery_and_SelfManaged_Combined"] or variables["load_type"] in ["all_loads_combined"]:
            print("Calculating accuracies for SelfManaged ...")
            accuracy = SelfManaged_Accuracy(stack_obj=stack_obj)
            selfmanaged_accuracies = accuracy.accuracy_selfmanaged()
            print(json.dumps(selfmanaged_accuracies, indent=2))

        #-------------------------Azure Load Accuracies----------------------------
        if variables["load_name"] == "Azure_MultiCustomer" or variables["load_type"] in ["all_loads_combined"]:
            print("Calculating accuracies for Azure Load ...")
        
        #--------------------------------------Events Counts--------------------------------------
        if variables["load_type"] in ["CloudQuery","osquery_cloudquery_combined","all_loads_combined"]:
            print("Calculating the counts of various events during the load ...")
            calc = EVE_COUNTS(variables=variables)
            evecount = calc.get_events_count()

        #--------------------------------------STS Records-------------------------------------------
        # if variables["load_name"] == "AWS_MultiCustomer":
        #     print("Calculating STS Records ...")
        #     calc = STS_RECORDS(start_timestamp=stack_obj.start_time_UTC,end_timestamp=stack_obj.end_time_UTC,stack_obj=stack_obj,variables=variables)
        #     sts = calc.calc_stsrecords()


        #-----------------------------Processing Time for Db Operations------------------------------
        if variables["load_type"] in ["CloudQuery","osquery_cloudquery_combined","all_loads_combined"]:
            print("Processing time for Db Operations ...")
            calc = DB_OPERATIONS_TIME(stack_obj=stack_obj)
            db_op=calc.db_operations()

        #-------------------------------PG Stats Calculations -------------------------------------
        print("Calculating Postgress Tables Details ...")
        pgtable = PG_STATS(stack_obj=stack_obj)
        pg_stats = pgtable.process_output()

        #--------------------------------Elk Erros------------------------------------------------
        print("Fetching Elk Errors ...")
        if "elastic" in test_env_json_details:
            elk = Elk_erros(stack_obj=stack_obj,elastic_ip=test_env_json_details['elastic'])
            elk_errors = elk.fetch_errors()
        
        #--------------------------------cpu and mem node-wise---------------------------------------
        print("Fetching resource usages data ...")
        comp = MC_comparisions(stack_obj=stack_obj,include_nodetypes=load_cls.hostname_types)
        mem_cpu_usages_dict,overall_usage_dict=comp.make_comparisions(load_cls.common_app_names,load_cls.common_pod_names)
        
        #--------------------------------complete resource extraction---------------------------------------
        resource_obj=resource_usages(stack_obj,include_nodetypes=load_cls.hostname_types)
        complete_resource_details=resource_obj.get_complete_result()

        #-------------------------Cloudquery Accuracies----------------------------
        if variables["load_type"] in ["CloudQuery","osquery_cloudquery_combined","all_loads_combined"]:
            print("Calculating accuracies for cloudquery ...")
            accu= ACCURACY(stack_obj=stack_obj,variables=variables)
            cloudquery_accuracies = accu.calculate_accuracy()

        #-------------------------Compaction Status----------------------------
        print("Fetching Compaction Status ...")
        if "elastic" in test_env_json_details:
            compaction = CompactionStatus(stack_obj=stack_obj,elastic_ip=test_env_json_details['elastic'])
            compaction_status = compaction.execute_query()
        
        #--------------------------------Capture charts data---------------------------------------
        try:
            hours=variables["load_duration_in_hrs"]
            step_factor=hours/10 if hours>10 else 1
            fs = GridFS(db)
            print("Fetching charts data ...")
            charts_obj = Charts(stack_obj=stack_obj,fs=fs)
            complete_charts_data_dict,all_gridfs_fileids=charts_obj.capture_charts_and_save(load_cls.get_all_chart_queries(),step_factor=step_factor)
            print("Saved charts data successfully !")
            #--------------------------------take screenshots---------------------------------------
            # print("Capturing compaction status screenshots  ...")
            # cp_obj = take_screenshots(start_time=start_time,end_time=end_time,fs=fs,elk_url=test_env_json_details["elk_url"])
            # compaction_status_image=cp_obj.get_compaction_status()
            #-------------------------- Saving the json data to mongo -------------------------
            print("Saving data to mongoDB ...")
            load_details =  {
                "stack":stack,
                "stack_url":str(test_env_json_details["domain"])+"."+str(test_env_json_details["suffix"]),
                "architecture":test_env_json_details["architecture"],
                "sprint": variables['sprint'],
                "build": variables['build'],
                "load_name":variables['load_name'],
                "load_type":variables['load_type'],
                "load_duration_in_hrs":variables['load_duration_in_hrs'],
                "load_start_time_utc" : stack_obj.start_time_str_utc,
                "load_end_time_utc" : stack_obj.end_time_str_utc,
                "load_start_time_ist" : variables['start_time_str_ist'],
                "load_end_time_ist" : stack_obj.end_time_str_ist,
                "run":run,
                }
            try:
                load_details.update(load_cls.get_load_specific_details(variables['load_name']))
            except:
                print(f"WARNING : Load specific details for {variables['load_name']} in {load_cls} is not found!")

            try:
                if params:
                    if "KubeQuery Load Details" in load_details:
                        load_details["KubeQuery Load Details"].update(params)
                    else:
                        load_details.update(params)
            except Exception as err:
                print(f"ERR : load_details.update(params) => {err}")

            final_data_to_save = {
                "load_details":load_details,
                # "test_environment_details":test_env_json_details,
                "Test environment details": extract_ram_cores_storage_details(stack_obj)
            }
            if overall_usage_dict:
                final_data_to_save.update(overall_usage_dict)
            if disk_space_usage_dict:
                final_data_to_save.update({"disk_space_usages":disk_space_usage_dict})
            if kafka_topics_list:
                final_data_to_save.update({"kafka_topics":kafka_topics_list})
            if evecount:
                final_data_to_save.update({"Cloudquery Event Counts":evecount})
            if sts:
                final_data_to_save.update({"STS Records":sts})
            if trino_queries_analyse_results:
                final_data_to_save.update({"Trino Queries Analysis":trino_queries_analyse_results})
            if active_conn_results:
                final_data_to_save.update({"Number of active connections group by application on master":active_conn_results})
            if cloudquery_accuracies:
                final_data_to_save.update({"Cloudquery Table Accuracies":cloudquery_accuracies})
            if compaction_status:
                final_data_to_save.update({"Compaction Status":compaction_status})
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
            # if api_load_result_dict:
            #     final_data_to_save.update({"API Load details":api_load_result_dict})
            if presto_load_result_dict:
                final_data_to_save.update({"Presto Load details":presto_load_result_dict})
            if realtime_query_results:
                final_data_to_save.update({"Realtimequery test results":realtime_query_results})
            if complete_resource_details:
                final_data_to_save.update(complete_resource_details)
            if complete_charts_data_dict:
                final_data_to_save.update({"charts":complete_charts_data_dict})
            if mem_cpu_usages_dict:
                final_data_to_save.update(mem_cpu_usages_dict)
            if api_load_folder_name and 'apiload_simulator_ip' in test_env_json_details and api_load_folder_name!="":
                final_data_to_save.update({"Api load report link":os.path.join(f"http://{test_env_json_details['apiload_simulator_ip']}:{api_report_port}",api_load_folder_name,f"index.html")})
            final_data_to_save.update({"observations":load_cls.get_dictionary_of_observations()})
            # all_gridfs_referenced_ids=all_gridfs_fileids[:]
            # final_data_to_save.update({"all_gridfs_referenced_ids":all_gridfs_referenced_ids})
            inserted_id = collection.insert_one(final_data_to_save).inserted_id
            print(f"Document pushed to mongo successfully into database:{database_name}, collection:{collection_name} with id {inserted_id}")
            
            graphs_path=f"{BASE_GRAPHS_PATH}/{database_name}/{collection_name}/{inserted_id}"
            os.makedirs(graphs_path,exist_ok=True)
            #---------------CREATING GRAPHS-----------------
            try:
                print("Generating graphs from the saved data ...")
                try:
                    test_title = "Test title : "+str(load_cls.get_load_specific_details(variables['load_name'])['test_title'])
                except:
                    test_title=""
                create_images_and_save(graphs_path,inserted_id,collection,fs,variables=variables,end_time_str=stack_obj.end_time_str_ist,run=run,stack=stack,test_title=test_title,step_factor=step_factor)
                print("Done!")
            except Exception as e:
                print(f"Error while generating graphs into {graphs_path} : {str(e)}")

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
                print("Capturing details from PG Badger ... ")
                pgbadger_tail_path=f"{database_name}/{collection_name}/{inserted_id}/pgbadger_reports"
                curr_pgbad_html_path=f"{BASE_HTML_PATH}/{pgbadger_tail_path}"
                print(f'Saving the html page to {curr_pgbad_html_path}')
                os.makedirs(curr_pgbad_html_path,exist_ok=True)
                pgbadger_links,extracted_tables=get_and_save_pgb_html(stack_obj,test_env_json_details['elastic'],curr_pgbad_html_path,pgbadger_tail_path,test_env_json_details['pgbadger_reports_mount'])
                collection.update_one({"_id": ObjectId(inserted_id)}, {"$set": {f"Pgbadger downloaded report links": pgbadger_links}})
                if extracted_tables!={}:
                    print("Empty extracted tables dictionary found !")
                    collection.update_one({"_id": ObjectId(inserted_id)}, {"$set": {f"Postgres Queries Analysis": extracted_tables}})

            except Exception as e:
                print(f"ERROR occured while processing pg badger details : {e}")

            #---------------FETCHING PDFS-----------------
            try:
                if presto_load_result_dict:
                    print(f"Fetching presto load charts pdf from {test_env_json_details['prestoload_simulator_ip']}:{benchto_load_csv_path}")
                    presto_load_local_pdf_path=f"{BASE_PDFS_PATH}/{database_name}/{collection_name}/{inserted_id}/Presto Load Charts pdf.pdf"
                    print(f'Saving the presto load pdf to {presto_load_local_pdf_path}')
                    os.makedirs(os.path.dirname(presto_load_local_pdf_path),exist_ok=True)
                    fetch_and_save_pdf(benchto_load_pdf_path,test_env_json_details['prestoload_simulator_ip'],presto_load_local_pdf_path)
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
    
