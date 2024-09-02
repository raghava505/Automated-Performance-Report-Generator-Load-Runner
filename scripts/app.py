from flask import Flask, render_template, request, jsonify, Response, send_from_directory, url_for, flash, session
from publish_perf_load_report import perf_load_report_publish
import ast
from pymongo import MongoClient
from config_vars import MONGO_CONNECTION_STRING, REPORT_UI_PORT, BASE_GRAPHS_PATH
import time
from queue import Queue
from flask_session import Session 
import json
import pandas as pd

app = Flask(__name__)
# app.config['SECRET_KEY'] = '343c855017e725321cb7f35b89c98b9e'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

report_data_user_queues = {}
publish_logs_user_queues = {}


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


@app.route('/test', methods=['GET'])
def something_test():
    return render_template('test2.html', collections=[x for x in range(5)], database_name="test_database")


@app.route('/graphs/<path:filename>')
def serve_image(filename):
    return send_from_directory(BASE_GRAPHS_PATH, filename)


@app.route('/publish_logs_stream')
def get_publish_logs_stream():
    def logs_generate(user_id):
        """Stream logs from the user's queue."""
        user_queue = publish_logs_user_queues.get(user_id, None)
        print("inside generate func : ", user_queue)
        while True:
            if not user_queue.empty():
                msg = user_queue.get()
                print("POPPING FROM QUEUE")
                yield msg
                # yield f'data: {{"status": "success", "message": "user id is {user_id}"}}\n\n'
                time.sleep(0.1)
            else:
                time.sleep(1)

    """Stream logs for the current user."""
    user_id = session.get('user_id')
    if user_id:
        print(user_id," found in session")
        return Response(logs_generate(user_id), content_type='text/event-stream')
    else:
        print("user id not found in session")
    return '', 403  # Forbidden if no user ID

@app.route('/report_data_queue_route')
def get_report_data_stream():
    def report_generate(user_id):
        """Stream logs from the user's queue."""
        user_queue = report_data_user_queues.get(user_id, None)
        print("inside generate func : ", user_queue)
        while True:
            if not user_queue.empty():
                msg = user_queue.get()
                print("POPPING FROM QUEUE")
                yield msg
                # yield f'data: {{"status": "success", "message": "user id is {user_id}"}}\n\n'
                time.sleep(0.1)
            else:
                time.sleep(1)
    """Stream logs for the current user."""
    user_id = session.get('user_id')
    if user_id:
        print(user_id," found in session")
        return Response(report_generate(user_id), content_type='text/event-stream')
    else:
        print("user id not found in session")

    return '', 403  # Forbidden if no user ID

@app.route('/test2')
def stream_data():
    def generate():
        for i in range(1, 7):  # 1 minute = 6 iterations (every 10 seconds)
            collections = [x for x in range(5)]
            data = f"Data batch {i}: {collections}"
            yield f"data:{data}\n\n"
            time.sleep(2)  # Wait for 10 seconds before sending the next batch
    return Response(generate(), content_type='text/event-stream')


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

    return jsonify({"dictionary":dictionary, "sprints":list(reversed(list(dictionary)))})

@app.route('/')
def index():
    """Render the main HTML page."""
    session['user_id'] = request.cookies.get('user_id', None)  # Get or set a unique user ID
    if not session['user_id']:
        session['user_id'] = str(time.time())  # Use timestamp or UUID for unique user ID

    user_id = session.get('user_id')
    report_data_user_queues[user_id] = Queue()
    publish_logs_user_queues[user_id] = Queue()

    return render_template('index.html',user_id=user_id)

@app.route('/submit_table', methods=['POST'])
def submit_table():
    # Extract form data and rebuild the dataframe
    form_data = request.form
    data_dict = {}
    key_name = None
    # Iterate over the ImmutableMultiDict items
    for key, value in form_data.items(multi=True):
        print(key, value)
        database_name = key.split('___')[0]
        collection_name = key.split('___')[1]
        sprint = int(key.split('___')[2])
        run = int(key.split('___')[3])
        key_name = key.split('___')[4]
        col_name = key.split('___')[5]  # Extract column name after '___'
        print(database_name)
        print(collection_name)
        print(sprint)
        print(run)
        print(key_name)
        print(col_name)
        # Append the value to the appropriate list in the dictionary
        if col_name not in data_dict:
            data_dict[col_name] = []
        data_dict[col_name].append(value)

    df = pd.DataFrame(data_dict)
    print(df)
    data_to_save = df.to_dict(orient="records")
    
    db = client[database_name]
    collection = db[collection_name]    
    result = collection.update_one(
        {"load_details.data.sprint": sprint , "load_details.data.run":run},  # Filter to find the document
        {"$set": {f"{key_name}.data":data_to_save}}  # Update nested fields within "data"
    )
    # Extract useful information
    matched_count = result.matched_count  # Number of documents that matched the filter
    modified_count = result.modified_count  # Number of documents that were modified
    acknowledged = result.acknowledged  # Whether the update was acknowledged
    upserted_id = result.upserted_id  # The _id of the document if an upsert occurred (can be None)

    # Construct a meaningful result string
    if not acknowledged:
        result_string = "Update operation was not acknowledged by the server."
        status = "error"
    elif matched_count == 0:
        result_string = "No documents matched the filter criteria. No update performed."
        status="error"
    elif modified_count == 0:
        # result_string = "Document matched the filter criteria, but no changes were made."
        result_string = "No changes detected. Please modify the table before saving."
        status="warning"
    else:
        result_string = f"Update successful! '{key_name}' table modified."
        status="success"

    # Check for upsert
    if upserted_id:
        result_string += f" A new document was created with _id: {upserted_id}."
    
    return jsonify({"status": status, "message": result_string})

