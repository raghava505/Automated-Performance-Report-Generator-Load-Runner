from helper import execute_prometheus_query, clean_and_preprocess_df
import pandas as pd


connections_to_pgbouncer_base_query = 'sum({}{{db="{}"}}) by (pod_name, db_user, host_name, pgb_role)'
dbs = ["configdb","pgbouncer","insightsdb","rangerdb","metastoredb","statedb"]
all_pgb_connection_queries = {
    "Pgbouncer active client connections":"uptycs_pgb_cl_active",
    "Pgbouncer waiting client connections":"uptycs_pgb_cl_waiting",
    "Pgbouncer active server connections":"uptycs_pgb_sv_active",
    "Pgbouncer idle server connections":"uptycs_pgb_sv_idle",
    "Pgbouncer used server connections":"uptycs_pgb_sv_used",
}
class pgbouncer_conn_class:
    def __init__(self,stack_obj):
        self.stack_obj=stack_obj
    
    def get_pgbouncer_connections(self):
        final_return_dict = {}
        for section_heading, query_title in all_pgb_connection_queries.items():
            result_dict={}
            for db in dbs:
                
                query = connections_to_pgbouncer_base_query.format(query_title,db)
                result =execute_prometheus_query(self.stack_obj,query)
                final=[]
                for app in result:
                    application_name = app["metric"]["pod_name"]
                    db_user = app["metric"]["db_user"]
                    host_name = app["metric"]["host_name"]
                    pgb_role = app["metric"]["pgb_role"]
                    avg = round(app["values"]["average"],2)
                    minimum = round(app["values"]["minimum"],2)
                    maximum = round(app["values"]["maximum"],2)
                    final.append({"pod":application_name,"db_user":db_user,"host_name":host_name,"pgb_role":pgb_role,"min":minimum , "max":maximum,"avg":avg})
                df = pd.DataFrame(final)
                # new_row={"application":"TOTAL","minimum":df["minimum"].sum() , "maximum":df["maximum"].sum(),"average":df["average"].sum()}
                # df = df._append(new_row, ignore_index=True)
                self.stack_obj.log.info(f"Printing {section_heading} details for {db} : ")
                self.stack_obj.log.info(f"\n {df}")
                if df.empty: 
                    self.stack_obj.log.info("Empty dataframe found.. skipping to save this key to mongo")
                    continue

                df = clean_and_preprocess_df(df)

                result_dict[db] = {
                    "format":"table","collapse":True,
                    "schema":{
                        "merge_on_cols" : ["host_name" , "pgb_role"],
                        "compare_cols":["avg"]
                    },
                    "data":df.to_dict(orient="records")
                }

            if result_dict != {}:
                final_return_dict[section_heading] = {"format":"nested_table","schema":{"page":"Postgres, Pgbouncer stats"},"data":result_dict}
            # return {"format":"nested_table","schema":{},"data":result_dict}
        if final_return_dict!={}:
            return final_return_dict
        return None
    

if __name__=='__main__':
    print("Testing active connections by app...")
    from settings import stack_configuration
    
    variables = {
        "start_time_str_ist":"2024-09-21 13:25",
        "load_duration_in_hrs":4,
        "test_env_file_name":'s1_nodes.json'
    }
    stack_obj = stack_configuration(variables)
    
    active_obj = pgbouncer_conn_class(stack_obj)
    result = active_obj.get_pgbouncer_connections()
    print(result)