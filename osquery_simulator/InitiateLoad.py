import sys
import json
import subprocess
import os
import uuid

base_dir_path =os.path.dirname(os.path.realpath(__file__))

testinput_file_name = os.path.join(base_dir_path,"testinput.json")

try:
   with open(testinput_file_name) as f:
      data = f.read()
except Exception:
    print("could not open file ",testinput_file_name)
    sys.exit(1)

try:
   loadinput= json.loads(data)
   #print loadinput
except Exception:
    print("conent of ",testinput_file_name," is not complying with json format")

instance=loadinput['instances']
print("number of instances",len(instance))
print('-------------------------------')
#print instance
print('-------------------------------')
Fd=open(f'{base_dir_path}/executeload.sh',"w")
Fd.write('#!/bin/bash' + '\n')
instancecmd=[]
for eachinstance in instance:

    replicas = eachinstance.get("replicas_for_this_instance", 1) 
    data_assets = eachinstance.get("data_assets", 0)
    controlplane_assets = eachinstance.get("controlplane_assets", 0)

    while replicas:
        if data_assets>0:
            loadcmd = f"nohup python3 {base_dir_path}/endpointsim.py --domain {eachinstance['domain']} --secret {eachinstance['secret']} --data_assets {data_assets} &> osx_log_data-{str(uuid.uuid4())}.out &"
            instancecmd.append(loadcmd)
            print(loadcmd)
            Fd.write(loadcmd +'\n')
            Fd.write("sleep 10" +'\n')

        if controlplane_assets>0:
            loadcmd = f"nohup python3 {base_dir_path}/endpointsim.py --domain {eachinstance['domain']} --secret {eachinstance['secret']} --controlplane_assets {controlplane_assets} &> osx_log_controlplane-{str(uuid.uuid4())}.out &"
            instancecmd.append(loadcmd)
            print(loadcmd)
            Fd.write(loadcmd +'\n')
            Fd.write("sleep 10" +'\n')
        replicas-=1
        #Fd.write("sleep " + str(loadinput["time_between_instance_seconds"]) +'\n')
Fd.write("sleep 20" +'\n')   
Fd.close()
subprocess.getoutput(f"chmod 777 {base_dir_path}/executeload.sh")
subprocess.getoutput(f"{base_dir_path}/executeload.sh")