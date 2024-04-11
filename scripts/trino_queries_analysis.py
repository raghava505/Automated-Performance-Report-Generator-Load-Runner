import pandas as pd
from io import StringIO
from helper import execute_trino_query

#configdb_command = "PGPASSWORD=pguptycs psql -h {} -U uptycs -p 5432 -d configdb -c \"select read_password from customer_database where database_name='upt_{}';\"".format(remote_host,self.stack_details['domain'])

class TRINO_ANALYSE:
    def __init__(self,start_utc_str,end_utc_str,prom_con_obj):
        self.prom_con_obj = prom_con_obj
        self.start_utc_str=start_utc_str
        self.end_utc_str=end_utc_str
        self.remote_username = prom_con_obj.abacus_username
        self.remote_password  = prom_con_obj.abacus_password
        self.dnode = prom_con_obj.execute_trino_queries_in

    def fetch_trino_results(self,commands):
        save_dict={}       
        for heading,value in commands.items():
            raw_command=value['query']
            columns=value['columns']
            schema = value["schema"]
            query = raw_command.replace("<start_utc_str>",self.start_utc_str).replace( "<end_utc_str>", self.end_utc_str)
            print(f"Command :\n {query}")
            output= execute_trino_query(self.dnode,query,self.prom_con_obj)
            # if not output or output.strip()=="":
            #     raise RuntimeError(f"ERROR : command output is empty. Check if trino @ {self.dnode} is in good state. Terminating program ...")
            stringio = StringIO(output)
            df = pd.read_csv(stringio, header=None, names=columns)
            df=df.fillna("NaN")
            # integer_columns = df.select_dtypes(include='int').columns
            # string_columns = df.select_dtypes(include='object').columns
            # new_row=dict([(int_col,df[int_col].sum()) for int_col in integer_columns])
            # new_row.update(dict([(str_col,"TOTAL") for str_col in string_columns]))
            # df = df._append(new_row, ignore_index=True)
            print(df)
            try:
                df["query_operation"] = df["query_operation"].astype(str)
            except:
                pass
            # df.to_csv("152_"+heading+".csv")
            save_dict[heading] = {
                "schema":schema,
                "table":df.to_dict(orient="records")
            }

        return save_dict
    
# if __name__=='__main__':
#     print("Testing trino queries analysis ...")
#     from settings import configuration
#     from datetime import datetime, timedelta
#     import pytz
#     from parent_load_details import parent
#     format_data = "%Y-%m-%d %H:%M"

#     start_time_str = "2024-04-03 21:39"
#     hours=10

#     start_time = datetime.strptime(start_time_str, format_data)
#     end_time = start_time + timedelta(hours=hours)
#     end_time_str = end_time.strftime(format_data)

#     ist_timezone = pytz.timezone('Asia/Kolkata')
#     utc_timezone = pytz.utc

#     start_ist_time = ist_timezone.localize(datetime.strptime(start_time_str, '%Y-%m-%d %H:%M'))
#     start_timestamp = int(start_ist_time.timestamp())
#     start_utc_time = start_ist_time.astimezone(utc_timezone)
#     start_utc_str = start_utc_time.strftime(format_data)

#     end_ist_time = ist_timezone.localize(datetime.strptime(end_time_str, '%Y-%m-%d %H:%M'))
#     end_timestamp = int(end_ist_time.timestamp())
#     end_utc_time = end_ist_time.astimezone(utc_timezone)
#     end_utc_str = end_utc_time.strftime(format_data)
#     calc = TRINO_ANALYSE(start_utc_str,end_utc_str,prom_con_obj=configuration('s1_nodes.json'))
#     trino_queries = calc.fetch_trino_results(parent.trino_details_commands)
#     import pandas as pd
#     from pymongo import MongoClient

#     # Create a sample DataFrame
#     client = MongoClient('mongodb://localhost:27017/')
#     db = client['Osquery_LoadTests']  # Replace 'your_database_name' with your actual database name
#     collection = db['Testing']  # Replace 'your_collection_name' with your actual collection name

#     collection.insert_one({"data":trino_queries})