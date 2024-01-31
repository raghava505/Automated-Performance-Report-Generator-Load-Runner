import requests
import pandas as pd

databases = ["configdb","statedb"]



class PG_STATS:
    def __init__(self,start_timestamp,end_timestamp,load_dur,prom_con_obj):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp
        self.prom_con_obj=prom_con_obj
        self.load_duration=load_dur
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path
        self.test_env_file_path=prom_con_obj.test_env_file_path
        
    def get_data(self,db):
        query = f'uptycs_pg_stats{{db=~"{db}"}}'
        params = {
            'query': query,
            'start': self.curr_ist_start_time,
            'end': self.curr_ist_end_time,
            'step': self.load_duration * 3600              
        }
        response = requests.get(self.PROMETHEUS + self.API_PATH, params=params)
        print(f"-------processing PG STATS for {query} (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time}), Status code : {response.status_code}")
        if response.status_code != 200:print("ERROR : Request failed")
        result = response.json()['data']['result']

        return result
            
    def process_output(self):
        table_dict = {}
        for db in databases:
            data_dict = self.get_data(db)

            # Create empty DataFrames
            df_table = pd.DataFrame(columns=['TableName', 'StartTableSize', 'EndTableSize', 'Delta'])
            df_index = pd.DataFrame(columns=['TableName', 'StartIndexSize', 'EndIndexSize', 'Delta'])
            df_tuples = pd.DataFrame(columns=['TableName', 'StartLiveTuples', 'EndLiveTuples', 'Delta'])
            
            for dict in data_dict:
                if dict['metric']['stat'] in ['table_size_bytes','index_size_bytes','live_tuples']:
                    table_name = dict['metric']['table_name']
                    start_value=None
                    end_value=None
                    diff=None
                    if len(dict['values'])==1:
                        if dict['values'][0][0] == self.curr_ist_start_time:
                            start_value=int(dict['values'][0][1])
                        else:
                            end_value=int(dict['values'][0][1])
                    elif len(dict['values'])==2:
                        start_value=int(dict['values'][0][1])
                        end_value=int(dict['values'][1][1])
                        diff = end_value-start_value
                    if dict['metric']['stat'] == 'table_size_bytes':
                        df_table.loc[len(df_table)] = [table_name,start_value,end_value,diff]
                    elif dict['metric']['stat'] == 'index_size_bytes':
                        df_index.loc[len(df_index)] = [table_name,start_value,end_value,diff]
                    elif dict['metric']['stat'] == 'live_tuples':
                        df_tuples.loc[len(df_tuples)] =[table_name,start_value,end_value,diff] 

            df_table[['StartTableSize','EndTableSize','Delta']] = df_table[['StartTableSize','EndTableSize','Delta']].div(1024)
            df_index[['StartIndexSize','EndIndexSize','Delta']] = df_index[['StartIndexSize','EndIndexSize','Delta']].div(1024)

            df_table.sort_values('Delta',ascending=False,inplace=True)
            df_index.sort_values('Delta',ascending=False,inplace=True)
            df_tuples.sort_values('Delta',ascending=False,inplace=True)
            
            table_json = df_table.to_json()
            index_json = df_index.to_json()
            tuples_json = df_tuples.to_json()

            obj = {
                "{}_tablesize".format(db) : table_json,
                "{}_indexsize".format(db) : index_json,
                "{}_tuples".format(db) : tuples_json
            }
            
            table_dict.update(obj)
        
        return table_dict

# from settings import configuration
# cls  = PG_STATS(1702926000,1702947600,6,configuration("longevity_nodes.json"))
# print("FINAL O/P : " ,cls.process_output())