import pandas as pd
from confluence_api import publish_to_confluence
from pymongo import MongoClient
import numpy as np
import os
from create_piechart_for_analysis import analysis_main
from config_vars import MONGO_CONNECTION_STRING
import uuid
import json
import io
import base64
import pandas as pd
import re
class custom_string(str):
    def __init__(self, value=""):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __add__(self, other):
        if other is None:
            return self
        elif isinstance(other, (str, custom_string)):
            return custom_string(self.value + str(other))
        else:
            return NotImplemented

    def __repr__(self):
        return f"custom_string({self.value!r})"
class ViewReportClass:
    def __getattr__(self, name):
        # Returns a callable object for any attribute
        def method(*args, **kwargs):
            # You can define custom behavior here if needed
            return f"Method {name} called with args: {args} and kwargs: {kwargs}"
        
        return method

    def __call__(self, *args, **kwargs):
        # This makes the instance itself callable
        return f"Instance called with args: {args} and kwargs: {kwargs}"
    def add_text(self,text):
        return text
    
    def add_table_from_dataframe(self, heading_text, df, isEditable=False,key_name=None,dbname=None, collname=None, sprint=None , run=None,is_comparison_table=False, *args, **kwargs):
        load_info_header = f"{dbname}___{collname}___{sprint}___{run}___{key_name}"
        # Generate custom header with sortable columns
        custom_header = "<thead><tr>"
        columns_list = list(df.columns)
        for column in df.columns:
            custom_header += f'<th class="sortable" data-column="{column}" data-order="desc">{column}</th>'
        if isEditable:
            custom_header += '<th></th>'
        custom_header += "</tr></thead>"

        # Define functions to apply color styles
        def colorize_cell(content):
            parts = content.split(';')
            content_with_line_breaks = '<br>'.join(parts)
            if "⬇️" in content:
                return f'<span style="color: green;">{content_with_line_breaks}</span>'
            elif "⬆️" in content:
                return f'<span style="color: red;">{content_with_line_breaks}</span>'
            return content_with_line_breaks
        
        def generate_cell_html(value, row_idx, col_idx):
            return f'<td><textarea  style="font-size:12px;" class="form-control" name="{load_info_header}___{columns_list[col_idx]}" style="width:100%; height:100%; text-align:left;">{value}</textarea></td>'
        
        if not isEditable:
            # Convert the DataFrame to HTML without headers
            table_html = df.to_html(classes="table table-bordered table-hover table-sm text-center custom-table", 
                                    index=False, header=False)

            # Apply color styles to cells
            table_html = re.sub(r'(<td>)(.*?)(</td>)', lambda m: m.group(1) + colorize_cell(m.group(2)) + m.group(3), table_html)

            # Add custom headers
            table_html = table_html.replace('<tbody>', custom_header + "<tbody>", 1)
        else:
            table_html = custom_header + '<tbody>'
            for row_idx, row in df.iterrows():
                table_html += '<tr>'
                for col_idx, value in enumerate(row):
                    table_html += generate_cell_html(value, row_idx, col_idx)
                if row_idx != 0:
                    table_html += '<td><button type="button" class="btn btn-danger btn-sm add_remove_row_btns remove-row"><i class="fa-solid fa-trash"></i></button></td>'
                table_html += '</tr>'
            table_html += '</tbody>'

            uuid_table = uuid.uuid4()
            table_html = f"""
            <form>
                <table class="table table-bordered table-hover table-sm text-center custom-table" id="{uuid_table}" load_info_header="{load_info_header}">
                    {table_html}
                </table>
                <div class="d-flex justify-content-between">
                    <button type="button" class="ml-2 btn btn-success save_table" style="font-size:10px;" id>Save</button>
                    
                    <button type="button" class="btn mr-1 btn-uptycs btn-sm add_new_row" style="font-size:10px;" data-table-id="{uuid_table}">Add Row</button>
                </div>            
            </form>"""

        # Return the final HTML string
        # return f"""{heading_text}
        #         <div class="tab-cont form-group">
        #             {table_html}
        #         </div>
        #         """
        # import uuid
        if is_comparison_table:
            unique_id_for_each_table = uuid.uuid4()

            # Create tab navigation
            html_text = f'<ul class="nav nav-tabs" id="tab{unique_id_for_each_table}" role="tablist">'
            html_text += f"""
                <li class="nav-item" style="font-size:14px">
                    <a class="nav-link active" id="table-{unique_id_for_each_table}" 
                    data-toggle="tab" href="#table-content-{unique_id_for_each_table}" role="tab" 
                    aria-controls="table-content-{unique_id_for_each_table}" 
                    aria-selected="true">
                    Table
                    </a>
                </li>

                <li class="nav-item" style="font-size:14px" id={unique_id_for_each_table} onclick='generate_dynamic_graph(this)'>
                    <a class="nav-link" id="graph-{unique_id_for_each_table} " 
                    data-toggle="tab" href="#graph-content-{unique_id_for_each_table}" role="tab" 
                    aria-controls="graph-content-{unique_id_for_each_table}" 
                    aria-selected="false">
                    Graph
                    </a>
                </li>
            """
            html_text += "</ul>"

            # Create tab content
            html_text += f'<div class="tab-content" id="tab-content-{unique_id_for_each_table}">'
            html_text += f"""
                <div class="tab-pane fade show active" id="table-content-{unique_id_for_each_table}" 
                    role="tabpanel" aria-labelledby="table-{unique_id_for_each_table}">
                    {table_html}
                </div>

                <div class="tab-pane fade" id="graph-content-{unique_id_for_each_table}" 
                    style="background-color: #191b1f; color: #EAEAEA;" 
                    role="tabpanel" aria-labelledby="graph-{unique_id_for_each_table}">
                    <canvas id="chart-{unique_id_for_each_table}" width="400" height="200"></canvas>
                </div>

            """
            html_text += "</div>"
            table_html = html_text
        # Final HTML return with collapsible section
        table_collapse_uuid = uuid.uuid4()
        final_html = f"""
        <p>
            <button class="btn btn-light btn-sm" style="display: block;width:50%;border-radius: 5px;font-size:12px;border-color:#b4b4b4;" 
            type="button" data-toggle="collapse" data-target="#collapseExample{table_collapse_uuid}" 
            aria-expanded="true" aria-controls="collapseExample{table_collapse_uuid}">
                {heading_text}
            </button>
        </p>
        <div class="collapse show mb-3" id="collapseExample{table_collapse_uuid}">
            <div class="tab-cont form-group">
                {table_html}
            </div>
        </div>
        """
        return final_html



    def attach_plot_as_image(self,piechart_name, image, heading_tag):
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")  # Adjust format if necessary
        img_byte_array = buffered.getvalue()
        # Encode byte stream to Base64
        img_base64 = base64.b64encode(img_byte_array).decode('utf-8')
        # Create HTML img tag
        # return f"""
        #         <h{heading_tag}>{piechart_name}</h{heading_tag}>
        #         <img src="data:image/png;base64,{img_base64}" alt="Image" class="img-fluid w-100"  />
        # """
    
        charts_collapse_uuid = uuid.uuid4()
        return f"""<p>
                    <button class="btn btn-sm analysis_btn-hover-effect" type="button"
                        data-toggle="collapse" 
                        data-target="#collapseExample{charts_collapse_uuid}" 
                        aria-expanded="true" 
                        aria-controls="collapseExample{charts_collapse_uuid}">
                        <h{heading_tag}>{piechart_name}</h{heading_tag}>
                    </button>
                    </p>
                    <div class="collapse show mb-3" id="collapseExample{charts_collapse_uuid}">
                        <img src="data:image/png;base64,{img_base64}" alt="Image" class="img-fluid w-100"  />
                    </div>
                """
    def attach_saved_charts(self, dict_of_list_of_filepaths, base_graphs_path, url_for, document_ids_mapping, main_doc_id):
        html_text = ""
        for main_heading in dict_of_list_of_filepaths:
            unique_id = str(uuid.uuid4())
            html_text += f"""
                        <hr style="border: 0; height: 2px; background: linear-gradient(to right, grey, white);">

                        <div class="pt-2 mb-4" style="text-align:center;display: block; width: 47%; border-radius: 7px; border: 1px solid #b7b7b7;  background-color:#edf5ff;">
                            <h5>{main_heading}</h5>
                        </div>     
                    """
            for filepath in dict_of_list_of_filepaths[main_heading]:
                if os.path.exists(os.path.join(base_graphs_path, filepath)):
                    unique_id_for_each_image = uuid.uuid4()
                    base_filename = os.path.basename(filepath)
                    base_filename_without_extension = str(os.path.splitext(base_filename)[0])

                    unique_id = str(uuid.uuid4())

                    html_text += f"""
                    <p>
                        <button class="btn btn-light " style="display: block; width: 40%; border-radius: 10px; border-color: #b4b4b4;" type="button" data-toggle="collapse" data-target="#collapseExample{unique_id}" aria-expanded="false" aria-controls="collapseExample{unique_id}">
                            <h6 class="">{base_filename_without_extension}</h6>
                        </button>
                    </p>
                    <div class="collapse " id="collapseExample{unique_id}">
                    """
                    

                    # Create tabs
                    html_text += f'<ul class="nav nav-tabs" id="tab{unique_id_for_each_image}" role="tablist">'
                    for index, (sprint_run_string, document_id) in enumerate(document_ids_mapping.items()):
                        curr_filepath = filepath.replace(main_doc_id, document_id)
                        active_class = "active" if index == 0 else ""

                        html_text += f"""
                            <li class="nav-item" style="font-size:14px">
                                <a class="nav-link {active_class}" id="tab-{unique_id_for_each_image}-{index}" 
                                data-toggle="tab" href="#tab-content-{unique_id_for_each_image}-{index}" role="tab" 
                                aria-controls="tab-content-{unique_id_for_each_image}-{index}" 
                                aria-selected="{'true' if index == 0 else 'false'}">
                                {sprint_run_string}
                                </a>
                            </li>
                        """
                    html_text += "</ul>"

                    # Create tab content
                    # html_text += f'<div class="tab-content" id="tab-content-{unique_id_for_each_image}">'
                    html_text += f'<div class="tab-content">'
                    for index, (sprint_run_string, document_id) in enumerate(document_ids_mapping.items()):
                        curr_filepath = filepath.replace(main_doc_id, document_id)
                        active_class = "show active" if index == 0 else ""

                        html_text += f"""
                            <div class="mb-4 tab-pane fade {active_class} images_transition_over_sprints" id="tab-content-{unique_id_for_each_image}-{index}" 
                                role="tabpanel" aria-labelledby="tab-{unique_id_for_each_image}-{index}">
                                <img src="{url_for('serve_image', filename=curr_filepath)}" alt="{curr_filepath}" class="img-fluid w-100" />                                                
                            </div>
                        """
                    html_text += "</div>"

                    html_text += """
                    </div>
                    """
                else:
                    print(f"{os.path.join(base_graphs_path, filepath)} does not exist")
            
        return html_text
    
