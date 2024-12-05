import socket
import time
import sys
import datetime
import os
import json
import logging
import _thread
import threading
import re
import requests
import zlib
import gzip
import base64

global datastats_action
global record_count
global statsflag
global linenumber

record_count=0
datastats_action={}
datastats={}
statsflag=True

logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')

base_dir_path =os.path.dirname(os.path.realpath(__file__))
testinput_file = os.path.join(base_dir_path,"testinput.json")

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
 
def SendTrigger(sockudp,msg,destip,portlist,timefornexttrigger):
    inetrvaltime=float(timefornexttrigger)/float(len(portlist)) *0.90
    for Port in portlist:
      _thread.start_new_thread(actual_send, (msg,Port))
    time.sleep(inetrvaltime)


sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

t = threading.Timer(30.0, statsdump)
t.start()  # after 30 seconds, "hello, world" will be printed

UDP_IP = "127.0.0.1"
UDP_PORT1=41234
UDP_PORT2=42234
UDP_PORT3=43234
UDP_PORT4=44234
UDP_PORT5=45234
UDP_PORT1a=41235
UDP_PORT2a=42235
UDP_PORT3a=43235
UDP_PORT4a=44235
UDP_PORT5a=45235

count=0
try:
   with open(testinput_file) as f:
      data = f.read()
      testinput_contents= json.loads(data)
except Exception as e:
    print(f"Error occured while processing  {testinput_file}",e)
    sys.exit(1)
    
instance=testinput_contents['instances']
endline=testinput_contents['endline']

portlist=[]
for eachinstance in instance:
   portlist.append(eachinstance['port'])
print(portlist)
linenumber=testinput_contents['linenumber']
trafficinstances=testinput_contents['trafficinstances']

if linenumber == 0:
    #logfd=open('sim.log','w')
    print("play full file")
    firstline=0
    linenumber=0
    TimeCon=testinput_contents['time']
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
    with open(testinput_contents['inputfile']) as fs:
      startline=testinput_contents['startline']
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
        analyse(Con)
        diff_ts=float(second_ts-first_ts)
        if diff_ts <= 0:
          diff_ts=4.0
        if abs(diff_ts) > 6:
          #print linenumber, "please check date at line ",linenumber, ' in json input'
          #logging.warning("please check date at line "+ str(linenumber)+ ' in json input')
          diff_ts=4.0
        _thread.start_new_thread(SendTrigger, (sock,con,UDP_IP,portlist[0:trafficinstances],diff_ts))
        time.sleep(diff_ts)
        #time.sleep(3)
        first_ts=second_ts
        if endline != 0:
           if endline <= linenumber:
              break
    statsflag=False      


    
else:
    print("play single log message")
    TimeCon=testinput_contents['time']
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
    with open(testinput_contents['inputfile']) as f:
      for Line in range(0,int(testinput_contents['linenumber'])):
          Con = f.readline().strip('\n')
    for no in range(0,int(testinput_contents['numberoftriggers'])):
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
     if testinput_contents['delaybetweentrigger'] == '0':
        delay=1
     else:
         delay=int(testinput_contents['delaybetweentrigger'])
     time.sleep(delay)
     analyse(Con)
     logging.warning("trigger no: " +str(no))
     for Port in portlist[0:trafficinstances]:
        sock.sendto(con, (UDP_IP, Port))
    statsflag=False
