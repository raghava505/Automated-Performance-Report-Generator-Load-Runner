import requests
import pandas as pd

class Active_conn:
    def __init__(self,prom_con_obj,start_timestamp,end_timestamp):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp
        self.prom_con_obj=prom_con_obj
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path
    
    def get_avg_active_conn(self):
        query="uptycs_pg_idle_active_connections_by_app{state=\"active\",db=\"configdb\",role=\"master\"}"
        final=[]
        PARAMS = {
            'query': query,
            'start': self.curr_ist_start_time,
            'end': self.curr_ist_end_time,
            'step':60
        }
        response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
        if response.status_code != 200:print("ERROR : Request failed")
        result = response.json()['data']['result']
        if len(result)==0:
            print(f"WARNING : No data found for : {query}, the query executed is : {query}")
            return None
        for app in result:
            application_name = app["metric"]["application_name"]
            values = [float(i[1]) for i in app['values']]
            avg = sum(values) / len(values)
            minimum = min(values)
            maximum = max(values)
            final.append({"application":application_name,"minimum":minimum , "maximum":maximum,"average":avg})
        df = pd.DataFrame(final)
        print("Printing details for active connections by app on master : ")
        print(df)
        return df.to_dict(orient="records")
    

# if __name__=='__main__':
#     print("Testing active connections by app...")
#     from settings import configuration
#     from datetime import datetime, timedelta
#     import pytz
#     format_data = "%Y-%m-%d %H:%M"
    
#     start_time_str = "2024-01-24 23:37"
#     hours=16

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
#     active_obj = Active_conn(configuration('longevity_nodes.json') , start_timestamp,end_timestamp)
#     result = active_obj.get_avg_active_conn()
#     print(result)