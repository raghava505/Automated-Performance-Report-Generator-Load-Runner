import requests
import json
import pandas as pd

databases = ["configdb","statedb"]

pg_query = 'uptycs_pg_stats{db=~"%s"}'

class PG_STATS:
    def __init__(self,start_timestamp,end_timestamp,load_dur,prom_con_obj):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp
        self.prom_con_obj=prom_con_obj
        self.load_duration=load_dur
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path
        self.test_env_file_path=prom_con_obj.test_env_file_path
        with open(self.test_env_file_path, 'r') as file:
            self.nodes_data = json.load(file)

    def get_data(self,db):

        params = {
            'query': pg_query %(db),
            'start': self.curr_ist_start_time,
            'end': self.curr_ist_end_time,
            'step': self.load_duration * 3600              
        }
        response = requests.get(self.PROMETHEUS + self.API_PATH, params=params)
        print(f"-------processing PG STATS for {pg_query} (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time}), Status code : {response.status_code}")
        if response.status_code != 200:print("ERROR : Request failed")
        result = response.json()['data']['result']

        # with open("output_{}.json".format(db),'w') as json_out:
        #     json.dump(result,json_out,indent=4)

        return result
            
    def process_output(self):

        table_list = {}

        for db in databases:
        
            data_dict = self.get_data(db)
            
            # Open the JSON file and load data into a dictionary
            # with open("out.json", "r") as json_file:
            #     data_dict = json.load(json_file)

            # Create empty DataFrames
            df_table = pd.DataFrame(columns=['TableName', 'StartTableSize', 'EndTableSize', 'Delta'])
            df_index = pd.DataFrame(columns=['TableName', 'StartIndexSize', 'EndIndexSize', 'Delta'])
            df_tuples = pd.DataFrame(columns=['TableName', 'StartLiveTuples', 'EndLiveTuples', 'Delta'])

            # Iterate over the data_dict
            for i in range(len(data_dict)):
                for key in data_dict[i]:
                    if data_dict[i]['metric']['stat'] == 'table_size_bytes':
                        df_table.loc[len(df_table)] = [data_dict[i]['metric']['table_name'], data_dict[i]['values'][0][1], data_dict[i]['values'][1][1],int(data_dict[i]['values'][1][1])-int(data_dict[i]['values'][0][1])]
                    elif data_dict[i]['metric']['stat'] == 'index_size_bytes':
                        df_index.loc[len(df_index)] = [data_dict[i]['metric']['table_name'], data_dict[i]['values'][0][1], data_dict[i]['values'][1][1],int(data_dict[i]['values'][1][1])-int(data_dict[i]['values'][0][1])]
                    elif data_dict[i]['metric']['stat'] == 'live_tuples':
                        df_tuples.loc[len(df_tuples)] = [data_dict[i]['metric']['table_name'], data_dict[i]['values'][0][1], data_dict[i]['values'][1][1],int(data_dict[i]['values'][1][1])-int(data_dict[i]['values'][0][1])]

            # Print the resulting DataFrame
            df_table = df_table.astype({"StartTableSize":'int', "EndTableSize":'int',"Delta":'int'})  
            df_index = df_index.astype({"StartIndexSize":'int', "EndIndexSize":'int',"Delta":'int'})  
            df_tuples = df_tuples.astype({"StartLiveTuples":'int', "EndLiveTuples":'int',"Delta":'int'})  

            df_table[['StartTableSize','EndTableSize','Delta']] = df_table[['StartTableSize','EndTableSize','Delta']].div(1024)
            df_index[['StartIndexSize','EndIndexSize','Delta']] = df_index[['StartIndexSize','EndIndexSize','Delta']].div(1024)
            df_tuples[['StartLiveTuples','EndLiveTuples','Delta']] = df_tuples[['StartLiveTuples','EndLiveTuples','Delta']]

            df_table.sort_values('EndTableSize',ascending=False,inplace=True)
            df_index.sort_values('EndIndexSize',ascending=False,inplace=True)
            df_tuples.sort_values('EndLiveTuples',ascending=False,inplace=True)

            df_table.reset_index(drop=True,inplace=True)
            df_index.reset_index(drop=True,inplace=True)
            df_tuples.reset_index(drop=True,inplace=True)

            table_json = df_table.to_json()
            index_json = df_index.to_json()
            tuples_json = df_tuples.to_json()

            obj = {
                "{}_tablesize".format(db) : table_json,
                "{}_indexsize".format(db) : index_json,
                "{}_tuples".format(db) : tuples_json
            }
            
            table_list.update(obj)
        
        return table_list
    
