from pymongo import MongoClient
from bson import ObjectId
import pandas as pd


class resource_analysis:
    def __init__(self,prom_con_obj,dbname,collection,id1,id2):
        client = MongoClient(prom_con_obj.mongo_connection_string)
        db = client[dbname]  # Replace 'your_database_name' with your actual database name
        self.collection = db[collection]  # Replace 'your_collection_name' with your actual collection name
        self.id1=ObjectId(id1)
        self.id2=ObjectId(id2)

    def get_doc(self,id,filter):
        result=self.collection.find_one({"_id":id},filter)
        return result

    def get_nodetype_level_df(self,id,mem_or_cpu):
        filter = {f"resource_utilization_for_report.{mem_or_cpu}_usages.nodetype_level_usage.table":1,'_id':0}
        result= self.get_doc(id,filter)['resource_utilization_for_report'][f'{mem_or_cpu}_usages']['nodetype_level_usage']['table']
        df = pd.DataFrame(result)
        return df
    
    def get_nodetype_apps_cont_level_df(self,id,mem_or_cpu,app_or_cont):
        filter = {f"resource_utilization_for_report.{mem_or_cpu}_usages.nodetype_and_{app_or_cont}_level_usage_for_analysis":1,'_id':0}
        result= self.get_doc(id,filter)['resource_utilization_for_report'][f'{mem_or_cpu}_usages'][f'nodetype_and_{app_or_cont}_level_usage_for_analysis']
        dfs={}
        for d in result.keys():
            dfs[d]=pd.DataFrame(result[d]["table"])
        return dfs
        
    def compare_dfs(self,main,prev,merge_on):
        main.rename(columns={'avg': 'avg_main'}, inplace=True)
        prev.rename(columns={'avg': 'avg_prev'}, inplace=True)

        merged_df = pd.merge(prev,main, on=merge_on, how='outer')
        merged_df["absolute"] = merged_df["avg_main"]- merged_df["avg_prev"] 
        merged_df["relative"] = (merged_df["avg_main"]- merged_df["avg_prev"] )*100/merged_df["avg_prev"]
        merged_df=merged_df.sort_values(by='absolute', ascending=False)

        # print(merged_df)
        return merged_df
    
    def compare_nodetype_usages(self,mem_or_cpu):
        main=self.get_nodetype_level_df(self.id1,mem_or_cpu)
        prev=self.get_nodetype_level_df(self.id2,mem_or_cpu)
        df = self.compare_dfs(main,prev,"node_type")
        print(df)


    def compare_nodetype_app_cont_usages(self,mem_or_cpu,app_or_cont):
        main_dict=self.get_nodetype_apps_cont_level_df(self.id1,mem_or_cpu,app_or_cont)
        prev_dict=self.get_nodetype_apps_cont_level_df(self.id2,mem_or_cpu,app_or_cont)
        node_types = list(main_dict.keys())
        compared_dfs={}
        for nodetype in list(main_dict.keys()):
             compared_dfs[nodetype]=self.compare_dfs(main_dict[nodetype],prev_dict[nodetype],merge_on=["node_type",app_or_cont])
        for nodetype,df in compared_dfs.items():
            df.to_csv(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_{app_or_cont}_{nodetype}.csv", index=False) 


if __name__=='__main__':
    from settings import configuration
    id1="65cb3b41160cbf0949289ab6"
    id2="65c2351cee40e652dd19ce81"
    obj = resource_analysis(configuration() , "Osquery_LoadTests","Testing",id1,id2)
    obj.compare_nodetype_usages("memory")
    obj.compare_nodetype_usages("cpu")

    obj.compare_nodetype_app_cont_usages("memory","application")
    obj.compare_nodetype_app_cont_usages("memory","container")
    obj.compare_nodetype_app_cont_usages("cpu","application")
    obj.compare_nodetype_app_cont_usages("cpu","container")