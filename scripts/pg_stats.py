import requests
import pandas as pd
from config_vars import *
from helper import execute_point_prometheus_query
from collections import defaultdict

databases = ["configdb","statedb"]
stats= ['table_size_bytes','index_size_bytes','live_tuples']
class pg_stats_class:
    def __init__(self,stack_obj):
        self.stack_obj=stack_obj
        self.start_timestamp=stack_obj.start_timestamp
        self.end_timestamp=stack_obj.end_timestamp
            
    def process_output(self):
        final_result = {}
        for db in databases:
            for stat in stats:
                curr_result=defaultdict(lambda:{})
                query = f'uptycs_pg_stats{{db=~"{db}", stat=~"{stat}"}}'

                results_before_load = execute_point_prometheus_query(self.stack_obj,self.start_timestamp,query)
                for line in results_before_load:
                    table_name = line['metric']['table_name']
                    start_value = int(line['value'][1])
                    curr_result[table_name]["before"]=start_value#={"startTableSize":start_value}

                results_after_load = execute_point_prometheus_query(self.stack_obj,self.end_timestamp,query)
                for line in results_after_load:
                    table_name = line['metric']['table_name']
                    end_value = int(line['value'][1])
                    curr_result[table_name]["after"]=end_value

                df = pd.DataFrame(curr_result)
                df=df.T
                df=df.reset_index().rename(columns={'index': 'table_name'})
                try:
                    df["after-before"] = df["after"]-df["before"]
                    df=df.sort_values(by="after-before",ascending=False)
                    df.drop(columns=["after","before"],inplace=True)
                    df = df[df['after-before'] != 0.0]
                    print(df)
                    if df.empty:
                        print(f"empty dataframe found for  db {db} and stat {stat}")
                        continue
                    final_result[f"{db}_{stat}"] = {
                        "format":"table","collapse":True,
                        "schema":{
                            "merge_on_cols" : ["table_name"],
                            "compare_cols":["after-before"],
                            "display_exact_table":False
                        },
                        "data":df.to_dict(orient="records")
                    }
                except Exception as e:
                    print(f"error while finding delta for pgstats : for db {db} and stat {stat}  : {e}")
                    print(df)
                    continue

        if final_result == {}:return None
        return {"format":"nested_table","schema":{"page":"Postgres, Pgbouncer stats"},"data":final_result}

if __name__ == "__main__":
    from settings import stack_configuration
    import json
    variables = {
        "start_time_str_ist":"2024-06-26 00:25",
        "load_duration_in_hrs":14,
        "test_env_file_name":'s1_nodes.json'
    }
    stack_obj = stack_configuration(variables)
    pgtable = pg_stats_class(stack_obj=stack_obj)
    pg_stats = pgtable.process_output()
    print(json.dumps(pg_stats,indent=1))