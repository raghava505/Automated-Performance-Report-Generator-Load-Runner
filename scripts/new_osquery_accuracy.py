from datetime import datetime, timedelta
import os, json
from config_vars import INPUTFILES_METADATA_PATH, DELAY_BETWEEN_TRIGGER_TO_USE_FOR_ACCURACIES
from helper import execute_trino_query, execute_configdb_query
from settings import stack_configuration
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import math, re

class osquery_accuracy:
    def __init__(self, stack_obj, assets_per_cust_dict, trans, input_file):
        
        file_name_without_suffix = os.path.splitext(os.path.basename(input_file))[0]
        metadata_filepath = os.path.join(INPUTFILES_METADATA_PATH, file_name_without_suffix+".json")

        self.continue_to_calculate_accuracy = True
        
        if os.path.exists(metadata_filepath):
            with open(metadata_filepath, "r") as m_f:
                self.metadata_contents = json.load(m_f)

            self.number_of_msgs_this_inputfile_contains = self.metadata_contents["number_of_msgs_this_inputfile_contains"]
            number_of_msgs_sent = stack_obj.hours * 60 *60 / DELAY_BETWEEN_TRIGGER_TO_USE_FOR_ACCURACIES
            print(number_of_msgs_sent)
            if number_of_msgs_sent % self.number_of_msgs_this_inputfile_contains == 0:
                self.iterations_made_by_input_file = number_of_msgs_sent // self.number_of_msgs_this_inputfile_contains 
                self.assets_per_cust_dict=assets_per_cust_dict
                self.trans=trans
                self.input_file=input_file

                start_time_utc=stack_obj.start_time_UTC
                end_time_utc=stack_obj.end_time_UTC
                format_data = "%Y-%m-%d %H:%M"
                start_time = start_time_utc - timedelta(minutes=20)
                self.start_time = start_time.strftime(format_data)
                end_time = end_time_utc + timedelta(minutes=40)
                self.end_time = end_time.strftime(format_data)
                self.stack_obj = stack_obj
                self.hours = stack_obj.hours


                self.upt_day="".join(str(start_time_utc.strftime("%Y-%m-%d")).split('-'))

                self.expected_records_for_each_table_per_asset = self.metadata_contents["expected_records_for_each_table"]
                expected_events_count_per_asset = self.metadata_contents["expected_events_counts"]
                self.expected_events_df = pd.DataFrame(list(expected_events_count_per_asset.items()), columns=["code", "expected"])

                self.expected_records_for_each_table_per_asset["process_open_sockets"] += self.expected_records_for_each_table_per_asset["process_open_sockets_local"] + self.expected_records_for_each_table_per_asset["process_open_sockets_remote"]
                self.expected_records_for_each_table_per_asset.pop("process_open_sockets_local")
                self.expected_records_for_each_table_per_asset.pop("process_open_sockets_remote")


                self.all_tables = list(self.expected_records_for_each_table_per_asset.keys())

        else:
            print("Accuracy cannot be calculated because the inputfile was not iterated completely")
            self.continue_to_calculate_accuracy = False
        
    def calculate_hdfs_tables_accuracy(self):
        table_accuracies_for_each_domain = {}

        def fetch_table_data(domain, assets, table):
            """Helper function to execute the query and process result"""
            query = "select count(*) from {} where upt_day>={} and upt_time >= timestamp '{}' and upt_time < timestamp '{}'".format(
                table, self.upt_day, self.start_time, self.end_time
            )
            actual = execute_trino_query(stack_obj.first_pnode, query, stack_obj=stack_obj, schema=domain)

            # Clean and validate the result
            clean_actual = actual.strip('"').strip()
            clean_actual = int(clean_actual) if clean_actual.isdigit() else 0

            return table, {
                "expected": self.expected_records_for_each_table_per_asset[table] * assets * self.iterations_made_by_input_file,
                "actual": clean_actual,
            }

        for domain, assets in self.assets_per_cust_dict.items():
            result_single_domain = {}

            # for table in self.all_tables[:10]:
            #     query="select count(*) from {} where upt_day>={} and upt_time >= timestamp '{}' and upt_time < timestamp '{}'".format(table,self.upt_day,self.start_time,self.end_time)
            #     actual = execute_trino_query(stack_obj.first_pnode, query, stack_obj=stack_obj, schema=domain)

            #     # Clean and validate the result
            #     clean_actual = actual.strip('"').strip()  # Remove surrounding quotes and extra spaces

            #     # Handle different cases
            #     if not clean_actual or not clean_actual.isdigit():
            #         clean_actual = 0  # Default to 0 for empty or invalid values

            #     result_single_domain[table] = {
            #         "expected": self.expected_records_for_each_table_per_asset[table] * assets * self.iterations_made_by_input_file,
            #         "actual": int(clean_actual)
            #     }
            with ThreadPoolExecutor() as executor:
                # Submit tasks for each table and collect results
                futures = {executor.submit(fetch_table_data, domain, assets, table): table for table in self.all_tables[:10]}

                for future in as_completed(futures):
                    table, result = future.result()
                    result_single_domain[table] = result

            

            # Process results and calculate accuracy
            df = pd.DataFrame(result_single_domain).T
            df["accuracy"] = df["actual"] * 100 / df["expected"]

            print(f"Tables Accuracy for {domain} customer:")
            print(df)

            table_accuracies_for_each_domain[domain] = {
                "format": "table",
                "collapse": True,
                "schema": {
                    "merge_on_cols": [],
                    "compare_cols": [],
                },
                "data": df.to_dict(orient="records"),
            }

        return {
            "format": "nested_table",
            "schema": {"page": "Postgres, Pgbouncer stats"},
            "data": table_accuracies_for_each_domain,
        }

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

    def calculate_events_accuracy(self,alert_rules_triggered_per_cust,event_rules_triggered_per_cust):
        event_accuracies_for_each_domain = {}
        for domain, assets in self.assets_per_cust_dict.items():
            events_tables=["upt_events_data","alerts","incidents"]

            for table in events_tables:
                if table == "upt_events_data":
                    query=f"select code,count(*) from {table} where upt_day>={self.upt_day} and upt_time >= timestamp '{self.start_time}' and upt_time < timestamp '{self.end_time}' and code like '%-builder-added%' group by code"

                    output = execute_trino_query(stack_obj.first_pnode, query, stack_obj=stack_obj, schema=domain)
                    stringio = StringIO(output)
                    actual_events_df = pd.read_csv(stringio, header=None, names=["code","actual"])
                    merged_df = pd.merge(actual_events_df, self.expected_events_df, on='code', how='outer')

                    # Update expected values
                    merged_df["expected"] = merged_df["expected"] * assets * self.iterations_made_by_input_file
                    expected_total = merged_df["expected"].sum()
                    actual_total = merged_df["actual"].sum()
                    
                
                if table == "alerts":
                    # utc_days = self.get_utc_days_involved()
                    # expected_total = alert_rules_triggered_per_cust*1000*(utc_days+1)
                    expected_total = alert_rules_triggered_per_cust * 50 * math.ceil(self.hours)
                    query=f"select count(*) from {table} where  created_at >= timestamp '{self.start_time}' and created_at < timestamp '{self.end_time}' and code like '%-builder-added%' and customer_id=(select id from customers where domain='{domain}')"
                    output = execute_configdb_query(self.stack_obj.configdb_node, query)
                    match = re.search(r"\d+", output)
                    if match:
                        actual_total = int(match.group())
                        print(f"{table} actual count for {domain} : {actual_total}")
                    else:
                        print(f"configdb output for {table} actual count for {domain} not found")
                        actual_total = -1

                if table == "incidents":
                    query=f"select count(*) from {table} where  created_at >= timestamp '{self.start_time}' and created_at < timestamp '{self.end_time}' and customer_id=(select id from customers where domain='{domain}')"
                    output = execute_configdb_query(self.stack_obj.configdb_node, query)
                    match = re.search(r"\d+", output)
                    if match:
                        actual_total = int(match.group())
                        print(f"{table} actual count for {domain} : {actual_total}")
                    else:
                        print(f"configdb output for {table} actual count for {domain} not found")
                        actual_total = -1
                    expected_total = None

                total_row = {
                        "code": f"Total {table} Triggered",
                        "expected": expected_total,
                        "actual": actual_total
                    }

                merged_df = merged_df._append(total_row, ignore_index=True)

            merged_df["accuracy"] = merged_df["actual"] * 100 / merged_df["expected"]
            print(f"Events Accuracy for {domain} customer:")
            print(merged_df)
            event_accuracies_for_each_domain[domain] = {
                "format": "table",
                "collapse": True,
                "schema": {
                    "merge_on_cols": [],
                    "compare_cols": [],
                },
                "data": merged_df.to_dict(orient="records"),
            }

        return {
            "format": "nested_table",
            "schema": {"page": "Postgres, Pgbouncer stats"},
            "data": event_accuracies_for_each_domain,
        }

if __name__ == "__main__":
    variables = {
        "start_time_str_ist":"2025-02-10 20:30",
        "load_duration_in_hrs":10,
        "test_env_file_name":'s1_nodes.json'
    }
    stack_obj=stack_configuration(variables)
    # assets_per_cust_dict = {"jupiter":10, "jupiter1":10,"jupiter2":10, "jupiter3":10,"jupiter4":10}
    assets_per_cust_dict = {"jupiter":10}

    alert_rules_triggered_per_cust=16
    event_rules_triggered_per_cust=34  

    accuracy_obj= osquery_accuracy(stack_obj,assets_per_cust_dict=assets_per_cust_dict,trans=True,input_file="inputfile_10min_150msgs_formed_using_155tables_with_ratio_30:60_6tab_12rec.json")
    if accuracy_obj.continue_to_calculate_accuracy:
        Osquery_table_accuracies = accuracy_obj.calculate_hdfs_tables_accuracy()
        Osquery_event_accuracies = accuracy_obj.calculate_events_accuracy(alert_rules_triggered_per_cust,event_rules_triggered_per_cust)

    # print(result)