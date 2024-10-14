from osquery.accuracy import osq_accuracy
from settings import stack_configuration
import json

variables = {
        "start_time_str_ist":"2024-10-14 21:20",
        "load_duration_in_hrs":0.5,
        "test_env_file_name":'longevity_nodes.json'
    }

stack_json_file = variables["test_env_file_name"]

if "longevity_nodes" in stack_json_file:
    api_file = "longevity"
    assets_per_cust= 100
    base_domain='longevity'
    extension='net'
    alert_rules_triggered_per_cust=12
    event_rules_triggered_per_cust=33  
    input_file_path="rhel7-6tab_12rec.log"
elif "s1_nodes" in stack_json_file:
    api_file = "jupiter"
    assets_per_cust= 100
    base_domain='jupiter'
    extension='net'
    alert_rules_triggered_per_cust=16
    event_rules_triggered_per_cust=34  
    # input_file_path="inputFile6tab_12rec.log"
    # input_file_path = "process_events_targeted_all_str.log"
    input_file_path="rhel7-6tab_12rec.log"
elif "s12_nodes" in stack_json_file:
    api_file = "milkyway"
    assets_per_cust= 112
    base_domain='milkyway'
    extension='net'
    alert_rules_triggered_per_cust=28
    event_rules_triggered_per_cust=39  
    input_file_path="rhel7-6tab_12rec.log"

input_file_path = f"scripts/osquery/testinputfiles/{input_file_path}"
print(input_file_path)
api_path = f'scripts/osquery/api_keys/{api_file}.json'

stack_obj=stack_configuration(variables)

for i in range(4):
    if i!=0:
        domain = base_domain+str(i)
    else:
        domain = base_domain
    accuracy_obj= osq_accuracy(stack_obj,api_path=api_path,domain=domain,assets_per_cust=assets_per_cust,ext=extension,trans=True,input_file=input_file_path)

    stack_obj.log.info("Calculating Table accuracies for Osquery Load...")
    Osquery_table_accuracies = accuracy_obj.table_accuracy()
    # stack_obj.log.info(f"Osquery_table_accuracies : {json.dumps(Osquery_table_accuracies,indent=4)}")

    stack_obj.log.info("Calculating Events accuracies for Osquery Load ...")
    # print("*********************** Accuracies for customer : " , domain)
    Osquery_event_accuracies = accuracy_obj.events_accuracy(alert_rules_triggered_per_cust,event_rules_triggered_per_cust)
    print("*********************** Accuracies for customer : " , domain , ", are printed above")
    # stack_obj.log.info(f"Osquery_event_accuracies : {json.dumps(Osquery_event_accuracies,indent=4)}")


#TEST1
#select count(*),code from upt_events where upt_day>= 20240709 and created_at >= timestamp '2024-07-09 09:00' and created_at < timestamp '2024-07-09 14:00' and code like '%-builder-added%' group by code;

#TEST3
#select count(*),code from upt_events where upt_day>= 20240709 and created_at >= timestamp '2024-07-09 14:00' and created_at < timestamp '2024-07-09 18:00' and code like '%-builder-added%' group by code