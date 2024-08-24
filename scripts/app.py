from flask import Flask, render_template, request, jsonify
from publish_perf_load_report import perf_load_report_publish
import ast
from pymongo import MongoClient

app = Flask(__name__)


# MongoDB client setup
client = MongoClient('mongodb://localhost:27017/')

@app.route('/get_databases', methods=['GET'])
def get_databases():
    databases = client.list_database_names()
    return jsonify({'databases': databases})

@app.route('/get_collections', methods=['GET'])
def get_collections():
    database_name = request.args.get('database')
    if not database_name:
        return jsonify({'collections': []})
    
    db = client[database_name]
    collections = db.list_collection_names()
    return jsonify({'collections': collections})


@app.route('/get_ids', methods=['GET'])
def get_ids():
    database_name = request.args.get('database')
    collection_name = request.args.get('collection')
    if not database_name or not collection_name:
        return jsonify({'ids': []})
    
    db = client[database_name]
    collection = db[collection_name]
    ids = [str(doc['_id']) for doc in collection.find({}, {'_id': 1})]
    return jsonify({'ids': ids})

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


    # url='https://uptycsjira.atlassian.net'
    # email_address = "masabathularao@uptycs.com"
    # api_key = "ATATT3xFfGF02rG4e5JQzZZ_mVdAkwKKGnjRLYIupWToEGxZm8X-r5dUrAzSAdzGi5FPXMIn_IacnJjOwORsOQV7noObZmkdHqsaHHIzw4pTVyid2Jh3rVmLjM8iw5_hmaK7rFWSMz1JBpQq44vGV1FJs7P-89zijob43kBuxHzfFJJxl5IlM0w=7CE826E3"
    # space = '~71202040c8bf45840d41c598c0efad54382c7b'


    # url='https://raghav-m.atlassian.net'
    # email_address = "pbpraghav@gmail.com"
    # api_key = "ATATT3xFfGF0Tne5mgz28ho5MDsnw1LL_auMF9d0nSufjfGj98I_W2pfpMfbsL1v74wDDPAm5evj46IOmYBQGF8g9UNW8nrsuTur9TuOuKIGnRC2T17j6dFj1hmwOYuHTor9GvtrBNurI92gOBdPwqlgjottdh1Y3WqpfHn2LSrMRd3IDtgrLcc=29FDB196"
    # space = '~712020a6f5183ca4bf41dcae421b10e977a0c1'
    
    # parent_page_title = 'TEST'  
    # import uuid
    # report_title = f"TEST {uuid.uuid4()}"

    # list_of_sprint_runs_to_show_or_compare = [(160,1)]
    # database_name = "Osquery_LoadTests_New"
    # collection_name = "ControlPlane"


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
