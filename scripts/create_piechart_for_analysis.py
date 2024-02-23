import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

sns.set_style("whitegrid")

kwargs={'autopct':'%1.1f%%', 'startangle':140, 'colors':sns.color_palette('pastel'), 'wedgeprops':{'edgecolor': 'black'}}
figsize=(10, 8)
fontsize=16


def compare_dfs(main,prev,merge_on):
    main.rename(columns={'avg': 'avg_main'}, inplace=True)
    prev.rename(columns={'avg': 'avg_prev'}, inplace=True)

    merged_df = pd.merge(prev,main, on=merge_on, how='outer')
    merged_df.fillna(0,inplace=True)
    merged_df["absolute"] = merged_df["avg_main"]- merged_df["avg_prev"] 
    merged_df["relative"] = (merged_df["avg_main"]- merged_df["avg_prev"] )*100/merged_df["avg_prev"]
    merged_df=merged_df.sort_values(by='absolute', ascending=False)
    return merged_df

def create_piechart(mem_or_cpu,app_or_cont,df,nodetype):
    increased = df[df["absolute"] > 0][[app_or_cont,"absolute"]]
    decreased = df[df["absolute"] < 0][[app_or_cont,"absolute"]]
    decreased["absolute"] = decreased["absolute"].abs()

    plt.figure(figsize=figsize)
    plt.pie(increased['absolute'], labels=increased[app_or_cont],**kwargs)
    plt.title(f'{app_or_cont}s contributing to increase in {mem_or_cpu} usage for {nodetype} nodetype'.capitalize(), fontsize=fontsize)
    plt.savefig(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_{app_or_cont}_{nodetype}_increased.png")
    
    
    plt.figure(figsize=figsize)
    plt.pie(decreased['absolute'], labels=decreased[app_or_cont],**kwargs)
    plt.title(f'{app_or_cont}s contributing to decrease in {mem_or_cpu} usage for {nodetype} nodetype'.capitalize(), fontsize=fontsize)
    plt.savefig(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_{app_or_cont}_{nodetype}_increased.png")
    
    # df.to_csv(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_{app_or_cont}_{nodetype}.csv", index=False) 


def call_create_piechart(mem_or_cpu,main_dict,prev_dict):
    application_or_container=["application","container"]
    for app_or_cont in application_or_container:
        current_main_dict=main_dict[f'nodetype_and_{app_or_cont}_level_{mem_or_cpu}_usages']
        current_prev_dict=prev_dict[f'nodetype_and_{app_or_cont}_level_{mem_or_cpu}_usages']
        for nodetype,schema_dict in current_main_dict.items():
            print(f"Analysing {app_or_cont} level {mem_or_cpu} usages for nodetype '{nodetype}'")
            main_df = pd.DataFrame(schema_dict["table"])
            prev_df = pd.DataFrame(current_prev_dict[nodetype]["table"])
            if main_df.empty:
                print(f"Main dataframe for {nodetype} is found empty")
                continue
            elif prev_df.empty:
                print(f"Previous dataframe for {nodetype} is found empty")
                continue
            df= compare_dfs(main_df,prev_df,merge_on=["node_type",app_or_cont])
            create_piechart(mem_or_cpu,app_or_cont,df,nodetype)
        