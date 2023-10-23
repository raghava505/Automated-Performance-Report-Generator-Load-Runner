from atlassian import Confluence
import logging
import pandas as pd
import os

# logging.basicConfig(level=logging.DEBUG)

class publish_to_confluence:
    def __init__(self,parent_page_title,report_title,email_address,api_key,space='PERF',url='https://uptycsjira.atlassian.net'):

        self.confluence = Confluence(
            url=url,
            username = email_address,
            password=api_key
            )

        if self.confluence.page_exists(space, parent_page_title, type=None) == False:
            print(f"ERROR : The parent page with title '{parent_page_title}' doesn't exist! Please enter a valid page title")
            return None
        elif self.confluence.page_exists(space, report_title, type=None) == True:
            print(f"ERROR : A page with title '{report_title}' already exists! Please enter a new title")
            return None
        else:
            print(f"Parent page '{parent_page_title}' exists")
        
        self.space = space
        self.title=report_title
        self.parent_title=parent_page_title
        self.body_content="""
                            <ac:structured-macro ac:name="toc">
                                <ac:parameter ac:name="maxLevel">6</ac:parameter>
                            </ac:structured-macro>
                            """

        parent_page=self.confluence.get_page_by_title(space=space, title=self.parent_title)
        self.parent_page_id = parent_page['id']
        
        print(f"Creating new child page '{self.title}', under '{self.parent_title}'")
        created_new_page=self.confluence.create_page(space=self.space, title=self.title, 
                                body=self.body_content,parent_id=self.parent_page_id, type='page', representation='storage',
                                editor='v2', full_width=True,
                                )
        
        self.page_id = created_new_page['id']
        print(f"Created new page with id {self.page_id}")

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
        positive_words = [
            "passed", "validated", "achieved", "verified", "succeeded", "accurate",
            "effective", "excellent", "efficient", "thorough", "flawless", "optimal",
            "superior", "outstanding", "aced", "exceptional", "impressive", "top-notch",
            "proficient", "masterful", "seamless", "airtight", "error-free", "superb",
            "remarkable","success","sucess","pass","ok","yes","done","reached","fine",
            "good","nice","not bad","authenticated","superb","super","reached","met",
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
    
    def add_table_from_dataframe(self,heading,dataframe,collapse=False,status_col=None):
        html_table = dataframe.to_html(classes='table table-striped', index=False)
        if status_col:
            col_values = list(dataframe[status_col])
            print(col_values)
            for val in col_values:
                html_table=html_table.replace(str(val),self.get_status_macro(val))
        self.add_table_from_html(heading=heading,html_table=html_table,collapse=collapse)
        
    def add_text(self,html_text):
        self.body_content+=html_text

    def attach_single_image(self,image_file_path,heading_tag):
        base_filename = os.path.basename(image_file_path)
        print(f"Attaching : {base_filename}")
        base_filename_without_extension = str(os.path.splitext(base_filename)[0])
        attachment=self.confluence.attach_file(image_file_path,name=str(base_filename),content_type="image/png",title=self.title, space=self.space)
        attachment_id = attachment['results'][0]['id']
        self.body_content+=f"""
                            <h{heading_tag}>{str(base_filename_without_extension)}</h{heading_tag}>
                                <ac:image ac:height="1400">
                                    <ri:attachment ri:filename="{str(base_filename)}" ri:space-key="{self.space}" />
                                </ac:image>
                        """
        
    def attach_saved_charts(self, dict_of_list_of_filepaths):
        print("Attaching charts ...")
        self.body_content += "<h2>Charts</h2>"
        for directory_name in dict_of_list_of_filepaths:
            print(directory_name)
            self.body_content += f"<h3>{str(os.path.basename(directory_name))}</h3>"

            self.body_content += """
                <ac:structured-macro ac:name="expand">
                <ac:parameter ac:name="title">Click to expand</ac:parameter>
                    <ac:rich-text-body>
            """

            for filepath in dict_of_list_of_filepaths[directory_name]:
                self.attach_single_image(filepath,4)

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

    def update_and_publish(self):
        self.confluence.update_page(self.page_id, self.title, self.body_content, 
                                    parent_id=self.parent_page_id, type='page', 
                                    representation='storage', minor_edit=False, 
                                    full_width=True)
        
        self.close()
