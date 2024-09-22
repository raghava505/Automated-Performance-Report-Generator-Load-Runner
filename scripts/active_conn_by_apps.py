from helper import execute_prometheus_query, clean_and_preprocess_df
import pandas as pd

class num_active_conn_class:
    def __init__(self,stack_obj):
        self.stack_obj=stack_obj
    
    def get_avg_active_conn(self):
        connections_to_dbs='sum(uptycs_pg_idle_active_connections_by_app{{state="active",db="{}",role="master"}}) by (application_name)'
        dbs = ["configdb","insightsdb","rangerdb","metastoredb","statedb"]
        result_dict={}
        for db in dbs:
            query = connections_to_dbs.format(db)
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
            self.stack_obj.log.info(f"Printing details for active connections by app for {db} on master : ")
            self.stack_obj.log.info(f"\n {df}")
            if df.empty: 
                self.stack_obj.log.info("Empty dataframe found.. skipping to save this key to mongo")
                continue

            df = clean_and_preprocess_df(df)

            result_dict[db] = {
                "format":"table","collapse":True,
                "schema":{
                    "merge_on_cols" : ["application"],
                    "compare_cols":["avg"]
                },
                "data":df.to_dict(orient="records")
            }
        if result_dict == {}:return None
        return {"format":"nested_table","schema":{"page":"Postgres stats"},"data":result_dict}
    

if __name__=='__main__':
    print("Testing active connections by app...")
    from settings import stack_configuration
    
    variables = {
        "start_time_str_ist":"2024-09-21 13:25",
        "load_duration_in_hrs":4,
        "test_env_file_name":'s1_nodes.json'
    }
    stack_obj = stack_configuration(variables)
    
    active_obj = num_active_conn_class(stack_obj)
    result = active_obj.get_avg_active_conn()
    print(result)