class perf_load_report_publish:
    def __init__(self,dbname,coll_name,sprint_runs_list,parent_page_title, report_title, email_address, api_key, space, url,isViewReport = False):
        client = MongoClient(MONGO_CONNECTION_STRING)
        self.dbname =dbname
        self.collname = coll_name
        self.database = client[dbname] 
        self.collection = self.database[coll_name]
        self.sprint_runs_list=sprint_runs_list
        self.main_sprint,self.main_run = sprint_runs_list[0][0],sprint_runs_list[0][1]
        self.sprint_runs_list.pop(0)
        self.main_result=self.collection.find_one({"load_details.data.sprint":self.main_sprint , "load_details.data.run":self.main_run})
        self.all_keys = list(self.main_result.keys())
        self.all_keys.remove('_id')
        print(f"All keys found in main document are : \n {self.all_keys}")

        self.confluence_page_mappings={}
        self.main_build = self.main_result["load_details"]["data"]["build"]
        self.id = str(self.main_result["_id"])
        self.document_specific_path = os.path.join(dbname,coll_name,self.id)
        self.parent_page_title=parent_page_title
        self.report_title=report_title
        self.email_address=email_address
        self.api_key=api_key
        self.space=space
        self.url = url
        self.isViewReport=isViewReport

        self.document_ids_mapping = {f"{self.main_sprint}_run{self.main_run}":self.id}
        for curr_sprint, curr_run in self.sprint_runs_list:
            self.document_ids_mapping[f"{curr_sprint}_run{curr_run}"] = str(self.get_key_result(curr_sprint, curr_run, "_id")["_id"])
        print(self.document_ids_mapping)


    def get_key_result(self,sprint,run,key_name):
        filter = {f"{key_name}":1}
        result=self.collection.find_one({"load_details.data.sprint":sprint , "load_details.data.run":run},filter)
        return result
    
    def create_report_page(self,parent_page_title, report_title):
        if self.isViewReport : return ViewReportClass(), "noerror"
        obj = publish_to_confluence(parent_page_title, report_title, self.email_address, self.api_key, self.space, self.url)
        flag, err = obj.create_page()
        if flag == False:
            print(f"error while creating confluence page : {err}")
            return None,err
        else:
            print(f"Created new confluence page : {report_title}")
            return obj,err
        

    def merge_dfs(self,merge_on_cols,key_name,parent_key_name):
        all_dfs = []
        builds=[]
        for sprint,run in self.sprint_runs_list:
            build = self.get_key_result(sprint,run,f"load_details.data.build")["load_details"]["data"]["build"]
            try:
                if parent_key_name:
                    result = self.get_key_result(sprint,run,f"{parent_key_name}.data.{key_name}")
                    if not result:continue
                    result = result[parent_key_name]["data"][key_name]["data"]
                else:
                    result = self.get_key_result(sprint,run,f"{key_name}")
                    if not result:continue
                    result = result[key_name]["data"]
            except:
                result={}
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
        return merged_df,builds
    
    def process_abs_rel_cols(self,val):
        if val > 0: return f"{val} ⬆️"
        elif val < 0: return f"{abs(val)} ⬇️"
        elif val == 0: return 0
        else :
            return val
        
    def preprocess_df(self,final_df):
        numeric_cols = final_df.select_dtypes(include=[np.number]).columns
        non_numeric_cols = final_df.select_dtypes(exclude=[np.number]).columns
           
        fill_values = {}
        fill_values.update({col: 0 for col in numeric_cols})
        fill_values.update({col: "NaN" for col in non_numeric_cols})
        final_df = final_df.fillna(fill_values)
        
        new_sum_row=dict([(int_col,final_df[int_col].sum()) for int_col in numeric_cols])
        new_sum_row.update(dict([(str_col,"SUM") for str_col in non_numeric_cols]))
        final_df = final_df._append(new_sum_row, ignore_index=True)
        return final_df        
        
    def compare_dfs(self,compare_col,merged_df,builds,merge_on_cols):
        if compare_col not in merged_df.columns:return None
        main_col_name = f"{compare_col}_{self.main_build}_run{self.main_run}"
        merged_df.rename(columns={compare_col: main_col_name}, inplace=True)
        cols_order = [f"{compare_col}_{build}" for build in reversed(builds)] 
        if not cols_order:return None
        cols_order = merge_on_cols+cols_order+[main_col_name]
        final_df = merged_df.loc[:, cols_order]
        final_df = self.preprocess_df(final_df)
        final_df["Absolute"] = round(final_df[cols_order[-1]]-final_df[cols_order[-2]],2)
        final_df["Relative %"] = np.where(final_df[cols_order[-2]] != 0,
                                          round((final_df[cols_order[-1]]-final_df[cols_order[-2]])*100/final_df[cols_order[-2]],2),
                                          100.0)

        final_df["Absolute"] = final_df["Absolute"].apply(self.process_abs_rel_cols)
        final_df["Relative %"] = final_df["Relative %"].apply(self.process_abs_rel_cols)
        return final_df
    
    def captilise_heading(self,heading):
        heading = str(heading).replace("_"," ")
        heading=heading.capitalize()
        return heading

    def add_standard_table(self,table_dictionary,key_name,curr_page_obj,parent_key=None):
        html_text = custom_string()
        schema = table_dictionary["schema"]
        merge_on_cols = schema.get("merge_on_cols",[])
        compare_cols = schema.get("compare_cols",[])
        display_exact_table = schema.get("display_exact_table", True)
        collapse = table_dictionary.get("collapse", True)
        isEditable=schema.get("isEditable",False)
        data=table_dictionary["data"]
        main_df = pd.DataFrame(data)
        if main_df.empty : return ""

        copy_main_df = main_df.copy()
        if "ccurac" not in key_name and "ugs raised" not in key_name and "servations" not in key_name and "environment details" not in key_name: 
            copy_main_df = self.preprocess_df(copy_main_df)

        heading_size = 3+2 if parent_key else 2+2

        if len(self.sprint_runs_list) > 0 and len(merge_on_cols) > 0 and len(compare_cols) > 0:
            merged_df, builds = self.merge_dfs(merge_on_cols,key_name,parent_key_name = parent_key)
            # if no comparison tables, show the exact table
            if display_exact_table or len(builds) == 0: 
                html_text+=curr_page_obj.add_table_from_dataframe(f"<h{heading_size}>{self.captilise_heading(key_name)}</h{heading_size}>", copy_main_df, collapse=collapse,isEditable=isEditable,key_name=key_name, dbname = self.dbname, collname = self.collname, sprint = self.main_sprint, run = self.main_run)
            else: 
                html_text+=curr_page_obj.add_text(f"<h{heading_size}>{self.captilise_heading(key_name)}</h{heading_size}>")
               
            if len(builds) > 0:
                for compare_col in compare_cols:
                    returned_df = self.compare_dfs(compare_col,merged_df,builds,merge_on_cols)
                    if returned_df is not None and not returned_df.empty :
                        html_text+=curr_page_obj.add_table_from_dataframe(f"<h{heading_size+1}>Comparison on {self.captilise_heading(compare_col)}</h{heading_size+1}>", returned_df.copy(), collapse=collapse,isEditable=isEditable,key_name=key_name, dbname = self.dbname, collname = self.collname, sprint = self.main_sprint, run = self.main_run, is_comparison_table = True)
                        main_df = returned_df.copy()
        else:
            html_text+=curr_page_obj.add_table_from_dataframe(f"<h{heading_size}>{self.captilise_heading(key_name)}</h{heading_size}>", copy_main_df, collapse=collapse,isEditable=isEditable,key_name=key_name, dbname = self.dbname, collname = self.collname, sprint = self.main_sprint, run = self.main_run)
        html_text=html_text.replace('style="text-align: right;"', '')
        return html_text


    def extract_all_variables_and_publish(self, url_for):
        try:
            _,err = self.create_report_page(self.parent_page_title, self.report_title)
            if not _:
                yield f'data: {{"status": "error", "message": "{err}"}}\n\n'
                return
            if self.isViewReport:
                test_title = self.main_result["load_details"]["data"]["test_title"]
                load_type = self.main_result["load_details"]["data"]["load_type"]
                sprint_runs_text_list = ['_'.join(map(str, x)) for x in self.sprint_runs_list]
                sprint_runs_text_list = list(map(lambda x : f"<span  class='mb-3 btn btn-success btn-sm disabled'>{x}</span>",sprint_runs_text_list))
                sprint_runs_text = f"<span  class='mb-3 btn btn-success btn-sm disabled'>{self.main_sprint}_{self.main_run}</span>"
                if sprint_runs_text_list:
                    vs_span = "<span class='btn mb-3 btn-sm disabled'>vs</span>"
                    joined_text = f"{vs_span}".join(sprint_runs_text_list)
                    sprint_runs_text += f"{vs_span}{joined_text}"
                data = json.dumps({"status": "info", "message": f"<div style='text-align: center; margin-top:10px;'><h3>{load_type} - {str(test_title).capitalize()} Performance Report</h3>{sprint_runs_text}</div><hr style='border: 0; height: 2px; background: linear-gradient(to right, black, #0000ff);'><br>"})
                                                                                                                                                                                                        
                yield f'data: {data}\n\n'
            for key_name in self.all_keys:
                # if key_name not in ['cpu_usages']:continue
                try:
                    html_text =  custom_string()
                    print(f"Processing {str(key_name).capitalize()}")
                    if not self.isViewReport:yield f'data: {{"status": "info", "message": "Processing {str(key_name).capitalize()} section"}}\n\n'
                    key_format = self.main_result[key_name]["format"]
                    schema = self.main_result[key_name]["schema"]
                    data = self.main_result[key_name]["data"]
                    page = schema.get("page" , "Accuracies, DiskSpace Usages, etc..")

                    if page in self.confluence_page_mappings: curr_page_obj = self.confluence_page_mappings[page]
                    else:
                        curr_page_obj,err = self.create_report_page(self.report_title, f"{page}-{self.report_title}")
                        if not curr_page_obj:
                            yield f'data: {{"status": "error", "message": {err}}}\n\n'
                            return
                            # return err, "error"
                        self.confluence_page_mappings[page]=curr_page_obj
                    
                    note_element = f'<span style="color:red;"><b><i>{str(self.main_result[key_name].get("note",""))}</i></b></span>'
                    html_text += curr_page_obj.add_text(note_element)
                    
                    if key_format == "table":
                        html_text += self.add_standard_table(self.main_result[key_name],key_name,curr_page_obj)
                
                    elif key_format == "nested_table":
                        html_text+=curr_page_obj.add_text(f"<h4>{self.captilise_heading(key_name)}</h4>")

                        for nested_key_name in data.keys():
                            if not self.isViewReport:yield f'data: {{"status": "info", "message": "Processing nested table : {str(nested_key_name).capitalize()}"}}\n\n'
                            html_text += self.add_standard_table(self.main_result[key_name]["data"][nested_key_name],nested_key_name,curr_page_obj,parent_key=key_name)

                    elif key_format == "mapping":
                        html_text+=curr_page_obj.add_text(f"<h4>{self.captilise_heading(key_name)}</h4>")
                        for key,value in data.items():
                            if type(value) != dict:
                                if type(value) == str and "http" in value:
                                    value = f'<a href="{value}">{value}</a>'
                                html_text+=curr_page_obj.add_text(f"<p>{self.captilise_heading(key)} : {value}</p>\n")

                            else:
                                html_text+=curr_page_obj.add_text(f"<h5>{str(key)}</h5>")
                                for nested_key,nested_value in value.items():
                                    html_text+=curr_page_obj.add_text(f"<p>{self.captilise_heading(nested_key)} : {nested_value}</p>\n")

                    elif key_format == "list":
                        curr_list = set(data)
                        if len(curr_list) !=0 :
                            curr_list_to_string = ", ".join(list(map(str,curr_list)))
                            html_text+=curr_page_obj.add_text(f"<h4>{self.captilise_heading(key_name)}</h4>")
                            if len(self.sprint_runs_list) == 0 :
                                print("Previous sprint not found ... ")
                                html_text+=curr_page_obj.add_text(f'<p><span style="color: black;">{curr_list_to_string} </span></p>')

                            else:
                                print("prev sprints provided.. checking")
                                prev_sprint,prev_run = self.sprint_runs_list[0][0],self.sprint_runs_list[0][1]
                                prev_data=self.get_key_result(prev_sprint,prev_run,key_name)
                                if not prev_data:
                                    print(f"WARNING : Previous sprint data for {key_name} is not found")
                                    html_text+=curr_page_obj.add_text(f'<p><span style="color: black;">{curr_list_to_string} </span></p>')
                                else:
                                    print("Previous sprint data found")
                                    prev_list = set(prev_data[key_name]["data"])
                                    if curr_list == prev_list:
                                        html_text+=curr_page_obj.add_text(f'<p><span style="color: green;">No new topics added/deleted </span></p>')
                                    else:
                                        newly_added = curr_list - prev_list
                                        deleted = prev_list - curr_list
                                        if len(newly_added)>0:
                                            html_text+=curr_page_obj.add_text(f'<p><span style="color: blue;">{len(newly_added)} newly added topics found : {newly_added}</span></p>')
                                        if len(deleted)>0:
                                            html_text+=curr_page_obj.add_text(f'<p><span style="color: blue;">{len(deleted)} topics are deleted : {deleted}</span></p>')
                    
                    elif key_format == "analysis":
                        if len(self.sprint_runs_list) == 0:
                            warning_message = "Previous sprints not provided by the user to compare and analyze resource usages"
                            print(warning_message)
                            continue
                        prev_sprint,prev_run = self.sprint_runs_list[0][0],self.sprint_runs_list[0][1]
                        prev_data=self.get_key_result(prev_sprint,prev_run,key_name)
                        if not prev_data:
                            yield f'data: {{"status": "warning", "message": "Found no previous data for sprint {prev_sprint} and run {prev_run}"}}\n\n'
                            continue
                        prev_data=prev_data[key_name]["data"]
                        temp_images,memory_combined_df,cpu_combined_df=analysis_main(data["memory_usages_analysis"],prev_data["memory_usages_analysis"],data["cpu_usage_analysis"],prev_data["cpu_usage_analysis"],main_build_load_details=self.main_result["load_details"]["data"],prev_build_load_details=self.get_key_result(prev_sprint,prev_run,"load_details")["load_details"]["data"] )                    
                        html_text+=curr_page_obj.add_text(f'<h4>Contributers to Resource Usage increase/decrease</h4>')
                        html_text+=curr_page_obj.add_table_from_dataframe(f'<h5>{self.captilise_heading("memory_usages_analysis")}</h5>', memory_combined_df.copy(), collapse=False)
                        html_text+=curr_page_obj.add_table_from_dataframe(f'<h5>{self.captilise_heading("cpu_usage_analysis")}</h5>', cpu_combined_df.copy(), collapse=False)
                        html_text+=curr_page_obj.add_text(f'<h4>Complete Analysis piecharts for resource utilizations</h4>')
                        for piechart_name in temp_images:
                            html_text+=curr_page_obj.attach_plot_as_image(piechart_name, temp_images[piechart_name], 3)
                    elif key_format == "charts":
                        # base_graphs_path=os.path.join(schema["base_graphs_path"])
                        charts_paths_dict={}
                        html_text += f"<h4>Charts</h4>"
                        for main_heading,inside_charts in data.items():
                            temp_list_for_confluence=[f'{os.path.join(self.document_specific_path,main_heading,str(file_name).replace("/","-")+".png")}' for file_name in list(inside_charts.keys())]
                            # temp_list_for_confluence=[f'{os.path.join(self.document_specific_path,main_heading,str(file_name).replace("/","-")+".png")}' for file_name in list(inside_charts.keys())]
                            charts_paths_dict[main_heading] = temp_list_for_confluence
                            # if not self.isViewReport:yield f'data: {{"status": "info", "message": "Attaching {main_heading}"}}\n\n'

                        charts_generator=curr_page_obj.attach_saved_charts(charts_paths_dict,base_graphs_path=schema["base_graphs_path"], url_for=url_for, document_ids_mapping=self.document_ids_mapping, main_doc_id=self.id)
                        if not self.isViewReport:
                            for current_chart_status_msg in charts_generator:
                                yield f'data: {{"status": "info", "message": "{current_chart_status_msg}"}}\n\n'
                        else:
                            html_text+=charts_generator

                    if self.isViewReport:
                        html_text+='<hr style="border: 0; height: 2px; background: linear-gradient(to right, black, #0000ff);">'
                        json_data = json.dumps({
                            "status": "info",
                            "message": html_text
                        })
                        yield f'data: {json_data}\n\n'

                    curr_page_obj.update_and_publish()
                except Exception as e:
                    error_msg_for_current_iteration = json.dumps({
                            "status": "warning",
                            "message": f"Error occured while processing {key_name}. Please check if this key has valid format in mongo. {str(e)}"
                    })
                    yield f'data: {error_msg_for_current_iteration}\n\n'
            if not self.isViewReport:yield f'data: {{"status": "success", "message": "Report published successfully"}}\n\n'
            else: yield f'data: {{"status": "success", "message": "Report generated successfully"}}\n\n'
        except Exception as e:
            error_message = f"Unexpected error occurred: {str(e)}"
            # Safely serialize the message to JSON
            data = json.dumps({"status": "error", "message": error_message})
            yield f'data: {data}\n\n'

