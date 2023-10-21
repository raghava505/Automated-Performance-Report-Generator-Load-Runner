# from pymongo import MongoClient
# from gridfs import GridFS
from bson import ObjectId
import matplotlib.pyplot as plt
import datetime
import pytz
import seaborn as sns
import os
from matplotlib.dates import date2num, DateFormatter, MinuteLocator
from matplotlib.ticker import FuncFormatter

def convert_to_ist_time(timestamp):
    ist_timezone = pytz.timezone('Asia/Kolkata')
    ist_datetime = datetime.datetime.fromtimestamp(timestamp, tz = ist_timezone)
    return ist_datetime

def format_y_ticks(value,pos):
    if value >= 1e9:
        return f'{value/1e9:.0f}B'
    elif value >= 1e6:
        return f'{value/1e6:.0f}M'
    elif value >= 1e3:
        return f'{value/1e3:.0f}K'
    else:
        return str(value)

def create_images_and_save(path,doc_id,collection,fs):
    sns.set_style("darkgrid")
    # client = MongoClient(conn_string)
    # database = client[database_name]
    # fs = GridFS(database)
    # collection = database[collection_name]
    cursor=collection.find_one({"_id" : ObjectId(doc_id)})
    total_charts=0
    charts_data=cursor["charts"]
    # category_count=1
    for category in charts_data:
        os.makedirs(f"{path}/{category}" , exist_ok=True)
        for title in charts_data[category]:
            print(f"Generating graph for : {title}")
            total_charts+=1
            plt.figure(figsize=(40, 20))
            try:
                for line in  charts_data[category][title]:
                    file_id = line["values"]
                    retrieved_data = fs.get(ObjectId(file_id)).read()
                    large_array = eval(retrieved_data.decode('utf-8'))
                    x = [convert_to_ist_time(point[0]) for point in large_array]
                    x_values_utc = date2num(x)
                    offset_ist_minutes = 330  # 5 hours and 30 minutes offset in minutes
                    x_values_ist = x_values_utc + (offset_ist_minutes / (60 * 24))  # Convert minutes to days
                    y = [float(point[1]) for point in large_array]
                    plt.plot_date(x_values_ist, y, linestyle='solid',label=line["legend"],markersize=1,linewidth=3)
                    
                plt.gca().xaxis.set_major_locator(MinuteLocator(interval=30))
                date_formatter = DateFormatter('%H:%M')
                plt.gca().xaxis.set_major_formatter(date_formatter)
                plt.gca().get_yaxis().set_major_formatter(FuncFormatter(format_y_ticks))
                
                # plt.xlabel('Time →',fontsize=12)
                # plt.ylabel('Value →',fontsize=12)
                plt.title(str(title).title(),fontsize=24,fontweight='bold',pad=20)
                plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.025), ncol=12, fontsize=14,mode='expand')  # Adjust fontsize as needed
                file_name = title.replace("/", "-")
                plt.xticks(fontsize=16,fontweight='bold')
                plt.yticks(fontsize=16,fontweight='bold')
                plt.tight_layout()

                if min(x).minute >30:start_min_to_replace=30
                else:start_min_to_replace = 0
                start_time_in_charts = date2num(min(x).replace(minute=start_min_to_replace))+(offset_ist_minutes / (60 * 24))

                if max(x).minute < 30:
                    end_hr_to_replace=max(x).hour
                    end_min_to_replace=30
                else:
                    end_hr_to_replace = max(x).hour+1
                    end_min_to_replace = 0
                end_time_in_charts = date2num(max(x).replace(minute=end_min_to_replace,hour=end_hr_to_replace))+(offset_ist_minutes / (60 * 24))
                plt.xlim((start_time_in_charts,end_time_in_charts))
                
                plt.savefig(f"{path}/{category}/{file_name}.png", bbox_inches='tight', pad_inches=0.1)
            except Exception as e:
                print(f"Error while generating graph for {title} : {str(e)}")
            finally:
                plt.close()
        # category_count+=1

    print("Total number of charts generated : " , total_charts)

import time,pymongo
from gridfs import GridFS

s_at = time.perf_counter()
path = "/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/other/images"
client = pymongo.MongoClient("mongodb://localhost:27017")
database = client["Osquery_LoadTests"]
fs = GridFS(database)
collection = database["MultiCustomer"]
create_images_and_save(path,"6530ce2a6c4124a8bbfe6aa1",collection,fs)
f3_at = time.perf_counter()
print(f"Collecting the report data took : {round(f3_at - s_at,2)} seconds in total")