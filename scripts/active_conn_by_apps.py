from helper import execute_prometheus_query
import pandas as pd
import numpy as np
class Active_conn:
    def __init__(self,stack_obj):
        self.stack_obj=stack_obj
    
    def get_avg_active_conn(self):
        base_query="uptycs_pg_idle_active_connections_by_app{{state=\"active\",db=\"{}\",role=\"master\"}}"
        dbs = ["configdb","insightsdb","rangerdb","metastoredb","statedb"]
        result_dict={}
        for db in dbs:
            query = base_query.format(db)
            result =execute_prometheus_query(self.stack_obj,query)
            final=[]
            for app in result:
                application_name = app["metric"]["application_name"]
                avg = round(app["values"]["average"],2)
                minimum = round(app["values"]["minimum"],2)
                maximum = round(app["values"]["maximum"],2)
                final.append({"application":application_name,"min":minimum , "max":maximum,"avg":avg})
            df = pd.DataFrame(final)
            # new_row={"application":"TOTAL","minimum":df["minimum"].sum() , "maximum":df["maximum"].sum(),"average":df["average"].sum()}
            # df = df._append(new_row, ignore_index=True)
            print(f"Printing details for active connections by app for {db} on master : ")
            print(df)
            if df.empty: 
                print("Empty dataframe found.. skipping to save this key to mongo")
                continue

            numeric_cols = df.select_dtypes(include=[np.number]).columns
            non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
            print("Numeric columns : " , numeric_cols)
            print("Non-Numeric columns : " , non_numeric_cols)

            fill_values = {}
            fill_values.update({col: 0 for col in numeric_cols})
            fill_values.update({col: "NaN" for col in non_numeric_cols})

            df = df.fillna(fill_values)
            result_dict[db] = {
                "schema":{
                    "merge_on_cols" : ["application"],
                    "compare_cols":["avg"]
                },
                "table":df.to_dict(orient="records")
            }
        return result_dict
    

if __name__=='__main__':
    print("Testing active connections by app...")
    from settings import stack_configuration
    
    variables = {
        "start_time_str_ist":"2024-01-26 13:25",
        "load_duration_in_hrs":4,
        "test_env_file_name":'s1_nodes.json'
    }
    stack_obj = stack_configuration(variables)
    
    active_obj = Active_conn(stack_obj)
    result = active_obj.get_avg_active_conn()
    print(result)