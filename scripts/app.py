from flask import Flask, render_template, request, jsonify
from publish_perf_load_report import perf_load_report_publish
import ast

app = Flask(__name__)

# class perf_load_report_publish:
#     def __init__(self, *args):
#         # Initialize with the passed parameters
#         self.all_keys = ["new_format"]  # example key for the demo
        
#     def extract_all_variables(self):
#         # Simulate the extraction process
#         return "Variables extracted successfully!"
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    # Get form data from the request
    url = request.form['url']
    email_address = request.form['email_address']
    api_key = request.form['api_key']
    space = request.form['space']
    parent_page_title = request.form['parent_page_title']
    report_title = request.form['report_title']
    string_of_list_of_sprint_runs_to_show_or_compare = request.form['sprint_runs']
    list_of_sprint_runs_to_show_or_compare  = ast.literal_eval(string_of_list_of_sprint_runs_to_show_or_compare)
    database_name = request.form['loadtype']
    collection_name = request.form['loadname']



    obj = perf_load_report_publish(database_name, collection_name, list_of_sprint_runs_to_show_or_compare, parent_page_title, report_title, email_address, api_key, space, url)
    if "new_format" not in obj.all_keys:
        return jsonify({"status": "ERROR", "message": "We are not dealing with new format mongo document"})
    else:
        obj.all_keys.remove('new_format')
        result , status= obj.extract_all_variables()
        print(status, result)
        return jsonify({"status": status, "message": result})

if __name__ == '__main__':
    app.run(debug=True)
