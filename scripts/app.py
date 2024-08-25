from flask import Flask, render_template, request, jsonify
from publish_perf_load_report import perf_load_report_publish
import ast
from pymongo import MongoClient
from config_vars import MONGO_CONNECTION_STRING

app = Flask(__name__)


# MongoDB client setup
client = MongoClient(MONGO_CONNECTION_STRING)

@app.route('/get_databases', methods=['GET'])
def get_databases():
    databases = client.list_database_names()
    databases=[item for item in databases if "_LoadTests_New" in item]
    return jsonify({'databases': databases})

@app.route('/get_collections', methods=['GET'])
def get_collections():
    database_name = request.args.get('database')
    if not database_name:
        return jsonify({'collections': []})
    
    db = client[database_name]
    collections = db.list_collection_names()
    collections=[item for item in collections if "fs" not in item]

    return jsonify({'collections': collections})


@app.route('/get_ids', methods=['GET'])
def get_ids():
    database_name = request.args.get('database')
    collection_name = request.args.get('collection')
    if not database_name or not collection_name:
        return jsonify({'ids': []})
    
    db = client[database_name]
    collection = db[collection_name]    
    # dictionary = {
    #     '160': [{'run':'1', 'build':160012}, {'run':'2', 'build':160013}, {'run':'5', 'build':160014}],
    #     '161': [{'run':'2', 'build':160022}, {'run':'3', 'build':160023}, {'run':'6', 'build':160024}],
    #     '162': [{'run':'3', 'build':160032}, {'run':'4', 'build':160033}, {'run':'7', 'build':160034}],
    # }
    dictionary= {}
    ids = [(str(doc['load_details']["data"]["sprint"]),str(doc['load_details']["data"]["run"]),str(doc['load_details']["data"]["build"]),str(doc['load_details']["data"]["stack"]),str(doc['load_details']["data"]["load_duration_in_hrs"])) for doc in collection.find({}, {'load_details.data.sprint': 1,'load_details.data.run': 1,'load_details.data.build': 1,'load_details.data.stack': 1,'load_details.data.load_duration_in_hrs': 1})]
    for sprint,run,build, stack, load_dur in ids:
        item = {'run':run,'build':build, 'stack':stack,'load_duration':load_dur}
        if sprint in dictionary:
            dictionary[sprint].append(item)
        else:
            dictionary[sprint] = [item]

    return jsonify({"dictionary":dictionary, "sprints":list(dictionary)})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    # Get form data from the request
    print("RETURNED FORM INPUT : ")
    print(request.form)
    url = request.form['url']
    email_address = request.form['email_address']
    api_key = request.form['api_key']
    space = request.form['space']
    parent_page_title = request.form['parent_page_title']
    report_title = request.form['report_title']
    string_of_list_of_sprint_runs_to_show_or_compare = request.form['sprint_runs']
    list_of_sprint_runs_to_show_or_compare  = ast.literal_eval(string_of_list_of_sprint_runs_to_show_or_compare)
    print(list_of_sprint_runs_to_show_or_compare)
    database_name = request.form['loadtype']
    collection_name = request.form['loadname']

    # url='https://uptycsjira.atlassian.net'
    # email_address = "masabathularao@uptycs.com"
    # space = '~71202040c8bf45840d41c598c0efad54382c7b'


    # url='https://raghav-m.atlassian.net'
    # email_address = "pbpraghav@gmail.com"
    # space = '~712020a6f5183ca4bf41dcae421b10e977a0c1'
    
    # parent_page_title = 'TEST'  
    # import uuid
    # report_title = f"TEST {uuid.uuid4()}"

    # list_of_sprint_runs_to_show_or_compare = [[160,5]]
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
    app.run(host='0.0.0.0', port=5000,debug=False)