if __name__=='__main__':
    url='https://raghav-m.atlassian.net'
    email_address = "pbpraghav@gmail.com"
    space = 'IT'
    parent_page_title = 'TEST'  
    import uuid
    report_title = f"TEST {uuid.uuid4()}"

    list_of_sprint_runs_to_show_or_compare = [[160,5]]
    database_name = "Osquery_LoadTests_New"
    collection_name = "ControlPlane"

    obj = perf_load_report_publish(database_name, collection_name, list_of_sprint_runs_to_show_or_compare, None, None, None, None, None, None,isViewReport=True)
    # obj = perf_load_report_publish(database_name, collection_name, list_of_sprint_runs_to_show_or_compare, parent_page_title, report_title, email_address, api_key, space, url,isViewReport=False)
    if "new_format" not in obj.all_keys:
        print({"status": "ERROR", "message": "We are not dealing with new format mongo document"})
    else:
        obj.all_keys.remove('new_format')
        # message , status= obj.extract_all_variables_and_publish()
        # return Response(obj.extract_all_variables_and_publish(), content_type='text/event-stream')
        for msg in obj.extract_all_variables_and_publish():
            print(msg)
        print({"status": "success", "message": "done"})
    


    # obj = perf_load_report_publish(database_name, collection_name, list_of_sprint_runs_to_show_or_compare, parent_page_title, report_title, email_address, api_key, space, url)
    # if "new_format" not in obj.all_keys:
    #     print("error : We are not dealing with new format mongo document")
    # else:
    #     obj.all_keys.remove('new_format')
    #     result , status= obj.extract_all_variables_and_publish()
    #     print(status, result)
    
    
    
