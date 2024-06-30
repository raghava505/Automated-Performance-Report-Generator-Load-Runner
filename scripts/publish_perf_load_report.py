import pandas as pd
from confluence_api import publish_to_confluence
from pymongo import MongoClient
from config_vars import MONGO_CONNECTION_STRING
import numpy as np
import os
from create_piechart_for_analysis import analysis_main
from config_vars import BASE_ANALYSIS_PIECHARTS_PATH
from collections import defaultdict

class perf_load_report_publish:
    def __init__(self,dbname,coll_name,sprint_runs_list,parent_page_title, report_title, email_address, api_key, space, url):
        self.dbname = dbname
        self.coll_name=coll_name
        client = MongoClient(MONGO_CONNECTION_STRING)
        self.database = client[dbname] 
        self.collection = self.database[coll_name]
        self.sprint_runs_list=sprint_runs_list
        self.main_sprint,self.main_run = sprint_runs_list[0][0],sprint_runs_list[0][1]
        self.sprint_runs_list.pop(0)
        self.main_result=self.collection.find_one({"load_details.data.sprint":self.main_sprint , "load_details.data.run":self.main_run})
        self.all_keys = list(self.main_result.keys())
        self.all_keys.remove('_id')
        self.main_build = self.main_result["load_details"]["data"]["build"]
        self.id = str(self.main_result["_id"])
        print("ID : ",self.id)
        print(self.all_keys)
        self.confluence_page_mappings={}
        
        self.parent_page_title=parent_page_title
        self.report_title=report_title
        self.email_address=email_address
        self.api_key=api_key
        self.space=space
        self.url = url


    def get_key_result(self,sprint,run,key_name):
        filter = {f"{key_name}":1,'_id':0}
        result=self.collection.find_one({"load_details.data.sprint":sprint , "load_details.data.run":run},filter)
        return result
    
    def create_page(self,parent_page_title, report_title):
        obj = publish_to_confluence(parent_page_title, report_title, self.email_address, self.api_key, self.space, self.url)
        flag, err = obj.create_page()
        if flag == False:
            print(f"error while create confluence page : {err}")
            return None
        else:
            print(f"Created new confluence page : {report_title}")
            return obj
        

    def merge_dfs(self,merge_on_cols,key_name,format,parent_key_name):
        print(f"Processing MERGE OF {parent_key_name} : {key_name}")
        all_dfs = []
        builds=[]
        for sprint,run in self.sprint_runs_list:
            print(f"finding data for {key_name} in sprint: {sprint}, run: {run}")
            build = self.get_key_result(sprint,run,f"load_details.data.build")["load_details"]["data"]["build"]
            try:
                if parent_key_name:
                    result = self.get_key_result(sprint,run,f"{parent_key_name}.data.{key_name}")
                    if not result:continue
                    result = result[parent_key_name]["data"][key_name]["data"]
                    # if result["format"] != format:continue
                else:
                    result = self.get_key_result(sprint,run,f"{key_name}")
                    if not result:continue
                    # if result["format"] != format:continue
                    result = result[key_name]["data"]
            except:
                result={}
            print(f"found data for {key_name} in build: {build}, run: {run}")
            temp_df = pd.DataFrame(result)
            if temp_df.empty : continue
            all_dfs.append((temp_df,f"_{build}_run{run}"))
            builds.append(f"{build}_run{run}")
        
        if parent_key_name:
            merged_df=pd.DataFrame(self.main_result[parent_key_name]["data"][key_name]["data"])
        else:
            merged_df=pd.DataFrame(self.main_result[key_name]["data"])

        for df, suffix in all_dfs:
            merged_df = pd.merge(merged_df, df, on=merge_on_cols, how='outer', suffixes=('', suffix))
        # print(merged_df)
        return merged_df,builds
    
    def process_abs_rel_cols(self,val):
        if val > 0: return f"{val} ⬆️"
        elif val < 0: return f"{abs(val)} ⬇️"
        elif val == 0: return 0
        else :
            print(f"WARNING : Unexpected value found : {val}")
            return val
        
    def compare_dfs(self,compare_col,merged_df,builds,merge_on_cols):
        print(f"comapring col {compare_col}")
        # print("recieved df : ")
        # print(merged_df)
        cols = merged_df.columns
        if compare_col not in cols:return None
        main_col_name = f"{compare_col}_{self.main_build}_run{self.main_run}"
        merged_df.rename(columns={compare_col: main_col_name}, inplace=True)
        cols_order = [f"{compare_col}_{build}" for build in reversed(builds)] 
        if len(cols_order)==0:return None
        cols_order = merge_on_cols+cols_order+[main_col_name]
        final_df = merged_df[cols_order]
        
        print(f"cols order {cols_order} ")
        print(final_df)

        final_df["Absolute"] = round(final_df[cols_order[-1]]-final_df[cols_order[-2]],2)
        final_df["Relative %"] = np.where(final_df[cols_order[-2]] != 0,
                                          round((final_df[cols_order[-1]]-final_df[cols_order[-2]])*100/final_df[cols_order[-2]],2),
                                          np.nan)
        print("final df")
        print(final_df)

        final_df["Absolute"] = final_df["Absolute"].apply(self.process_abs_rel_cols)
        final_df["Relative %"] = final_df["Relative %"].apply(self.process_abs_rel_cols)
        print("final df")
        print(final_df)
        return final_df
    


    def captilise_heading(self,heading):
        heading = str(heading).replace("_"," ")
        heading=heading.capitalize()
        return heading


    def extract_all_variables(self):
        self.create_page(self.parent_page_title, self.report_title)
        for key_name in self.all_keys:
            # if "usage" not in key_name:continue
            print(f"--------- processing {key_name}")
            key_format = self.main_result[key_name]["format"]
            schema = self.main_result[key_name]["schema"]
            data = self.main_result[key_name]["data"]
            try:collapse = self.main_result[key_name]["collapse"]
            except Exception as e:
                print(f"error finding cllapse var : {e}")
                collapse=True
            print(f"collapse is set to : {collapse}")


            if "page" in schema : page = schema["page"]
            else : page = "Overview"

            if page in self.confluence_page_mappings:
                curr_page_obj = self.confluence_page_mappings[page]
            else:
                curr_page_obj = self.create_page(self.report_title, f"{page}-{report_title}")
                self.confluence_page_mappings[page]=curr_page_obj

            if key_format == "table":
                merge_on_cols = schema["merge_on_cols"]
                compare_cols = schema["compare_cols"]
                
                # try:display_exact_table = schema["display_exact_table"]
                # except:display_exact_table=True

                main_df = pd.DataFrame(data)
                print("main df")
                print(main_df)
                if main_df.empty : continue
                curr_page_obj.add_table_from_dataframe(f"<h2>{self.captilise_heading(key_name)}</h2>", main_df, collapse=collapse)
                print("lengths")
                print(len(self.sprint_runs_list),len(merge_on_cols) ,len(compare_cols))
                if len(self.sprint_runs_list) > 0 and len(merge_on_cols) > 0 and len(compare_cols) > 0:
                    merged_df, builds = self.merge_dfs(merge_on_cols,key_name,key_format,parent_key_name = None)
                    for compare_col in compare_cols:
                        print(f"compare col is : {compare_col}")
                        returned_df = self.compare_dfs(compare_col,merged_df,builds,merge_on_cols)
                        print("--------returned df is : ")
                        print(returned_df)
                        main_df = returned_df.copy()
                        if returned_df is not None and not returned_df.empty :curr_page_obj.add_table_from_dataframe(f"<h3>comparison on {self.captilise_heading(compare_col)}</h3>", returned_df, collapse=collapse, red_green_column_list=["Absolute","Relative %"])
                        print("main df updated(copied) with returned df")

                if "Overall Memory" in key_name:
                    print("Now main df is : ")
                    print(main_df)
                    self.overall_memory_df = main_df
                    print("OEVRALL MEM UPDATED")
                    print(self.overall_memory_df)
                if "Overall CPU" in key_name:
                    print("Now main df is : ")
                    print(main_df)
                    self.overall_cpu_df = main_df
                    print("OEVRALL CPU UPDATED")
                    print(self.overall_cpu_df)


           
            elif key_format == "nested_table":
                curr_page_obj.add_text(f"<h2>{self.captilise_heading(key_name)}</h2>")
                for nested_key_name in data.keys():
                    print(f"processing nested key {nested_key_name}")
                    key_format = self.main_result[key_name]["data"][nested_key_name]["format"]
                    schema = self.main_result[key_name]["data"][nested_key_name]["schema"]
                    data = self.main_result[key_name]["data"][nested_key_name]["data"]
                    if key_format != "table":print(f"WARNING check the nested key format for this key. current key format is : {key_format}")
                    if key_format == "table":
                        merge_on_cols = schema["merge_on_cols"]
                        compare_cols = schema["compare_cols"]
                        # try:display_exact_table = schema["display_exact_table"]
                        # except:display_exact_table=True

                        main_df = pd.DataFrame(data)
                        if main_df.empty : continue

                        curr_page_obj.add_table_from_dataframe(f"<h3>{self.captilise_heading(nested_key_name)}</h3>", main_df, collapse=collapse)
                        if len(self.sprint_runs_list) > 0 and len(merge_on_cols) > 0 and len(compare_cols) > 0:
                            merged_df, builds = self.merge_dfs(merge_on_cols,nested_key_name,key_format,parent_key_name = key_name)
                            for compare_col in compare_cols:
                                
                                returned_df = self.compare_dfs(compare_col,merged_df,builds,merge_on_cols)
                                if returned_df is not None and not returned_df.empty :curr_page_obj.add_table_from_dataframe(f"<h4>comparison on {self.captilise_heading(compare_col)}</h4>", returned_df, collapse=collapse,red_green_column_list=["Absolute","Relative %"])

                        
            elif key_format == "mapping":
                curr_page_obj.add_text(f"<h2>{self.captilise_heading(key_name)}</h2>")

                for key,value in data.items():
                    if type(value) != dict:
                        if type(value) == str and "http" in value:
                            value = f'<a href="{value}">{value}</a>'
                        curr_page_obj.add_text(f"<p>{self.captilise_heading(key)} : {value}</p>\n")
                    else:
                        curr_page_obj.add_text(f"<h3>{str(key)}</h3>")
                        for nested_key,nested_value in value.items():
                            curr_page_obj.add_text(f"<p>{self.captilise_heading(nested_key)} : {nested_value}</p>\n")

            elif key_format == "list":
                pass
            elif key_format == "analysis":
                if len(self.sprint_runs_list) == 0:
                    print("warning sprints not provided to compare and analyse resource usages")
                    continue
                prev_sprint,prev_run = self.sprint_runs_list[0][0],self.sprint_runs_list[0][1]
                prev_data=self.get_key_result(prev_sprint,prev_run,key_name)
                if not prev_data:
                    print(f"Found no previous data for sprint {prev_sprint} and run {prev_run}")
                    continue
                prev_data=prev_data[key_name]["data"]
                temp_images,memory_combined_df,cpu_combined_df=analysis_main(data["memory_usages_analysis"],prev_data["memory_usages_analysis"],data["cpu_usage_analysis"],prev_data["cpu_usage_analysis"])
                print("INSIDE ANALYSIS : ")
                print(temp_images)
                print(memory_combined_df)
                print(cpu_combined_df)

                os.makedirs(BASE_ANALYSIS_PIECHARTS_PATH,exist_ok=True)

                final_images=defaultdict(lambda : [])

                for piechart_name in temp_images:
                    file_path = f"{BASE_ANALYSIS_PIECHARTS_PATH}/{piechart_name}.png"
                    temp_images[piechart_name].save(file_path)
                    final_images[piechart_name].append(file_path)
                print(final_images)
                memory_combined_df = pd.merge(self.overall_memory_df,memory_combined_df,on=["node_type"], how='outer')
                cpu_combined_df = pd.merge(self.overall_cpu_df,cpu_combined_df,on=["node_type"], how='outer')

                curr_page_obj.add_text(f"<h2>Overall Resource Utilizations</h2>")

                curr_page_obj.add_table_from_dataframe(f'<h2>{self.captilise_heading("memory_usages_analysis")}</h2>', memory_combined_df, collapse=False,red_green_column_list=["Absolute","Relative %"])
                curr_page_obj.add_table_from_dataframe(f'<h2>{self.captilise_heading("cpu_usage_analysis")}</h2>', cpu_combined_df, collapse=False,red_green_column_list=["Absolute","Relative %"])
                curr_page_obj.attach_saved_charts(final_images,main_heading="Complete Analysis piecharts for resource utilizations")

            elif key_format == "charts":
                base_graphs_path=os.path.join(schema["base_graphs_path"],self.dbname,self.coll_name,self.id)
                charts_paths_dict={}
                for main_heading,inside_charts in data.items():
                    charts_paths_dict[main_heading] = [f'{os.path.join(base_graphs_path,main_heading,f"{file_name}.png")}' for file_name in list(inside_charts.keys())]
                # print(charts_paths_dict)
                curr_page_obj.attach_saved_charts(charts_paths_dict)

            curr_page_obj.update_and_publish()


if __name__=='__main__':
    url='https://uptycsjira.atlassian.net'
    email_address = "masabathularao@uptycs.com"
    api_key = "ATATT3xFfGF02rG4e5JQzZZ_mVdAkwKKGnjRLYIupWToEGxZm8X-r5dUrAzSAdzGi5FPXMIn_IacnJjOwORsOQV7noObZmkdHqsaHHIzw4pTVyid2Jh3rVmLjM8iw5_hmaK7rFWSMz1JBpQq44vGV1FJs7P-89zijob43kBuxHzfFJJxl5IlM0w=7CE826E3"
    space = '~71202040c8bf45840d41c598c0efad54382c7b'
    parent_page_title = 'PUBLISH TEST'
    report_title = "TEST 26"

    obj = perf_load_report_publish("Osquery_LoadTests","MultiCustomer",[(100,4),(100,3),(100,2)],parent_page_title, report_title, email_address, api_key, space, url)
    # result = obj.get_key_result(100,1,"Trino Queries Analysis.data.Total time taken by each dag")
    # print(result)
    obj.extract_all_variables()
    
