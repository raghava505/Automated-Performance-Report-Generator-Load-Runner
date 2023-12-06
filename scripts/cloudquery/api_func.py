import json
import datetime
import time
import jwt
import requests
import urllib3
from .configs import *
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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
    #data = open_js_safely(apiconfig)
    data=apiconfig
    headers = generateHeaders(data['key'], data['secret'])
    url = "https://%s.uptycs.io/public/api/version" % (data['domain'])
    resp = requests.get(url, headers=headers, verify=False, timeout=300)
    return resp.json()

@retry(num_times=5, sleep_between_error_seconds=10)
def get_api(apiconfig, url) -> dict:
    #data = open_js_safely(apiconfig)
    data=apiconfig
    headers = generateHeaders(data['key'], data['secret'])
    i=0
    resp = requests.get(url, headers=headers, verify=False, timeout=300)
    if resp.status_code == 200:
        return resp.json()
    else:
        while (i < 20) and (resp.status_code != 200):
            time.sleep(0.1)
            resp = requests.get(url, headers=headers, verify=False, timeout=300)
            i = i + 1
        if resp.status_code == 200:
            return resp.json()
        if i == 10 and (resp.status_code != 200):
            raise Exception("Could not get the response for GET api request %s" % (url))
         
@retry(num_times=5, sleep_between_error_seconds=10)




@retry(num_times=5, sleep_between_error_seconds=10)
def post_api(apiconfig: str, url: str, raw_data) -> dict:
    i=0
    #data = open_js_safely(apiconfig)
    data=apiconfig
    headers = generateHeaders(data['key'], data['secret'])
    json_payload = json.dumps(raw_data)
    resp = requests.post(url, data=json_payload, headers=headers, verify=False, timeout=300)
    if resp.status_code == 200:
        return resp.json()
    else:
        while (i < 20) and (resp.status_code != 200):
            time.sleep(0.1)
            resp = requests.post(url, data=json_payload, headers=headers, verify=False, timeout=300)
            i = i + 1
        if resp.status_code == 200:
            return resp.json()
        if i == 20 and (resp.status_code != 200):
            raise Exception("Could not get the response for POST api request %s" % (url))

def general_api(apiconfig: str) -> dict:
    data = open_js_safely(apiconfig)
    headers = generateHeaders(data['key'], data['secret'])
    url = "https://{}{}/public/api/version".format(data['domain'], data['domainSuffix'])
    resp = requests.get(url, headers=headers, verify=False, timeout=300)
    return resp.json()