from bson import ObjectId
import matplotlib.pyplot as plt
import pytz
import seaborn as sns
import os
from matplotlib.dates import date2num, DateFormatter, MinuteLocator
from matplotlib.ticker import FuncFormatter
import numpy as np
# import pandas as pd

area_fill_titles=["No.of active connections group by application for configdb on master"]

def convert_to_ist_time(timestamp):
    import datetime
    ist_timezone = pytz.timezone('Asia/Kolkata')
    ist_datetime = datetime.datetime.fromtimestamp(timestamp, tz = ist_timezone)
    return ist_datetime

def format_y_ticks(value,pos,unit):
    if value >= 1e9:
        return f'{value/1e9:.2f} B {unit}'
    elif value >= 1e6:
        return f'{value/1e6:.2f} M {unit}'
    elif value >= 1e3:
        return f'{value/1e3:.2f} K {unit}'
    else:
        return f"{float(value):.2f} {unit}"

def eliminate_long_breaks(old_x,old_y,step_factor):
    x=[]
    y=[]
    prev_point=None
    for point in zip(old_x,old_y):
        if prev_point and (point[0]-prev_point)> (0.00069445)*step_factor :
            x.append(None)
            y.append(None)
        x.append(point[0])
        y.append(point[1])
        prev_point=point[0]
    return x,y

def eliminate_long_breaks_for_area_plot(old_x,old_y,step_factor):
    x=[]
    y=[]
    prev_point=None
    for point in zip(old_x,old_y):
        if prev_point and (point[0]-prev_point)> (0.00069445)*step_factor :
            x.append(prev_point+0.00000001)
            y.append(0)
            x.append(point[0]-0.00000001)
            y.append(0)
        x.append(point[0])
        y.append(point[1])
        prev_point=point[0]
    return x,y

offset_ist_minutes = 330  # 5 hours and 30 minutes offset in minutes

outer_background_color="#191b1f"
# text_color="#ccccdc"
text_color="#EAEAEA"
inner_background_color = "#191b1f"
gridline_color = "#404144"
gridline_width = 0.01

fig_width=22
character_width = 12.0                     #inversly prop to initial ncol
initial_legend_fontsize=fig_width/1.90
fontsize_decrease_rate_with_rows=fig_width/165
ncol_increase_rate_with_rows=8000

