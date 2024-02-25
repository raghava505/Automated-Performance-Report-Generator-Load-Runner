import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from PIL import Image
import io

# sns.set_theme(palette="dark", font="arial")
outer_background_color="#191b1f"
text_color="#FDFEFE"
sns.set(rc={"text.color": text_color})

kwargs={'startangle':270, 
        'wedgeprops': {'edgecolor': 'black', 'linewidth': 1.0},  # Set edge width
        'textprops': {'fontsize': 11},  # Increase font size of labels
        'colors' : ['#145A32','#641E16','#154360','#7D6608','#4A235A','#424949','#784212'],
        'rotatelabels':True,
        'labeldistance':0.9,
        'pctdistance':0.7,
        }

figsize=(27, 15)
title_fontsize=18
show_top_n=10

def compare_dfs(main,prev,merge_on):
    main.rename(columns={'avg': 'avg_main'}, inplace=True)
    prev.rename(columns={'avg': 'avg_prev'}, inplace=True)

    merged_df = pd.merge(prev,main, on=merge_on, how='outer')
    merged_df.fillna(0,inplace=True)
    merged_df["absolute"] = merged_df["avg_main"]- merged_df["avg_prev"] 
    merged_df["relative"] = (merged_df["avg_main"]- merged_df["avg_prev"] )*100/merged_df["avg_prev"]
    merged_df=merged_df.sort_values(by='absolute', ascending=False)
    return merged_df

def autopct_format(values,mem_or_cpu,sign='+'):
    if mem_or_cpu=="memory":
        unit="GB"
    else:
        unit="cores"
    def my_format(pct):
        total = sum(values)
        val = round(float(pct*total/100),2)
        return '{:.1f}%\n({}{} {})'.format(pct,sign, val,unit)
    return my_format

def create_piechart(mem_or_cpu,app_df,cont_df,nodetype):
    plots_dict={}
    if mem_or_cpu=="memory":
        unit="GB"
    else:
        unit="cores"
    increased = app_df[app_df["absolute"] > 0][["application","absolute"]]
    sum_app_increased = round(sum(increased["absolute"]),2)
    increased=increased.head(show_top_n)
    decreased = app_df[app_df["absolute"] < 0][["application","absolute"]]
    sum_app_decreased = round(sum(decreased["absolute"]),2)
    decreased=decreased.tail(show_top_n).sort_values(by="absolute",ascending=True)
    decreased["absolute"] = decreased["absolute"].abs()

    fig, axs = plt.subplots(2, 2, figsize=figsize)  # 2 row, 2 columns

    axs[0][0].pie(increased['absolute'], labels=increased["application"],autopct=autopct_format(increased['absolute'],mem_or_cpu), **kwargs)
    title_increased = f'applications contributing to {"increase".upper()} in {mem_or_cpu} usage for "{nodetype}" nodetype (+{sum_app_increased} {unit} ↑)'
    axs[0][0].set_title(title_increased, fontsize=title_fontsize)

    axs[0][1].pie(decreased['absolute'], labels=decreased["application"],autopct=autopct_format(decreased['absolute'],mem_or_cpu,'-'), **kwargs)
    title_decreased = f'applications contributing to {"decrease".upper()} in {mem_or_cpu} usage for "{nodetype}" nodetype ({sum_app_decreased} {unit} ↓)'
    axs[0][1].set_title(title_decreased, fontsize=title_fontsize)

