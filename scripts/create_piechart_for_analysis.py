import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# sns.set_theme(palette="dark", font="arial")
outer_background_color="#1A1A1A"
text_color="#FDFEFE"
sns.set(rc={"text.color": text_color})

kwargs={'autopct':'%1.1f%%',
        'startangle':180, 
        'wedgeprops': {'edgecolor': 'black', 'linewidth': 1.0},  # Set edge width
        'textprops': {'fontsize': 17},  # Increase font size of labels
        # 'shadow': True,
        # 'labeldistance': 2.1,  # Increase distance of labels from the center
        # 'pctdistance': 0.5,  # Set distance of percentage labels from the center
        'colors' : ['#196F3D', '#873600', '#76448A', '#21618C', '#9C640C', '#717D7E']
        }

figsize=(26, 16)
title_fontsize=25
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

def create_piechart(mem_or_cpu,app_df,cont_df,nodetype):
    increased = app_df[app_df["absolute"] > 0][["application","absolute"]].head(show_top_n)
    decreased = app_df[app_df["absolute"] < 0][["application","absolute"]].tail(show_top_n)
    decreased["absolute"] = decreased["absolute"].abs()

    fig, axs = plt.subplots(2, 2, figsize=figsize)  # 1 row, 2 columns

    axs[0][0].pie(increased['absolute'], labels=increased["application"], **kwargs)
    title_increased = f'applications contributing to increase in {mem_or_cpu} usage for {nodetype} nodetype'.capitalize()
    axs[0][0].set_title(title_increased, fontsize=title_fontsize)

    axs[0][1].pie(decreased['absolute'], labels=decreased["application"], **kwargs)
    title_decreased = f'applications contributing to decrease in {mem_or_cpu} usage for {nodetype} nodetype'.capitalize()
    axs[0][1].set_title(title_decreased, fontsize=title_fontsize)

#-----
    
    cont_increased = cont_df[cont_df["absolute"] > 0][["container","absolute"]].head(show_top_n)
    cont_decreased = cont_df[cont_df["absolute"] < 0][["container","absolute"]].tail(show_top_n)
    cont_decreased["absolute"] = cont_decreased["absolute"].abs()

    axs[1][0].pie(cont_increased['absolute'], labels=cont_increased["container"], **kwargs)
    cont_title_increased = f'containers contributing to increase in {mem_or_cpu} usage for {nodetype} nodetype'.capitalize()
    axs[1][0].set_title(cont_title_increased, fontsize=title_fontsize)
    
    axs[1][1].pie(cont_decreased['absolute'], labels=cont_decreased["container"], **kwargs)
    cont_title_decreased = f'containers contributing to decrease in {mem_or_cpu} usage for {nodetype} nodetype'.capitalize()
    axs[1][1].set_title(cont_title_decreased, fontsize=title_fontsize)
               
    plt.gcf().set_facecolor(outer_background_color)
    # plt.subplots_adjust(wspace=0.5) 

    plt.tight_layout()
    plt.savefig(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_{nodetype}.png")

    # app_df.to_csv(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_application_{nodetype}.csv", index=False) 
    # cont_df.to_csv(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_container_{nodetype}.csv", index=False) 


def call_create_piechart(mem_or_cpu,main_dict,prev_dict):
    current_main_dict_application=main_dict[f'nodetype_and_application_level_{mem_or_cpu}_usages']
    current_prev_dict_application=prev_dict[f'nodetype_and_application_level_{mem_or_cpu}_usages']

    current_main_dict_container=main_dict[f'nodetype_and_container_level_{mem_or_cpu}_usages']
    current_prev_dict_container=prev_dict[f'nodetype_and_container_level_{mem_or_cpu}_usages']
    for nodetype,schema_dict in current_main_dict_application.items():
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

        create_piechart(mem_or_cpu,app_df,cont_df,nodetype)
        