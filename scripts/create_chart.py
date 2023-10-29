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
import numpy as np

def convert_to_ist_time(timestamp):
    ist_timezone = pytz.timezone('Asia/Kolkata')
    ist_datetime = datetime.datetime.fromtimestamp(timestamp, tz = ist_timezone)
    return ist_datetime

def format_y_ticks(value,pos):
    if value >= 1e9:
        return f'{value/1e9:.2f} B'
    elif value >= 1e6:
        return f'{value/1e6:.2f} M'
    elif value >= 1e3:
        return f'{value/1e3:.2f} K'
    else:
        return str(int(value))

# outer_background_color="#111217"
outer_background_color="#191b1f"
text_color="#ccccdc"
inner_background_color = "#191b1f"
gridline_color = "#404144"
gridline_width = 0.01

fig_width=34
# character_width = 28
# initial_legend_fontsize=17
# fontsize_decrease_rate_with_rows=0.165
# ncol_increase_rate_with_rows=0.28

character_width = 13.5                      #inversly prop to initial ncol
initial_legend_fontsize=fig_width/1.90
fontsize_decrease_rate_with_rows=fig_width/185
ncol_increase_rate_with_rows=fig_width/0.00425

def create_images_and_save(path,doc_id,collection,fs):
    sns.set_style("darkgrid")
    sns.plotting_context("talk")
    sns.set(rc={"text.color": text_color})
    sns.set_style({"axes.facecolor": inner_background_color})
    sns.set_style({"grid.color": gridline_color})
    sns.set_style({"grid.linewidth": gridline_width})
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
            plt.figure(figsize=(fig_width, fig_width*8/16))
            try:
                num_lines=0
                list_of_legend_lengths=[]
                for line in  charts_data[category][title]:
                    file_id = line["values"]
                    retrieved_data = fs.get(ObjectId(file_id)).read()
                    large_array = eval(retrieved_data.decode('utf-8'))
                    x = [convert_to_ist_time(point[0]) for point in large_array]
                    x_values_utc = date2num(x)
                    offset_ist_minutes = 330  # 5 hours and 30 minutes offset in minutes
                    x_values_ist = x_values_utc + (offset_ist_minutes / (60 * 24))  # Convert minutes to days
                    y = [float(point[1]) for point in large_array]
                    plt.plot_date(x_values_ist, y, linestyle='solid',label=line["legend"],markersize=0.1,linewidth=fig_width/21)
                    list_of_legend_lengths.append(len(str(line["legend"])))
                    num_lines+=1
                plt.gca().xaxis.set_major_locator(MinuteLocator(interval=30))
                date_formatter = DateFormatter('%H:%M')
                plt.gca().xaxis.set_major_formatter(date_formatter)
                plt.gca().get_yaxis().set_major_formatter(FuncFormatter(format_y_ticks))
                plt.title("\n"+str(title),fontsize=fig_width/1.68,fontweight='bold',pad=fig_width/0.9,y=1)
                if num_lines == 0:
                    print(f"ERROR : Unable to find data for chart {title} : 0 lines found" )
                    continue
                if sum(list_of_legend_lengths) == 0:
                    print(f"WARNING : No legend text found for the chart {title} , sum_legends_length is 0")
                else:
                    std=np.std(list_of_legend_lengths)
                    mean=np.mean(list_of_legend_lengths)
                    average_legend_length = mean+1*std
                    available_width_points = (fig_width * plt.rcParams['figure.dpi'])/character_width
                    ncol=(available_width_points/(average_legend_length+6))
                    rows=(num_lines/ncol)+1
                    fontsize = initial_legend_fontsize - (fontsize_decrease_rate_with_rows * (rows-1))
                    final_ncol = ncol + ((ncol_increase_rate_with_rows/((average_legend_length**2.09) * (fontsize**2.21))) * (rows-1))
                    leg=plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.030), ncol=final_ncol, fontsize=fontsize,handlelength=1,frameon=False)
                    for legobj in leg.legendHandles:
                        legobj.set_linewidth(fig_width/6) 
                file_name = title.replace("/", "-")
                plt.xticks(fontsize=fig_width/1.935,color=text_color,fontweight='bold')
                plt.yticks(fontsize=fig_width/1.935,color=text_color,fontweight='bold')
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
                ax = plt.gca()
                for spine in ax.spines.values():
                    spine.set_color(gridline_color)
                plt.gca().spines['right'].set_visible(False)
                plt.gca().spines['left'].set_visible(False)
                plt.gca().spines['top'].set_visible(False)                
                plt.gcf().set_facecolor(outer_background_color)
                plt.savefig(f"{path}/{category}/{file_name}.png", bbox_inches='tight', pad_inches=0.1,format='webp')
            except Exception as e:
                print(f"Error while generating graph for {title} : {str(e)}")
            finally:
                plt.close()
        # category_count+=1

    print("Total number of charts generated : " , total_charts)

# import time,pymongo
# from gridfs import GridFS

# s_at = time.perf_counter()
# path = "/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/other/images"
# client = pymongo.MongoClient("mongodb://localhost:27017")
# database = client["Osquery_LoadTests"]
# fs = GridFS(database)
# collection = database["MultiCustomer"]
# create_images_and_save(path,"653b84666c1d0c76e5ef921c",collection,fs)
# f3_at = time.perf_counter()
# print(f"Collecting the report data took : {round(f3_at - s_at,2)} seconds in total")