import socket
import time
import sys
import datetime
import binascii
import json
import logging
import _thread
import threading
import re
import requests
import zlib
import gzip
import base64
import zmq
import os

global datastats_action
global record_count
global statsflag
global linenumber

record_count=0
datastats_action={}
datastats={}
statsflag=True

port = 5555

logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
base_dir_path =os.path.dirname(os.path.realpath(__file__))

testinput_file_name = os.path.join(base_dir_path,"testinput.json")

def timeinlinux(ts):
  #print 'tsssssssss',ts
  ts_sep=ts.split(" ")
  ts_date=ts_sep[0].split('-')
  ts_time=ts_sep[1].strip('\n').split(':')
  d=datetime.datetime(int(ts_date[0]),int(ts_date[1]),int(ts_date[2]),int(ts_time[0]),int(ts_time[1]),int(ts_time[2]))
  tstamp=time.mktime(d.timetuple())
  return tstamp

def statsdump():
    global linenumber
    global statsflag
    while statsflag:
      time.sleep(100)
      logging.warning(linenumber)
      logging.warning(datastats_action)


def clean_table_name(name):
    #if name.find('pack') == -1:
    return name
    splits = name.split('##')
    return "qp_%s_q_%s" % (splits[2], splits[4])


def analyse(line2):
        global record_count
        #global datastats_action
        pydict=json.loads(line2)
        for key,value in list(pydict.items()):
            if key == "data_chunks":
                for chunk in pydict['data_chunks']:
                    for record in chunk:
                        record_count = record_count + 1
                        c_name = clean_table_name(record['name'])
                        if datastats_action.get(c_name) == None:
                            datastats_action[c_name]={"added":0,"removed":0,"snapshot":0}
                        if record.get('action') == 'added':
                            datastats_action[c_name]['added'] =  datastats_action[c_name]['added'] +1
                        if record.get('action') == 'removed':
                            datastats_action[c_name]['removed'] = datastats_action[c_name]['removed'] + 1
                        if record.get('action') == 'snapshot':
                           datastats_action[c_name]['snapshot'] = datastats_action[c_name]['snapshot'] + 1
                        if record.get('name') == None:
                           print(("Warning ,name is missing in :",record))
                        if datastats.get(c_name) == None:
                            datastats[c_name] = 1
                        else:
                            datastats[c_name]=datastats[c_name]+1
            if key == "data":
                #print("No of records",len(pydict['data']))
                #print( len(pydict['data']))
                for record in pydict['data']:
                    record_count = record_count + 1
                    c_name = clean_table_name(record['name'])
                    if datastats_action.get(c_name) == None:
                        datastats_action[c_name]={"added":0,"removed":0,"snapshot":0}
                    if record.get('action') == 'added':
                            datastats_action[c_name]['added'] =  datastats_action[c_name]['added'] +1
                    if record.get('action') == 'removed':
                            datastats_action[c_name]['removed'] = datastats_action[c_name]['removed'] + 1
                    if record.get('action') == 'snapshot':
                           datastats_action[c_name]['snapshot'] = datastats_action[c_name]['snapshot'] + 1
                    if record.get('name') == None:
                        print(("Warning ,name is missing in :",record))
                    if datastats.get(c_name) == None:
                        datastats[c_name] = 1
                    else:
                        datastats[c_name]=datastats[c_name]+1
def actual_send(msg,port):
      #print(msg) 
      #additional_headers= {'content-encoding': 'gzip'}
      #request_body = zlib.compress(msg)
      #print("after compession lenngth",len(request_body))
      #x = requests.post("http://127.0.0.1:"+str(port), data=request_body, headers=additional_headers)
      #print("printing msg....")
      #print(msg)
      x = requests.post("http://127.0.0.1:"+str(port), data=msg)
      #print(dir(x))
      #print(x.status_code)
      #print(x.url)
 
def bactual_send(msg,port):
      print((dir(msg)))
      print((type(msg)))
      print(msg) 
      additional_headers= {'content-encoding': 'gzip'}
      bytes_com = gzip.zlib.compress(msg.encode("utf-8"))
      request_body = base64.b64encode(bytes_com)
      print((len(request_body)))
      print(request_body)
      x = requests.post("http://127.0.0.1:"+str(port), data=request_body, headers=additional_headers)
      #x = requests.post("http://127.0.0.1:"+str(port), data=msg)
      print((dir(x)))
      print((x.status_code))
      print((x.url))
 
def SendTrigger(sockudp,msg,destip,port,timefornexttrigger):
    inetrvaltime=float(timefornexttrigger) *0.90
    _thread.start_new_thread(actual_send, (msg,port))
    time.sleep(inetrvaltime)


sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

t = threading.Timer(30.0, statsdump)
t.start()  # after 30 seconds, "hello, world" will be printed

UDP_IP = "127.0.0.1"

