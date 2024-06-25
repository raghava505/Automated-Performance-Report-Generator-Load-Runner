# Steps to save your performance load report data into the database.

1. Login to **perf-prod-dashboard** node .
 ```
 ssh abacus@192.168.146.69
 ```
2. Switch to monkey user
 ```
 sumonkey
 ```
3. Run generate_report.py script
```
./generate_report.sh
```
Enter the required load details and the report data will be saved to Mongodb.
Then you can publish your report from this UI : http://192.168.146.69:5050

# Configure a New Lab Stack

1. Create "<your_stack_name>_nodes.json" file inside "stacks" folder if not present 
```
vi /stacks/<your_stack_name>_nodes.json
```
2. Make sure all your stack host IP Addresses are mapped in ```/etc/hosts``` in perf-prod-dashboard Node


# Configure a New Load Type

-  In ```scripts/input.py```  Add a new key-value pair inside load_type_options. The key is the ```load_type``` and the value is another dictionary storing list of ```subtypes```.
   
-  Optionally you can also pass another key ```class``` by creating a child class from the ```<parent_load_details.parent> class```. This helps to customize your load specific details such as chart queries etc.


python environment version: 3.11.4