@app.route('/view_report',methods=['POST','GET'])
def view_report():
    string_of_list_of_sprint_runs_to_show_or_compare = request.form['sprint_runs']
    list_of_sprint_runs_to_show_or_compare  = ast.literal_eval(string_of_list_of_sprint_runs_to_show_or_compare)
    print(list_of_sprint_runs_to_show_or_compare)
    database_name = request.form['loadtype']
    collection_name = request.form['loadname']

    # list_of_sprint_runs_to_show_or_compare = [[158,1], [157,1]]
    # database_name = "Osquery_LoadTests_New"
    # collection_name = "MultiCustomer"

    """Add a log message to the queue for the current user."""
    user_id = session.get('user_id')
    if not user_id:
        # return '', 403 
        return  jsonify({
                        "status": "error",
                        "message": "403 : User not found. Please refresh the page and try again"
                    })
    try:
        obj = perf_load_report_publish(database_name, collection_name, list_of_sprint_runs_to_show_or_compare, None, None, None, None, None, None,isViewReport=True)
        if "new_format" in obj.all_keys:obj.all_keys.remove('new_format')
    except Exception as e:
        error_message = f"Error occurred during object initialization at view-report : {str(e)}"
        message_dict = {"status": "error", "message": error_message}

        if user_id in report_data_user_queues:
            json_data = json.dumps(message_dict)
            msg =  f'data: {json_data}\n\n'
            report_data_user_queues[user_id].put(msg)
        print("returning json data on error : " , message_dict)
        return jsonify(message_dict)

    for msg in obj.extract_all_variables_and_publish(url_for):
        if user_id in report_data_user_queues:
            report_data_user_queues[user_id].put(msg)
        else:
            print("FATAL ERROR : userid not found in user queues")
            return jsonify({"status": "error", "message": "FATAL : user_id not found in report_data_user_queues. Please refresh the page and try again"})
    return jsonify({"status": "info", "message": "succesfully processed request for 'view-report' "})
    
    

@app.route('/publish_report',methods=['POST'])
def publish_report():
    # Get form data from the request
    # print("RETURNED FORM INPUT : ")
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

    # url='https://raghav-m.atlassian.net'
    # email_address = "pbpraghav@gmail.com"
    # space = 'IT'
    # parent_page_title = 'TEST'  
    # import uuid
    # report_title = f"TEST {uuid.uuid4()}"

    # list_of_sprint_runs_to_show_or_compare = [[160,4],[160,1]]
    # database_name = "Osquery_LoadTests_New"
    # collection_name = "ControlPlane"

    user_id = session.get('user_id')
    if not user_id:
        # return '', 403 
        return  jsonify({
                        "status": "error",
                        "message": "403 : User not found. Please refresh the page and try again"
                    })

    try:
        obj = perf_load_report_publish(database_name, collection_name, list_of_sprint_runs_to_show_or_compare, parent_page_title, report_title, email_address, api_key, space, url,isViewReport=False)
        if "new_format" in obj.all_keys:obj.all_keys.remove('new_format')
    except Exception as e:
        error_message = f"Error occurred during object initialization at publish-report: {str(e)}"
        message_dict = {"status": "error", "message": error_message}

        if user_id in publish_logs_user_queues:
            json_data = json.dumps(message_dict)
            msg =  f'data: {json_data}\n\n'
            publish_logs_user_queues[user_id].put(msg)
        print("returning json data on error : " , message_dict)
        return jsonify(message_dict)
    

    for msg in obj.extract_all_variables_and_publish(url_for):
        if user_id in publish_logs_user_queues:
            publish_logs_user_queues[user_id].put(msg)
        else:
            print("FATAL ERROR : userid not found in user queues")
            return jsonify({"status": "error", "message": "FATAL : user_id not found in publish_logs_user_queues. Please refresh the page and try again"})
    return jsonify({"status": "info", "message": "succesfully processed request for 'pubslih-report' "})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=REPORT_UI_PORT,debug=True)
