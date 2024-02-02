
import json
import datetime
import time
import jwt
import requests
import urllib3
from .configs import *
from subprocess import Popen, PIPE


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RunCommand:

    def __init__(self, command:str):
        self.command = command

    def get_basic_command(self):
        stdout, stderr, return_code = self.get_output()
        return stdout

    def get_output(self):
        command_stdout=''
        command_stderr='' 
        command_return_code=''
        try:
            proc = Popen(self.command, shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            command_stdout, command_stderr = proc.communicate(timeout=300)
            command_return_code = proc.returncode
        except:
            proc.kill()
            command_stdout, command_stderr = proc.communicate()
            command_return_code = 1
        finally:
            return command_stdout, command_stderr, command_return_code
        
# def command_on_node(cmd):
#     obj=RunCommand(command=cmd)
#     result = obj.get_basic_command()
#     return result
def command_on_node(cmd):
    obj = RunCommand(command=cmd)
    result, _, return_code = obj.get_output()
    return result, return_code


def retry(num_times: int = 5, sleep_between_error_seconds: int = 60):
    """If an error happens while calling function, sleep for
    sleep_between_error_seconds and try again"""

    def fxn_accepter(fxn):
        def arg_accepter(*args, **kwargs):
            exceptions = []
            cur = 1
            while cur <= num_times:
                try:
                    return fxn(*args, **kwargs)
                except Exception as e:
                    exceptions.append(e)
                    print("retry encountered error on fxn %s. Sleeping for %s seconds and retrying..." % (
                        fxn.__name__, sleep_between_error_seconds))
                    cur += 1
                    time.sleep(sleep_between_error_seconds)
            print("Could not execute %s" % fxn.__name__)
            print("List of %s problems: %s" % (num_times, exceptions))
            raise Exception("Could not execute %s" % fxn.__name__)

        return arg_accepter

    return fxn_accepter

def open_js_safely(file: str) -> dict:
    """Open a json file without leaving a dangling file descriptor"""
    with open(file, "r") as fin:
        content = fin.read()
    return json.loads(content)

def generateHeaders(key: str, secret: str) -> dict:
    header = {}
    utcnow = datetime.datetime.utcnow()
    date = utcnow.strftime("%a, %d %b %Y %H:%M:%S GMT")
    exp_time = time.time() + 3600
    try:
        authVar = jwt.encode({'iss':key, 'exp': exp_time},secret).decode("utf-8")
    except:
        authVar = jwt.encode({'iss':key, 'exp': exp_time},secret)
    authorization = "Bearer %s" % (authVar)
    header['date'] = date
    header['authorization'] = authorization
    header['Content-type'] = "application/json"
    return header

def general_api(apiconfig: str) -> dict:
    data = open_js_safely(apiconfig)
    headers = generateHeaders(data['key'], data['secret'])
    url = "https://%s.uptycs.io/public/api/version" % (data['domain'])
    resp = requests.get(url, headers=headers, verify=False, timeout=120)
    return resp.json()

@retry(num_times=5, sleep_between_error_seconds=10)
def get_api(apiconfig, url) -> dict:
    data = open_js_safely(apiconfig)
    headers = generateHeaders(data['key'], data['secret'])
    i=0
    resp = requests.get(url, headers=headers, verify=False, timeout=120)
    if resp.status_code == 200:
        return resp.json()
    else:
        while (i < 20) and (resp.status_code != 200):
            time.sleep(0.1)
            resp = requests.get(url, headers=headers, verify=False, timeout=120)
            i = i + 1
        if resp.status_code == 200:
            return resp.json()
        if i == 10 and (resp.status_code != 200):
            raise Exception("Could not get the response for GET api request %s" % (url))
         
@retry(num_times=5, sleep_between_error_seconds=10)
def prometheus_api(metric) -> dict:
    # command = ' curl http://localhost:9090/api/v1/query?query=%s '%(metric)
    try:
        command_metric= 'curl http://localhost:9090/api/v1/query?query=%s'%(metric)
        command = f"ssh {monitor_node_name} ' {command_metric} ; exit'"
        temp= command_on_node(command)
        op = json.loads(temp)
        return op
    except Exception as e:
        return str(e)
    # url = "http://%s:9090/api/v1/query?query=%s"%(monitor_node_name, metric)
    # try:
    #     resp = requests.get(url, verify=False, timeout=120)
    #     if resp.status_code == 200:
    #         return resp.json()
    # except Exception as e:
    #     return str(e)

def build_go_request(command: str, user: str = USER, path: str = HOME_PATH) -> dict:
    """Assuming reasonable defaults, construct payload for the go API"""
    return {"user": user, "path": path, "comd": command}


def issue_go_request(req_dict: dict, hostname: str, port: int = GO_API_PORT, timeout=None) -> dict:
    
    url = "http://%s:%s/issue" % (hostname, port) 
    try:
        resp = requests.post(url, json=req_dict, timeout=timeout)
        return resp.json()
    except Exception as e:
        return str(e)

def execute_command_on_node(node_name, cmd):

    req_json = build_go_request(cmd, USER, HOME_PATH)
    req_out = issue_go_request(req_json, node_name, GO_API_PORT)
    return req_out
    


@retry(num_times=5, sleep_between_error_seconds=10)
def post_api(apiconfig: str, url: str, raw_data) -> dict:
    i=0
    data = open_js_safely(apiconfig)
    headers = generateHeaders(data['key'], data['secret'])
    json_payload = json.dumps(raw_data)
    resp = requests.post(url, data=json_payload, headers=headers, verify=False, timeout=120)
    # print (resp)
    # print(resp.status_code)
    if resp.status_code == 200:
        return resp.json()
    else:
        while (i < 20) and (resp.status_code != 200):
            time.sleep(0.1)
            resp = requests.post(url, data=json_payload, headers=headers, verify=False, timeout=120)
            i = i + 1
        if resp.status_code == 200:
            return resp.json()
        if i == 20 and (resp.status_code != 200):
            raise Exception("Could not get the response for POST api request %s" % (url))

def general_api(apiconfig: str) -> dict:
    data = open_js_safely(apiconfig)
    headers = generateHeaders(data['key'], data['secret'])
    url = "https://{}{}/public/api/version".format(data['domain'], data['domainSuffix'])
    resp = requests.get(url, headers=headers, verify=False, timeout=120)
    return resp.json()








