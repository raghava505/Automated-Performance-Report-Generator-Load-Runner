from pymongo import MongoClient
from bson import ObjectId
import pandas as pd
from create_piechart_for_analysis import *

class resource_analysis:
    def __init__(self,mongo_connection_string,dbname,collection,id1,id2):
        client = MongoClient(mongo_connection_string)
        db = client[dbname]  # Replace 'your_database_name' with your actual database name
        self.collection = db[collection]  # Replace 'your_collection_name' with your actual collection name
        self.id1=ObjectId(id1)
        self.id2=ObjectId(id2)

    def get_doc(self,id,filter):
        result=self.collection.find_one({"_id":id},filter)
        return result

    def get_nodetype_level_df(self,id,mem_or_cpu):
        filter = {f"resource_utilization_for_report":1,'_id':0}
        result= self.get_doc(id,filter)['resource_utilization_for_report'][f'{mem_or_cpu}_usages']['nodetype_level_usages']['table']
        df = pd.DataFrame(result)
        return df
    
    def get_nodetype_apps_cont_level_df(self,id,mem_or_cpu):
        filter = {f"resource_utilization_for_report":1,'_id':0}
        result= self.get_doc(id,filter)['resource_utilization_for_report'][f'{mem_or_cpu}_usages_analysis']#[f'nodetype_and_{app_or_cont}_level_{mem_or_cpu}_usages']
        return result
    
    
    def compare_nodetype_usages(self,mem_or_cpu):
        main=self.get_nodetype_level_df(self.id1,mem_or_cpu)
        prev=self.get_nodetype_level_df(self.id2,mem_or_cpu)
        df = compare_dfs(main,prev,"node_type")
        print(df)


    def compare_nodetype_app_cont_usages(self,mem_or_cpu):
        main_dict=self.get_nodetype_apps_cont_level_df(self.id1,mem_or_cpu)
        prev_dict=self.get_nodetype_apps_cont_level_df(self.id2,mem_or_cpu)
        call_create_piechart(mem_or_cpu,main_dict,prev_dict)
            

if __name__=='__main__':
    from settings import configuration
    main="65d8c893ecedea2c4d40bf97"
    prev="65d8c8da312d910618b0d12c"
    obj = resource_analysis(configuration().mongo_connection_string , "Osquery_LoadTests","Testing",main,prev)
    obj.compare_nodetype_usages("memory")
    obj.compare_nodetype_usages("cpu")

    obj.compare_nodetype_app_cont_usages("memory")
    obj.compare_nodetype_app_cont_usages("cpu")
