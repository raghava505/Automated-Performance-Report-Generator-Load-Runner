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
        # self.load_duration=stack_obj.hours
        # self.PROMETHEUS = stack_obj.prometheus_path
        # self.API_PATH = PROM_API_PATH
        
    # def get_data(self,db):
    #     query = f'uptycs_pg_stats{{db=~"{db}"}}'
    #     params = {
    #         'query': query,
    #         'start': self.curr_ist_start_time,
    #         'end': self.curr_ist_end_time,
    #         'step': self.load_duration * 3600              
    #     }
    #     response = requests.get(self.PROMETHEUS + self.API_PATH, params=params)
    #     self.stack_obj.log.info(f"-------processing PG STATS for {query} (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time}), Status code : {response.status_code}")
    #     if response.status_code != 200:self.stack_obj.log.error(f"Request failed status code {response.status_code}")
    #     result = response.json()['data']['result']

    #     return result
            
    def process_output(self):
        final_result = {}
        for db in databases:
            for stat in stats:
                # final_result[f"{db}_{stat}"] = {}
                curr_result=defaultdict(lambda:{})
                query = f'uptycs_pg_stats{{db=~"{db}", stat=~"{stat}"}}'

                results_before_load = execute_point_prometheus_query(stack_obj,self.start_timestamp,query)
                for line in results_before_load:
                    table_name = line['metric']['table_name']
                    start_value = int(line['value'][1])
                    curr_result[table_name]["before"]=start_value#={"startTableSize":start_value}

                results_after_load = execute_point_prometheus_query(stack_obj,self.end_timestamp,query)
                for line in results_after_load:
                    table_name = line['metric']['table_name']
                    end_value = int(line['value'][1])
                    curr_result[table_name]["after"]=end_value

                df = pd.DataFrame(curr_result)
                df=df.T
                df=df.reset_index().rename(columns={'index': 'table_name'})
                # print(df)
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
                        "schema":{
                            "merge_on_cols" : ["table_name"],
                            "compare_cols":["after-before"]
                        },
                        "table":df.to_dict(orient="records")
                    }
                except Exception as e:
                    print(f"error while finding delta for pgstats : for db {db} and stat {stat}  : {e}")
                    print(df)
                    continue
                # return
            # data_dict = self.get_data(db)

            # # Create empty DataFrames
            # df_table = pd.DataFrame(columns=['TableName', 'StartTableSize', 'EndTableSize', 'Delta'])
            # df_index = pd.DataFrame(columns=['TableName', 'StartIndexSize', 'EndIndexSize', 'Delta'])
            # df_tuples = pd.DataFrame(columns=['TableName', 'StartLiveTuples', 'EndLiveTuples', 'Delta'])
            
            # for dict in data_dict:
            #     if dict['metric']['stat'] in ['table_size_bytes','index_size_bytes','live_tuples']:
            #         table_name = dict['metric']['table_name']
            #         start_value=None
            #         end_value=None
            #         diff=None
            #         if len(dict['values'])==1:
            #             if dict['values'][0][0] == self.curr_ist_start_time:
            #                 start_value=int(dict['values'][0][1])
            #             else:
            #                 end_value=int(dict['values'][0][1])
            #         elif len(dict['values'])==2:
            #             start_value=int(dict['values'][0][1])
            #             end_value=int(dict['values'][1][1])
            #             diff = end_value-start_value
            #         if dict['metric']['stat'] == 'table_size_bytes':
            #             df_table.loc[len(df_table)] = [table_name,start_value,end_value,diff]
            #         elif dict['metric']['stat'] == 'index_size_bytes':
            #             df_index.loc[len(df_index)] = [table_name,start_value,end_value,diff]
            #         elif dict['metric']['stat'] == 'live_tuples':
            #             df_tuples.loc[len(df_tuples)] =[table_name,start_value,end_value,diff] 

            # df_table[['StartTableSize','EndTableSize','Delta']] = df_table[['StartTableSize','EndTableSize','Delta']].div(1024)
            # df_index[['StartIndexSize','EndIndexSize','Delta']] = df_index[['StartIndexSize','EndIndexSize','Delta']].div(1024)

            # df_table.sort_values('Delta',ascending=False,inplace=True)
            # df_index.sort_values('Delta',ascending=False,inplace=True)
            # df_tuples.sort_values('Delta',ascending=False,inplace=True)
            
            # table_json = df_table.to_json()
            # index_json = df_index.to_json()
            # tuples_json = df_tuples.to_json()

            # obj = {
            #     "{}_tablesize".format(db) : table_json,
            #     "{}_indexsize".format(db) : index_json,
            #     "{}_tuples".format(db) : tuples_json
            # }
            
            # final_result.update(obj)
        
        return final_result

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
    # print(pg_stats)