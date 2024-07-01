from confluence_api import publish_to_confluence
import pandas as pd

if __name__ == "__main__":

    # CONFLUENCE_URL='https://uptycsjira.atlassian.net'
    # CONFLUENCE_USERNAME = "masabathularao@uptycs.com"
    # CONFLUENCE_PASSWORD = "ATATT3xFfGF02rG4e5JQzZZ_mVdAkwKKGnjRLYIupWToEGxZm8X-r5dUrAzSAdzGi5FPXMIn_IacnJjOwORsOQV7noObZmkdHqsaHHIzw4pTVyid2Jh3rVmLjM8iw5_hmaK7rFWSMz1JBpQq44vGV1FJs7P-89zijob43kBuxHzfFJJxl5IlM0w=7CE826E3"
    # SPACE_KEY = '~71202040c8bf45840d41c598c0efad54382c7b'
    # PARENT_PAGE_TITLE = 'PUBLISH TEST'


    
    CONFLUENCE_URL = 'https://raghav-m.atlassian.net'
    CONFLUENCE_USERNAME = "pbpraghav@gmail.com"
    CONFLUENCE_PASSWORD ="ATATT3xFfGF0DFIeyQhHyNt8MaLHpITWpKl_lJLd1OiQHXoVnYP25aYEtC_ByMOBaBhwz_hYOI8YEqMgXSSX2r0ddjKA4ksQpIoeluC2OhmAdg4tWro23iC-dDYcj5OEWn8sHuQ23dcrVbSftQQPh02c3u2ykBKB_XxNZKvs_p0nfN9dtcKxVn0=B84EB549"
    SPACE_KEY = 'SD'
    PARENT_PAGE_TITLE = 'QWERT'

    NEW_PAGE_TITLE = 'TEST - new layout 43'


    obj = publish_to_confluence(parent_page_title=PARENT_PAGE_TITLE, report_title=NEW_PAGE_TITLE, email_address=CONFLUENCE_USERNAME, api_key=CONFLUENCE_PASSWORD,space=SPACE_KEY,url=CONFLUENCE_URL)
    flag,error=obj.create_page()
    if flag:
        # obj.attach_single_file("/Users/masabathulararao/Downloads/process node RAM used percentage.png" , "1")

        obj.attach_single_file("/Users/masabathulararao/Downloads/Uptycs redis Connections.mp4" , "1")
        obj.attach_single_file("/Users/masabathulararao/Downloads/_71202040c8bf45840d41c598c0efad54382c7b-TEST -143 multi sample1-291223-113248.pdf" , "1")

        obj.add_text("<h2>Load Details</h2> <p>this is paragraph</p>")
        obj.add_text("<p> load start time ist : 2023-03-22 23:10</p>")
        obj.add_text("<p> Another p tag key : value</p>")

        s="SAM-1"
        obj.add_jira_issue_by_key(s)
        obj.add_jira_issue_by_key(s)
        obj.add_jira_issue_by_key(s)
        obj.add_jira_issue_by_key(s)

        obj.add_jira_issue_by_link("https://raghav-m.atlassian.net/browse/SAM-2")
        
        data = {'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [30, 35, 25],
        'City': ['New York', 'San Francisco', 'Los Angeles']}
        df = pd.DataFrame(data)
        obj.add_table_from_dataframe("<h2>collapseable table</h2>",df,collapse=True)

        obj.add_table_from_dataframe("<h2>non-collapsable table</h2>",df,collapse=False)

        # import os
        # dict_of_list_of_images={}
        # dirname="/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/other/images"
        # for root,dirs,files in os.walk(dirname):
        #     if len(files)>0:
        #         base_dir=os.path.basename(root)
        #         main_dir=os.path.dirname(root)
        #         dict_of_list_of_images[base_dir] = [main_dir+'/'+base_dir+'/'+file for file in files]

        # obj.attach_saved_charts(dict_of_list_of_images)

        # data = {'Name': [' ', "", '      '],
        # 'Age': [30, 35, 25],
        # 'City': ['good', 'nice', 'not good']}
        # df = pd.DataFrame(data)
        # print(df)
        # obj.add_table_from_dataframe("<h2>collapsable with staus=name</h2>",df,collapse=True,status_col='Name')

        # data = {'Name': ['passed', '', 'Charlie'],
        # 'Age': ['passed', 'ok', 'bad'],
        # 'City': ['New York', 'San Francisco', 'Los Angeles']}
        # df = pd.DataFrame(data)

        # d={'Test': {0: 'Check for Rule passed Lag', 1: 'Check for ingestion lag', 2: 'Check for db-events lag', 3: 'Check for equal distribution of HDFS disk usage ', 4: 'Data good check (accuracy)'}, 'Status': {0: 'passed', 1: 'good', 2: '', 3: '       ', 4: 'passed'}, 'Comments': {0: '0 min, 0 min extra time to drain for cluster1, clsuter2 respectively', 1: '9 min, 3 min extra time to drain for cluster1, clsuter2 respectively', 2: '28 min, 0 min extra time to drain for cluster1, clsuter2 respectively', 3: '', 4: ''}}
        # print(d)
        # df = pd.DataFrame.from_dict(d)

        # obj.add_table_from_dataframe("<h2>collapsable with staus=age</h2>",df,collapse=True,status_col="Status")

        # data = {'Name': ['first', ' ' , 'thrid',  '    foruthqd  ' , '','sissxth '],
        #         'Status':['passed','failed','    ','passed' , '  failed   ', '      pass1 '],
        #         'Status2':['passed','failed','    ','passed' , '  failed   ', '      pass 1'],
        #         'relative': ["                  0.03%           ⬆️               ", "0.33%  ⬇️", "1.23% ⬆️" , "10.48%  ⬇️" , "4.103%  ⬇️                ","4.103%  ⬇️"],
        #         'absolute': ['8.76% ⬆️', '               110.233%  ⬇️', '9.0% ⬆️' , "5.9%  ⬇️" , "6.065%  ⬇️","4.103%  ⬇️"],
        #         'relative2': ["             0.03% ⬆️", "0.33%  ⬇️", "          1.23% ⬆️" , "10.48%  ⬇️           " , "4.103%  ⬇️","4.103%  ⬇️"],
        #         'absolute2': ['             8.76% ⬆️', '110.233%  ⬇️', '9.0% ⬆️' , "5.9%             ⬇️" , "6.065%  ⬇️","4.103%  ⬇️"]}
        # df = pd.DataFrame(data)

        # obj.add_table_from_dataframe("<h2>color table</h2>",df,collapse=True,status_col="Status",red_green_column_list=['relative','absolute'])


        # Assuming you have two dataframes df1 and df2
        # data1 = {'Category': ['A', 'B', 'C'],
