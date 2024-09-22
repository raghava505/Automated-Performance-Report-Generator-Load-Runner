from helper import execute_prometheus_query, clean_and_preprocess_df
import pandas as pd

dbs = ["configdb","insightsdb","rangerdb","metastoredb","statedb"]

all_pg_stats_queries  = {
    "Idle and Active Postgres Connections by applications":["uptycs_pg_idle_active_connections_by_app" , "application_name, role, state"],
    # "Idle and Active Postgres Connections by applications and host":["uptycs_pg_idle_active_connections_by_app" , "application_name, role, state, host_name"],
    "Postgres Connections by state" : ["uptycs_pg_connections_by_state" , "role, state"],
    # "Postgres Connections by state and host" : ["uptycs_pg_connections_by_state" , "role, state, host_name"],

}

postgres_stats_base_query  = 'sum({}{{db="{}"}}) by ({})'

class postgres_monitoring_stats_class:
    def __init__(self,stack_obj):
        self.stack_obj=stack_obj
    
    def get_postgres_monitoring_stats(self):
        final_return_dict = {}
        for section_heading, query_params in all_pg_stats_queries.items():
            result_dict={}
            query_title = query_params[0]
            query_groupby = query_params[1]
            for db in dbs:
                query = postgres_stats_base_query .format(query_title,db, query_groupby)
                result =execute_prometheus_query(self.stack_obj,query)
                final=[]
                merge_on_cols=None
                for app in result:
                    row_to_append = {}
                    merge_on_cols = []
                    for col_name in query_groupby.split(','):
                        col_name = col_name.strip()
                        merge_on_cols.append(col_name)
                        row_to_append[col_name] = app["metric"][col_name]

                    row_to_append["avg"] = round(app["values"]["average"],2)
                    row_to_append["min"] = round(app["values"]["minimum"],2)
                    row_to_append["max"] = round(app["values"]["maximum"],2)
                    final.append(row_to_append)
                df = pd.DataFrame(final)
                self.stack_obj.log.info(f"Printing details for {section_heading} for {db} : ")
                self.stack_obj.log.info(f"\n {df}")
                if df.empty: 
                    self.stack_obj.log.info("Empty dataframe found.. skipping to save this key to mongo")
                    continue

                df = clean_and_preprocess_df(df)

                result_dict[db] = {
                    "format":"table","collapse":True,
                    "schema":{
                        "merge_on_cols" : merge_on_cols if merge_on_cols else [],
                        "compare_cols":["avg"]
                    },
                    "data":df.to_dict(orient="records")
                }
            if result_dict != {}:
                final_return_dict[section_heading] = {"format":"nested_table","schema":{"page":"Postgres stats"},"data":result_dict}
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
    
    active_obj = postgres_monitoring_stats_class(stack_obj)
    result = active_obj.get_postgres_monitoring_stats()
    print(result)