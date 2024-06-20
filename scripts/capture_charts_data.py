from helper import execute_prometheus_query

class Charts:
    def __init__(self,stack_obj,start_timestamp,end_timestamp,fs,hours):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp
        self.stack_obj=stack_obj
        self.add_extra_time_for_charts_at_end_in_min=2*hours
        self.add_extra_time_for_charts_at_start_in_min=2*hours
        self.fs=fs
        self.hours=hours

    def extract_charts_data(self,queries,step_factor):
        final=dict()
        file_ids=[]
        ste = self.curr_ist_start_time - (self.add_extra_time_for_charts_at_start_in_min * (60))
        ete = self.curr_ist_end_time + (self.add_extra_time_for_charts_at_end_in_min * (60))

        for query in queries:
            main_query = queries[query][0]
            result=execute_prometheus_query(self.stack_obj,ste,ete,main_query,self.hours,preprocess=False,step_factor=step_factor)
            legend_list = queries[query][1]
            try:unit = queries[query][2]
            except:unit=""
            print(f"processing {query} chart data (timestamp : {ste} to {ete})")
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
            
        return final,file_ids
            
    def capture_charts_and_save(self,all_chart_queries,step_factor): 
        all_gridfs_fileids = []
        final_dict={}
        for key,value in all_chart_queries.items():
            print(f"----------------------Processing {key} queries----------------------")
            final_dict[key],file_ids = self.extract_charts_data(value,step_factor)
            all_gridfs_fileids.extend(file_ids)
        return final_dict,all_gridfs_fileids