#                 'Value': [10, 20, 15]}
#         df1 = pd.DataFrame(data1)

#         # Sample data for DataFrame 2
#         data2 = {'Category': ['X', 'Y', 'Z'],
#                 'Value': [30, 25, 18]}
#         df2 = pd.DataFrame(data2)
#         headings = ['Table 1', 'Table 2']
#         dataframes = [df1, df2]

#         # obj.add_tables_side_by_side(headings, dataframes, collapse=True)
# # Assuming 'self' is an instance of the class with 'body_content' attribute
#         # obj.add_tables_side_by_side("TwoTablesLayout", "Table 1 Heading", df1, "Table 2 Heading", df2)
#         obj.div()

       
        
        # obj.add_text("{color:red}This text is red.{color}")
        # obj.add_text("""<p style="color:red">This is a paragraph.</p>
        #             <p style="color:blue">This is another paragraph.</p>
        #             """)    
        # obj.add_text("""<p style="color:#FF0000";>Testing text color</p>""")
        # cell_content = '<div style="background-color: red;">Your Cell Content</div>'

        # # Define    the table HTML code with the cell content
        # table_html = f'<table><tr><td>{cell_content}</td></tr></table>'
        # obj.add_table_from_html("<h2>cell color</h2>",table_html)
        # t= """<tr>
        # <td >
        # <p>asasd</p>
        # </td>

        # <td >
        # <p>30</p>
        # </td>
        # <td style="background-color: #FFBDAD;">
        # <p>good</p>
        # </td>
        # </tr>"""
       
        # # obj.add_table_from_html("had",t)
        # obj.add_text('<span style="color: red;">This text is red.</span>')
        obj.update_and_publish()
    else:
        print(error)

