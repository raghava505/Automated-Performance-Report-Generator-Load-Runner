from settings import configuration
import os,json
from parent_load_details import parent
from osquery.osquery_child_class import osquery_child
from cloudquery.cloudquery_child_class import cloudquery_child
from kubequery.kubequery_child_class import kubequery_child
from combined_loads_setup import all_combined_child,osquery_cloudquery_combined_child

bool_options=[False,True]
load_type_options = {   
                        'Osquery':{
                                        'subtypes':['ControlPlane', 'SingleCustomer', 'MultiCustomer'],
                                        'class':osquery_child
                                  },
                        'CloudQuery':{
                                        'subtypes':['AWS_MultiCustomer','GCP_MultiCustomer','AWS_SingleCustomer'],
                                        'class':cloudquery_child
                                     },
                        'KubeQuery_and_SelfManaged':{
                                        'subtypes':['KubeQuery_SingleCustomer','SelfManaged_SingleCustomer'],
                                        'class':kubequery_child
                                    } ,
                        'osquery_cloudquery_combined':{
                                        'subtypes':['Osquery(multi)_CloudQuery(aws_gcp_multi)'],
                                        'class':osquery_cloudquery_combined_child
                                    },
                        'all_loads_combined':{
                                        'subtypes':['Osquery(multi)_CloudQuery(aws_gcp_multi)_KubeQuery(single)_and_SelfManaged(single)'],
                                        'class':all_combined_child
                                    }
                     }

all_files = os.listdir(configuration().base_stack_config_path)
test_env_path_options = sorted([file for file in all_files if file.endswith('.json') and '_nodes' in file])

def create_input_form():
    details = {
            "test_env_file_name":'longevity_nodes.json',
            "load_type":"KubeQuery_and_SelfManaged",
            "load_name": "KubeQuery_SingleCustomer",
            "start_time_str_ist":  "2023-12-05 22:40",
            "load_duration_in_hrs": 10,
            "sprint": 144,
            "build": "144068",
            "add_extra_time_for_charts_at_end_in_min": 10,
            "api_load_csv_file_path":"/path/to/file.csv"
            # "fetch_node_parameters_before_generating_report" :  False,
            }
    
    # These three lines are for Debugging Purposes :)
    # load_cls = load_type_options[details["load_type"]]['class']
    # prom_con_obj = configuration(test_env_file_name=details['test_env_file_name'] , fetch_node_parameters_before_generating_report=False)
    # return details,prom_con_obj,load_cls

    print("Please enter the following load details ...")
    for key,value in details.items():
        Type =type(value)
        if Type == str:            
            if key == "load_type":
                helper_text=''
                for i,val in enumerate(load_type_options.keys()):
                    helper_text += f"\n {i} : {val}"
                helper_text += "\n select one option " 
                input_index = int(input(f"Enter : {' '.join(str(key).split('_')).title()} {helper_text} : ").strip())
                input_value = list(load_type_options.keys())[input_index]
            elif key == "load_name":
                helper_text=''
                for i,val in enumerate(load_type_options[details["load_type"]]['subtypes']):
                    helper_text += f"\n {i} : {val}"
                helper_text += "\n select one option "
                input_index = int(input(f"Enter : {' '.join(str(key).split('_')).title()} {helper_text} : ").strip())
                input_value = load_type_options[details["load_type"]]['subtypes'][input_index]
            elif key == "test_env_file_name":
                helper_text=''
                for i,val in enumerate(test_env_path_options):
                    helper_text += f"\n {i} : {val}"
                helper_text += "\n select one option " 
                input_index = int(input(f"Enter : {' '.join(str(key).split('_')).title()} {helper_text} : ").strip())
                input_value = test_env_path_options[input_index]
            elif key == "api_load_csv_file_path":
                input_value=str(input(f"Enter : {' '.join(str(key).split('_')).title()}  (example: {value}) .Press ENTER to skip this variable : ").strip())
            else:
                input_value=str(input(f"Enter : {' '.join(str(key).split('_')).title()}  (example: {value}) : ").strip())
        
        elif Type==bool:
            helper_text=''
            for i,val in enumerate(bool_options):
                helper_text += f"\n {i} : {val}"
            helper_text += "\n select one option " 
            input_index = int(input(f"Enter : {' '.join(str(key).split('_')).title()} {helper_text} : ").strip())
            input_value = bool_options[input_index]
        elif Type == int:
            if key == "sprint":
                input_value=int(input(f"Enter release {' '.join(str(key).split('_')).title()}  (example: {value}) : ").strip())
            else:
                input_value=int(input(f"Enter : {' '.join(str(key).split('_')).title()}  (example: {value}) : ").strip())

        details[key] = Type(input_value)

    print("The details you entered are : ")
    for key,val in details.items():
        print(f"{key} : {val}")

    print()
    try:
        load_cls = load_type_options[details["load_type"]]['class']
        print(f"Using load class : {load_cls}")
    except:
        print(f"WARNING: load class for {load_type_options[details['load_type']]} is not found , hence using the parent class : {parent}")
        load_cls = parent
    print(f"Please verify the below load details for {details['load_type']}:{details['load_name']} : ")
    print(json.dumps(load_cls.get_load_specific_details(details["load_name"]), indent=4))
    edit_inp=input(f"These details will be saved to database. Enter any one of the 2 strings (edit/proceed) : ").strip().lower()
    if edit_inp == 'edit':
        print("(NOTE : To set default value press enter)")
        old_dictionary = load_cls.get_load_specific_details(details["load_name"])
        new_dictionary={}
        for key,val in old_dictionary.items():
            new_input = input(f"Enter '{key}' (default : {val}) : ").strip()
            if new_input=="":new_dictionary[key] = old_dictionary[key]
            else:new_dictionary[key] = new_input
        load_cls.load_specific_details[details["load_name"]]=new_dictionary
        print("Your new details are : ")
        print(json.dumps(load_cls.get_load_specific_details(details["load_name"]), indent=4))

    user_input = input("Are you sure you want to continue with these details? This will make permenant changes in the database (y/n): ").strip().lower()

    if user_input =='y':
        print("Continuing ...")
        prom_con_obj = configuration(test_env_file_name=details['test_env_file_name'] , fetch_node_parameters_before_generating_report=True)
        return details,prom_con_obj,load_cls
    elif user_input =='n':
        print("OK! Enter the modified details ...")
        return create_input_form()
    else:
        print("INVALID INPUT!")
        return None,None,None

if __name__ == "__main__":
    details = create_input_form()
    print(details) 