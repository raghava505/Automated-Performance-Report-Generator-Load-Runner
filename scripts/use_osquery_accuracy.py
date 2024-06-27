from osquery.accuracy import osq_accuracy
from settings import stack_configuration
import json

variables = {
        "start_time_str_ist":"2024-06-26 12:55",
        "load_duration_in_hrs":1,
        "test_env_file_name":'s1_nodes.json'
    }

stack_json_file = variables["test_env_file_name"]

if "longevity" in stack_json_file:
    api_file = "longevity"
    assets_per_cust= 80
    domain='longevity48'
    extension='net'
    alert_rules_triggered_per_cust=12
    event_rules_triggered_per_cust=33  
    input_file_path="inputFile6tab_12rec.log"
elif "s1" in stack_json_file:
    api_file = "jupiter"
    assets_per_cust= 100
    domain='jupiter48'
    extension='net'
    alert_rules_triggered_per_cust=16
    event_rules_triggered_per_cust=34  
    input_file_path="inputFile6tab_12rec.log"

input_file_path = f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/osquery/testinputfiles/{input_file_path}"
print(input_file_path)
api_path = f'/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/osquery/api_keys/{api_file}.json'

stack_obj=stack_configuration(variables)
accuracy_obj= osq_accuracy(stack_obj,api_path=api_path,domain=domain,assets_per_cust=assets_per_cust,ext=extension,trans=True,input_file=input_file_path)

stack_obj.log.info("Calculating Table accuracies for Osquery Load...")
Osquery_table_accuracies = accuracy_obj.table_accuracy()
stack_obj.log.info(f"Osquery_table_accuracies : {json.dumps(Osquery_table_accuracies,indent=4)}")

stack_obj.log.info("Calculating Events accuracies for Osquery Load ...")
Osquery_event_accuracies = accuracy_obj.events_accuracy(alert_rules_triggered_per_cust,event_rules_triggered_per_cust)
stack_obj.log.info(f"Osquery_event_accuracies : {json.dumps(Osquery_event_accuracies,indent=4)}")





