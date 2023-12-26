import requests
import copy
import json


class Charts:
    def __init__(self,prom_con_obj,start_timestamp,end_timestamp,add_extra_time_for_charts_at_end_in_min,fs):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp
        self.prom_con_obj=prom_con_obj
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path
        self.add_extra_time_for_charts_at_end_in_min=add_extra_time_for_charts_at_end_in_min
        self.add_extra_time_for_charts_at_start_in_min=10
        self.fs=fs

    def extract_charts_data(self,queries):
        final=dict()
        file_ids=[]
        ste = self.curr_ist_start_time - (self.add_extra_time_for_charts_at_start_in_min * (60))
        ete = self.curr_ist_end_time + (self.add_extra_time_for_charts_at_end_in_min * (60))

        for query in queries:
            try:
                PARAMS = {
                    'query': queries[query][0],
                    'start': ste,
                    'end': ete,
                    'step':60
                }
                legend_list = queries[query][1]
                try:unit = queries[query][2]
                except:unit=""
                response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
                print(f"processing {query} chart data (timestamp : {ste} to {ete}), Status code : {response.status_code}")
                if response.status_code != 200:print("ERROR : Request failed")
                else:
                    result = response.json()['data']['result']
                    for host in result:
                        file_id = self.fs.put(str(host["values"]).encode('utf-8'), filename=f'{query}.json')
                        host["values"] = file_id
                        file_ids.append(file_id)
                        try:
                            if len(legend_list)>0:
                                legend_text=str(host['metric'][legend_list[0]])
                            else:
                                print("Empty legend list found")
                                legend_text=""
                        except:
                            print(f"Warning : Key '{legend_list[0]}' not present in '{host['metric']}'. please check the provided legend attribute")
                            legend_text=""
                        for key in legend_list[1:]:
                            try:
                                legend_text += f"-{host['metric'][key]}"
                            except:
                                print(f"Warning : Key '{key}' not present in {host['metric']}. please check the provided legend attribute")
                        host["legend"]=legend_text
                        host["unit"]=unit
                    final[query] = result
            except Exception as e:
                print(f"Error occured while processing data for '{query}' , {str(e)}")
        return final,file_ids
            
    def capture_charts_and_save(self,all_chart_queries): 
        print("All chart queries to be executed are:")
        print(json.dumps(all_chart_queries, indent=4))

        all_gridfs_fileids = []
        final_dict={}
        for key,value in all_chart_queries.items():
            print(f"-----------Processing {key} queries-----------")
            final_dict[key],file_ids = self.extract_charts_data(value)
            all_gridfs_fileids.extend(file_ids)
        return final_dict,all_gridfs_fileids