count=0
# argvcount=sys.argv
# print(argvcount)
# if len(argvcount) != 2:
#    print("Invalid arguments")
#    print("python load_trigger.py testinput.json")
#    sys.exit(1)
# try:
#    with open("argvcount[1]") as f:
#       data = f.read()
# except Exception:
#     print(("could not open file ",argvcount[1]))
#     sys.exit(1)
#    #do something with data
try:
   with open(testinput_file_name) as f:
      data = f.read()
   loadinput= json.loads(data)
   #print loadinput
except Exception:
    print(f"content of {testinput_file_name} is not complying with json format")

instance=loadinput['instances']
endline=loadinput['endline']

linenumber=loadinput['linenumber']

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(f"tcp://127.0.0.1:{port}")  # Bind to a local port

print("Producer started. Waiting 5 seconds for subscribers to connect...")
time.sleep(5)  # Allow time for subscribers to connect

if linenumber == 0:
    #logfd=open('sim.log','w')
    print("play full file")
    firstline=0
    linenumber=0
    TimeCon=loadinput['time']
    Time= TimeCon.split('-')
    if Time[0] == '0000':
      starttime=int(str(time.time()).split('.')[0])
    else:
      year=int(Time[0])
      month=int(Time[1])
      day=int(Time[2])
      hr=int(Time[3])
      minute=int(Time[4])
      d = datetime.datetime(year,month,day,hr,minute)
      starttime = int(time.mktime(d.timetuple()))

    
    diff_ts=0
    with open(os.path.join(base_dir_path,loadinput['inputfile'])) as fs:
      startline=loadinput['startline']
      if startline != 0:
        print('start skipping lines')
        logging.warning("skipping "+str(startline) +" lines")
        for Line in range(0,startline-1):
          linebuffer=fs.readline()
          linenumber=linenumber+1

        if len(linebuffer) < 30:
          linebuffer=fs.readline()
          linenumber=linenumber+1          
      while 1:
        if firstline == 0:
            first_ts=fs.readline()
            first_ts=timeinlinux(first_ts)
            #print 'first_ts',first_ts
            firstline=1
            linenumber=linenumber+1
        Con,second_ts=fs.readline(),fs.readline()
        Con=Con.strip('\n')
        linenumber=linenumber+2
        if len(Con) == 0:
          break
        if len(second_ts) == 0:
          break
        second_ts=timeinlinux(second_ts)
        starttime=starttime+diff_ts
        starttimestr=str(starttime).split('.')[0]
        #Con=re.sub('"unixTime": \d+,','"unixTime": %s,' %starttimestr, Con)
        #print "starttimestr",starttimestr
        con=starttimestr + Con
        #print(con)
        if len(con) > 50065000:
          logging.warning("Line number : " +str(linenumber) + ',length of logger msg : ' + str(len(con)))
          continue
        logging.warning("Line number : " +str(linenumber) + ',tstamp : ' + starttimestr + ' ' + str(len(con)))
        print("Line number : " +str(linenumber) + ',tstamp : ' + starttimestr + ' ' + str(len(con)))
        analyse(Con)
        diff_ts=float(second_ts-first_ts)
        if diff_ts <= 0:
          diff_ts=4.0
        if abs(diff_ts) > 6:
          #print linenumber, "please check date at line ",linenumber, ' in json input'
          #logging.warning("please check date at line "+ str(linenumber)+ ' in json input')
          diff_ts=4.0
        # _thread.start_new_thread(SendTrigger, (sock,con,UDP_IP,port,diff_ts))
        socket.send_json(con)
        time.sleep(diff_ts)
        #time.sleep(3)
        first_ts=second_ts
        if endline != 0:
           if endline <= linenumber:
              break
    statsflag=False      


    
else:
    print("play single log message")
    TimeCon=loadinput['time']
    Time= TimeCon.split('-')
    if Time[0] == '0000':
      unixtime=int(str(time.time()).split('.')[0])
    else:
      year=int(Time[0])
      month=int(Time[1])
      day=int(Time[2])
      hr=int(Time[3])
      minute=int(Time[4])
      d = datetime.datetime(year,month,day,hr,minute)
      unixtime = int(time.mktime(d.timetuple()))
    begtime=int(str(time.time()).split('.')[0])
    with open(loadinput['inputfile']) as f:
      for Line in range(0,int(loadinput['linenumber'])):
          Con = f.readline().strip('\n')
    for no in range(0,int(loadinput['numberoftriggers'])):
     curtime=int(str(time.time()).split('.')[0]) 
     difftime=curtime-begtime
     newtime=unixtime+difftime
     TS=str(newtime).split('.')[0]
     print(TS)
     con=TS + Con
     count=count+1
     print((count,len(con)))
     if len(con) > 65000:
        continue
     if len(con) == 10:
        print(("reading data is done",count))
        break
     if loadinput['delaybetweentrigger'] == '0':
        delay=1
     else:
         delay=int(loadinput['delaybetweentrigger'])
     time.sleep(delay)
     analyse(Con)
     logging.warning("trigger no: " +str(no))
     
    socket.send_json(con)
    statsflag=False

socket.close()
context.term()
print(f"Port {port} is now free.")