#-----
    
    cont_increased = cont_df[cont_df["absolute"] > 0][["container","absolute"]]
    sum_cont_increased = round(sum(cont_increased["absolute"]),2)
    cont_increased=cont_increased.head(show_top_n)
    cont_decreased = cont_df[cont_df["absolute"] < 0][["container","absolute"]]
    sum_cont_decreased = round(sum(cont_decreased["absolute"]),2)
    cont_decreased=cont_decreased.tail(show_top_n).sort_values(by="absolute",ascending=True)
    cont_decreased["absolute"] = cont_decreased["absolute"].abs()

    axs[1][0].pie(cont_increased['absolute'], labels=cont_increased["container"],autopct=autopct_format(cont_increased['absolute'],mem_or_cpu), **kwargs)
    cont_title_increased = f'containers contributing to {"increase".upper()} in {mem_or_cpu} usage for "{nodetype}" nodetype (+{sum_cont_increased} {unit} ↑)'
    axs[1][0].set_title(cont_title_increased, fontsize=title_fontsize)
    
    axs[1][1].pie(cont_decreased['absolute'], labels=cont_decreased["container"],autopct=autopct_format(cont_decreased['absolute'],mem_or_cpu,'-'), **kwargs)
    cont_title_decreased = f'containers contributing to {"decrease".upper()} in {mem_or_cpu} usage for "{nodetype}" nodetype ({sum_cont_decreased} {unit} ↓)'
    axs[1][1].set_title(cont_title_decreased, fontsize=title_fontsize)

    main_title=f"Complete {mem_or_cpu} usage analysis for '{nodetype}' nodetype"
    fig.suptitle(f"{main_title}\n\n", fontsize=title_fontsize+2)

    plt.gcf().set_facecolor(outer_background_color)
    # plt.subplots_adjust(left=10.1, right=10.9, bottom=0.1, top=0.9, wspace=70.4, hspace=700.4)
    plt.tight_layout()
    # plt.savefig(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_{nodetype}.png")

    # app_df.to_csv(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_application_{nodetype}.csv", index=False) 
    # cont_df.to_csv(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_container_{nodetype}.csv", index=False) 
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)  # Reset the buffer position
    
    image = Image.open(buffer)
    plt.close()
    
    plots_dict[main_title] = image
    return plots_dict

def compress(val):
    last = val.split('/')[-1]
    if len(last)>30:
        last = last.split('-')[-1]
    last=last.capitalize()
    return last

def call_create_piechart(mem_or_cpu,main_dict,prev_dict):
    current_main_dict_application=main_dict[f'nodetype_and_application_level_{mem_or_cpu}_usages']
    current_prev_dict_application=prev_dict[f'nodetype_and_application_level_{mem_or_cpu}_usages']

    current_main_dict_container=main_dict[f'nodetype_and_container_level_{mem_or_cpu}_usages']
    current_prev_dict_container=prev_dict[f'nodetype_and_container_level_{mem_or_cpu}_usages']
    return_piecharts={}
    for nodetype,schema_dict in current_main_dict_application.items():
        if nodetype not in ["process","data","pg","ep"]:continue
        print(f"Analysing {mem_or_cpu} usages for nodetype '{nodetype}'")
        main_app_df = pd.DataFrame(schema_dict["table"])
        prev_app_df = pd.DataFrame(current_prev_dict_application[nodetype]["table"])

        main_cont_df = pd.DataFrame(current_main_dict_container[nodetype]["table"])
        prev_cont_df = pd.DataFrame(current_prev_dict_container[nodetype]["table"])

        if main_app_df.empty:
            print(f"Main application dataframe for {nodetype} is found empty")
            continue
        elif prev_app_df.empty:
            print(f"Previous container dataframe for {nodetype} is found empty")
            continue
        elif main_cont_df.empty:
            print(f"Main application dataframe for {nodetype} is found empty")
            continue
        elif prev_cont_df.empty:
            print(f"Previous container dataframe for {nodetype} is found empty")
            continue

        app_df= compare_dfs(main_app_df,prev_app_df,merge_on=["node_type","application"])
        cont_df= compare_dfs(main_cont_df,prev_cont_df,merge_on=["node_type","container"])

        app_df["application"] = app_df["application"].apply(compress)
        cont_df["container"] = cont_df["container"].apply(compress)
        return_piecharts.update(create_piechart(mem_or_cpu,app_df,cont_df,nodetype))
    
    # for title,im in return_piecharts.items():
    #     # im.show(title=title)
    #     im.save("/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/"+title+".png")

    return return_piecharts
        