def create_images_and_save(path,doc_id,collection,fs,variables,end_time_str,run,stack,test_title,step_factor,stack_obj):
    duration = variables['load_duration_in_hrs']
    stack_obj.log.info(f"Delete saved images data set to : {delete_image_data}")
    sns.set_style("darkgrid")
    sns.plotting_context("talk")
    sns.set(rc={"text.color": text_color})
    sns.set_style({"axes.facecolor": inner_background_color})
    sns.set_style({"grid.color": gridline_color})
    sns.set_style({"grid.linewidth": gridline_width})
    cursor=collection.find_one({"_id" : ObjectId(doc_id)})
    total_charts=0
    charts_data=cursor["charts"]["data"]
    complete_time_set=set()
    for category in charts_data:
        os.makedirs(f"{path}/{category}" , exist_ok=True)
        for title in charts_data[category]:
            stack_obj.log.info(f"Generating graph for : {title}")
            total_charts+=1
            plt.figure(figsize=(fig_width, fig_width*8/16))
            try:
                num_lines=0
                list_of_legend_lengths=[]
                unit=""
                for line in  charts_data[category][title]:
                    file_id = line["values"]
                    retrieved_data = fs.get(ObjectId(file_id)).read()
                    if delete_image_data:
                        fs.delete(file_id)
                    large_array = eval(retrieved_data.decode('utf-8'))
                    x = [convert_to_ist_time(point[0]) for point in large_array]
                    complete_time_set.add(min(x))
                    complete_time_set.add(max(x))
                    x_values_utc = date2num(x)
                    x_values_ist = x_values_utc + (offset_ist_minutes / (60 * 24))  # Convert minutes to days
                    y = [float(point[1]) for point in large_array]
                    # y = pd.Series(y).rolling(window=5).mean()
                    if title in area_fill_titles or 'Lag' in category or 'Lag' in title:
                        x_values_ist,y=eliminate_long_breaks_for_area_plot(x_values_ist,y,step_factor)
                    else:
                        x_values_ist,y=eliminate_long_breaks(x_values_ist,y,step_factor)
                    line_plot, = plt.plot_date(x_values_ist, y, linestyle='solid', label=line["legend"], markersize=0.1, linewidth=fig_width/21)
                    list_of_legend_lengths.append(len(str(line["legend"])))
                    num_lines+=1
                    # plt.text(x_values_ist[0],y[0],line['legend'])
                    # Get the line color
                    line_color = line_plot.get_color()
                    if title in area_fill_titles or 'Lag' in category or 'Lag' in title:
                        plt.fill_between(x_values_ist, y, color=line_color, alpha=0.1)
                    plt.text(x_values_ist[0],y[0],line['legend'], fontsize=10, verticalalignment='bottom', horizontalalignment='left', color='black', rotation=0, bbox=dict(facecolor=line_color, edgecolor='none', boxstyle='round,pad=0.1'))
                    plt.text(x_values_ist[-1],y[-1],line['legend'], fontsize=10, verticalalignment='bottom', horizontalalignment='right', color='black', rotation=0, bbox=dict(facecolor=line_color, edgecolor='none', boxstyle='round,pad=0.1'))
                    unit = line['unit']

                base_x_interval_min = 30
                factor = (duration//18) + 1
                x_time_interval_in_min = int(base_x_interval_min * factor)
                
                # if duration > 24:
                x_date_formatter = DateFormatter('%m/%d \n%H:%M')
                # else:
                    # x_date_formatter = DateFormatter('%H:%M')

                plt.gca().xaxis.set_major_locator(MinuteLocator(interval=x_time_interval_in_min))
                # date_formatter = DateFormatter('%H:%M')
                plt.gca().xaxis.set_major_formatter(x_date_formatter)
                plt.gca().get_yaxis().set_major_formatter(FuncFormatter(lambda value,pos:format_y_ticks(value,pos,unit)))
                other_details=f"{test_title}\nLoad time : {variables['start_time_str_ist']} - {end_time_str} IST ({variables['load_duration_in_hrs']} hrs)"
                plt.title(other_details,fontsize=fig_width/2.18,y=1,loc="left")
                plt.title(f"Build and run : {variables['build']} , run{run}\nStack : {stack}",fontsize=fig_width/2.18,y=1,loc="right")
                plt.title("\n"+str(title),fontsize=fig_width/1.48,pad=fig_width/0.9,y=1)
                if num_lines == 0:
                    stack_obj.log.error(f"Unable to find data for chart {title} : 0 lines found" )
                    continue
                if sum(list_of_legend_lengths) == 0:
                    stack_obj.log.warning(f"No legend text found for the chart {title} , sum_legends_length is 0")
                else:
                    std=np.std(list_of_legend_lengths)
                    mean=np.mean(list_of_legend_lengths)
                    average_legend_length = mean+1*std
                    available_width_points = (fig_width * 100)/character_width
                    ncol=(available_width_points/(average_legend_length+6))
                    rows=(num_lines/ncol)+1
                    fontsize = initial_legend_fontsize - (fontsize_decrease_rate_with_rows * (rows-1))
                    font_diff = (initial_legend_fontsize-fontsize)
                    if font_diff > 8:
                        scale = 0.024
                    else:
                        scale=0.03
                    final_ncol = ncol + scale*font_diff*(rows-1)
                    # print(f"ncol : {ncol}, finalncol: {final_ncol}, font diff:{initial_legend_fontsize-fontsize} , rows:{rows}")
                    # final_ncol = ncol + ((ncol_increase_rate_with_rows/((average_legend_length**2.09) * (fontsize**2.21))) * (rows-1))
                    if num_lines<50:
                        leg=plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.050), ncol=final_ncol, fontsize=fontsize,handlelength=1,frameon=False)
                        for legobj in leg.legendHandles:
                            legobj.set_linewidth(fig_width/6) 
                file_name = title.replace("/", "-")
                plt.xticks(fontsize=fig_width/1.935,color=text_color)
                plt.yticks(fontsize=fig_width/1.935,color=text_color)
                plt.tight_layout()

                if min(complete_time_set).minute >30:start_min_to_replace=30
                else:start_min_to_replace = 0
                start_time_in_charts = date2num(min(complete_time_set).replace(minute=start_min_to_replace))+(offset_ist_minutes / (60 * 24))

                if max(complete_time_set).minute < 30:
                    end_hr_to_replace=max(complete_time_set).hour
                    end_min_to_replace=30
                else:
                    end_hr_to_replace = max(complete_time_set).hour+1
                    end_min_to_replace = 0
                end_time_in_charts = date2num(max(complete_time_set).replace(minute=end_min_to_replace,hour=end_hr_to_replace))+(offset_ist_minutes / (60 * 24))
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
                stack_obj.log.error(f"Error while generating graph for {title} : {str(e)}")
            finally:
                plt.close()

    stack_obj.log.info(f"Total number of charts generated : {total_charts}")

if __name__=="__main__":
    global delete_image_data
    delete_image_data=True
    import time,pymongo
    # from collections import defaultdict
    from gridfs import GridFS
    from settings import stack_configuration
    # from datetime import datetime, timedelta
    import pytz
    from capture_charts_data import Charts
    from parent_load_details import parent as load_cls
    s_at = time.perf_counter()
    client = pymongo.MongoClient("mongodb://localhost:27017")
    database = client["Osquery_LoadTests"]
    fs = GridFS(database)

    variables = {
        "start_time_str_ist":"2024-01-26 13:25",
        "load_duration_in_hrs":4,
        "test_env_file_name":'s1_nodes.json',
        "build":"153105",

    }
    stack_obj = stack_configuration(variables)

    print("Fetching charts data ...")
    charts_obj = Charts(stack_obj=stack_obj,fs=fs)
    
    step_factor=variables["load_duration_in_hrs"]/10 if variables["load_duration_in_hrs"]>10 else 1
    complete_charts_data_dict,all_gridfs_fileids=charts_obj.capture_charts_and_save(load_cls.get_all_chart_queries(),step_factor=step_factor)
    # complete_charts_data_dict,all_gridfs_fileids=charts_obj.capture_charts_and_save({"live Charts":load_cls.get_other_chart_queries()},step_factor=step_factor)
    print("Saved charts data successfully !")
    path = "/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/publish_practice/images"
    collection = database["Testing"]
    inserted_id = collection.insert_one({"charts":complete_charts_data_dict})    
    create_images_and_save(path,str(inserted_id.inserted_id),collection,fs,variables,stack_obj.end_time_str_ist,1,"Longevity","Multiple Customer Rule Engine, Control Plane, CloudQuery, KubeQuery and SelfManaged Load",step_factor)

    f3_at = time.perf_counter()
    print(f"Collecting the report data took : {round(f3_at - s_at,2)} seconds in total")
else:
    delete_image_data=True