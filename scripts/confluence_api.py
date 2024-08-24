from atlassian import Confluence
import logging
import pandas as pd
import os
import io
import plotly.io as pio

# logging.basicConfig(level=logging.DEBUG)

class publish_to_confluence:
    def __init__(self,parent_page_title,report_title,email_address,api_key,space='PERF',url='https://uptycsjira.atlassian.net'):

        self.confluence = Confluence(
            url=url,
            username = email_address,
            password=api_key
            )
        self.space = space
        self.title=report_title
        self.parent_title=parent_page_title
    
    def create_page(self):
        try:
            if self.confluence.page_exists(self.space, self.parent_title, type=None) == False:
                error_string=f"ERROR : The parent page with title '{self.parent_title}' doesn't exist! Please enter a valid page title"
                return False,error_string
            elif self.confluence.page_exists(self.space, self.title, type=None) == True:
                error_string=f"ERROR : A page with title '{self.title}' already exists! Please enter a new title"
                return False,error_string
            else:
                print(f"Parent page '{self.parent_title}' found")
                # return True,''
        except Exception as e:
            return False,str("ERROR : "+str(e))
        
        try:
            self.body_content="""
                                <ac:structured-macro ac:name="toc">
                                    <ac:parameter ac:name="maxLevel">6</ac:parameter>
                                </ac:structured-macro>
                                <p><ac:structured-macro ac:name=\"children\" ac:schema-version=\"1\">
                                    <ac:parameter ac:name=\"all\">true</ac:parameter></ac:structured-macro></p>
                              
                                """

            parent_page=self.confluence.get_page_by_title(space=self.space, title=self.parent_title)
            self.parent_page_id = parent_page['id']
            
            print(f"Creating new child page '{self.title}', under '{self.parent_title}'")
            created_new_page=self.confluence.create_page(space=self.space, title=self.title, 
                                    body=self.body_content,parent_id=self.parent_page_id, type='page', representation='storage',
                                    editor='v2', full_width=True,
                                    )
            
            self.page_id = created_new_page['id']
            print(f"Created new page with id {self.page_id}")
            return True,""
        except Exception as e:
            return False,str(e)

    def add_table_from_html(self,heading,html_table,collapse=False):
        print(f"adding table : {heading}")
        if collapse:
            html_page = f'''
                {heading}
                <ac:structured-macro ac:name="expand">
                    <ac:parameter ac:name="title">Click to expand</ac:parameter>
                    <ac:rich-text-body>
                            {html_table}
                    </ac:rich-text-body>
                </ac:structured-macro>
            '''
        else:
            html_page=f'''{heading}
                            <body>
                                {html_table}
                            </body>
                        '''
        self.body_content+=html_page

    def get_status_macro(self,title):
        title=title.split('/')[1]
        if len(str(title).strip()) < 1:return ''
        positive_words = [
            "passed", "validated", "achieved", "verified", "succeeded", "accurate",
            "effective", "excellent", "efficient", "thorough", "flawless", "optimal",
            "superior", "outstanding", "aced", "exceptional", "impressive", "top-notch",
            "proficient", "masterful", "seamless", "airtight", "error-free", "superb",
            "remarkable","success","sucess","pass","ok","yes","done","reached","fine",
            "good","authenticated","reached","met",
            "accomplished", "fulfilled"
        ]

        if str(title).strip().lower() in positive_words:
            color="green"
        else:
            color="red"
        status_macro = f'''
        <ac:structured-macro ac:name="status">
            <ac:parameter ac:name="title">{title}</ac:parameter>
            <ac:parameter ac:name="color">{color}</ac:parameter>
        </ac:structured-macro>
        '''
        return status_macro
    
    def get_red_green_text(self,text):
        text = str(text.split('/')[1]).strip()
        if "⬇️" in str(text):
            return f'<span style="color: green;">{text}</span>'
        elif "⬆️" in str(text):
            return f'<span style="color: red;">{text}</span>'
        else:return text

    def add_table_from_dataframe(self,heading,dataframe,collapse=False,status_col=None,red_green_column_list=None):
        if status_col and red_green_column_list and status_col in red_green_column_list:return False,"ERROR : Status col shouldn't be present in red_green_column_list" 
        html_table = dataframe.to_html(classes='table table-striped', index=False)
        if status_col or red_green_column_list:
            status_col_values=[]
            color_col_values=[]
            if status_col:
                dataframe[status_col] = dataframe[status_col].apply(lambda x : f"sm/{x}/sm")
                status_col_values = list(dataframe[status_col].unique())
                print(status_col_values)
            
            if red_green_column_list:
                for column in red_green_column_list:
                    dataframe[column] = dataframe[column].apply(lambda x : f"color/{x}/color")
                    color_col_values.extend(list(dataframe[column].unique()))
                color_col_values=list(set(color_col_values))
                    
            html_table = dataframe.to_html(classes='table table-striped', index=False) 
            for val in status_col_values:
                html_table=html_table.replace(str(val),self.get_status_macro(val))
            for val in color_col_values:
                html_table=html_table.replace(str(val),self.get_red_green_text(val))
        self.add_table_from_html(heading=heading,html_table=html_table,collapse=collapse)
        
    def add_text(self,html_text):
        self.body_content+=html_text

    def attach_single_file(self,image_file_path,heading_tag):
        if os.path.exists(image_file_path):
            # if image_file_path.endswith(".mp4"):
            #     content_type = "video/mp4"
            # else:
            #     content_type="image/gif"
            base_filename = os.path.basename(image_file_path)
            print(f"Attaching : {base_filename}")
            base_filename_without_extension = str(os.path.splitext(base_filename)[0])
            attachment=self.confluence.attach_file(image_file_path,name=str(base_filename),title=self.title, space=self.space)
            attachment_id = attachment['results'][0]['id']
            self.body_content+=f"""
                                <h{heading_tag}>{str(base_filename_without_extension)}</h{heading_tag}>
                                    <ac:image ac:height="1400" ac:width="2100">
                                        <ri:attachment ri:filename="{str(base_filename)}" ri:space-key="{self.space}" />
                                    </ac:image>
                            """
        else:
            print(f"ERROR : {image_file_path} doesnt exist! Skipping this chart ...")
        
    def attach_saved_charts(self, dict_of_list_of_filepaths,main_heading=None):
        if not main_heading:main_heading="Charts"
        print("Attaching charts ...")
        self.body_content += f"<h2>{main_heading}</h2>"
        for directory_name in dict_of_list_of_filepaths:
            print(directory_name)

            if len(dict_of_list_of_filepaths[directory_name]) == 1:
                self.attach_single_file(dict_of_list_of_filepaths[directory_name][0],3)
                continue

            self.body_content += f"<h3>{str(os.path.basename(directory_name))}</h3>"

            self.body_content += """
                <ac:structured-macro ac:name="expand">
                <ac:parameter ac:name="title">Click to expand</ac:parameter>
                    <ac:rich-text-body>
            """

            for filepath in dict_of_list_of_filepaths[directory_name]:
                self.attach_single_file(filepath,4)

            self.body_content += """
                    </ac:rich-text-body>
                </ac:structured-macro>
            """
    
    def add_jira_issue_by_key(self,jira_issue_key):
        print(f"Attaching jira issue : {jira_issue_key}")
        jira_issue_macro = f'''<p>
            <ac:structured-macro ac:name="jira">
                <ac:parameter ac:name="key">{jira_issue_key}</ac:parameter>
            </ac:structured-macro></p>
            '''
        self.body_content+=jira_issue_macro

    def close(self):
        self.confluence.close()

    def add_jira_issue_by_link(self,link_string):
        base=link_string.split('//')[-1]
        key=base.split('/')[2]
        self.add_jira_issue_by_key(key)

    def attach_plot_as_image(self, chart_name, fig, heading_tag):
        try:
            print(f"Attaching : {chart_name}")
            img_bytes = pio.to_image(fig, format='png') # Convert Plotly figure to image bytes
            img_stream = io.BytesIO(img_bytes) # Create an Image object from the image bytes
            attachment = self.confluence.attach_content(content=img_stream, name=chart_name, content_type="image/png", title=self.title, space=self.space)
            attachment_id = attachment['results'][0]['id']
            self.body_content += f"""
                                <h{heading_tag}>{str(chart_name)}</h{heading_tag}>
                                    <ac:image ac:height="1400">
                                        <ri:attachment ri:filename="{str(chart_name)}" ri:space-key="{self.space}" />
                                    </ac:image>
                            """
        except Exception as err:
            print(f"ERROR : {err}")
    
    def attach_plots_as_charts(self, dict_of_figures):
        print("Attaching charts ...")
        self.body_content += "<h2>Charts</h2>"
        for chart_name in dict_of_figures:
            self.attach_plot_as_image(chart_name, dict_of_figures[chart_name], 4)

    def update_and_publish(self):
        self.confluence.update_page(self.page_id, self.title, self.body_content, 
                                    parent_id=self.parent_page_id, type='page', 
                                    representation='storage', minor_edit=False, 
                                    full_width=True)
        print("Page published successfully!")
        self.close()
