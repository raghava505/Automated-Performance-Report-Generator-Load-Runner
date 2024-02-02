import logging
from .api_func import *
from datetime import datetime
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

LOG_PATH = str(PROJECT_ROOT) + "/logs"


api_path = str(PROJECT_ROOT)  + '/API_keys/api_key_{}.json'.format(domain)
stack_keys = open_js_safely(api_path)
modified_api= build_api.format(stack_keys['domain'], stack_keys['domainSuffix'])

output= get_api(api_path,modified_api)
build = output['number']
# print()
log = logging.getLogger()
default_level = logging.INFO
log.setLevel(default_level)
log_format = logging.Formatter("%(asctime)s.%(msecs)03d] %(levelname)s %(module)s - %(funcName)s: %(message)s",
                               datefmt="%Y-%m-%d %H:%M:%S")
if not log.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_format)
    log.addHandler(handler)

test_start_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
log_path = os.path.join(LOG_PATH)
if not os.path.exists(log_path):
    os.system("mkdir " + log_path)
log_file = os.path.join(log_path, build + "_"+ test_start_time + ".log")
# log_file = os.path.join(test_start_time + ".log")
fh = logging.FileHandler(log_file)
fh.setFormatter(log_format)
fh.setLevel(default_level)
log.handlers = []
log.addHandler(fh)