# Steps to save your performance load report data into the database.

## Step 1 
  Add the below line to ``` /etc/hosts ```
 ```
 192.168.146.69 perf-prod-dashboard
 ```
1. Login to **perf-prod-dashboard** node as abacus user.
 ```
 ssh abacus@192.168.146.69
 ```
2. Switch to monkey user
 ```
 sumonkey
 ```
3. Navigate to project directory
```
cd tool_support/LoadTests/save-report-data-to-mongo
```
4. Pull the latest code from github.
*Make sure there are no any local uncommited changes*
```
git checkout main
git pull origin main
```
5. Activate the python virtual environment
```
source raghava_env/bin/activate
```
## Step 2
Run the below command
```
python3 scripts/main.py
```
Enter the required load details and the report data will be saved to Mongodb.

### Accessing the Mongodb
```
docker exec -it mongo bash 
```

# Configure a New Lab Stack

Create "<your_stack>_nodes.json" file inside "config" folder if not present 

*Make sure to enter the details upto "other_nodes" field*
-  *No need to enter the later fields i.e fields containing 'ram', 'cores', storage details*
-  *Make sure all your stack host IP Addresses are mapped in ```/etc/hosts``` in perf-prod-dashboard Node*

Example
```
vi /config/S12_nodes.json
```



# Configure a New Load Type

-  In ```scripts/input.py```  Add a new key-value pair inside load_type_options. The key is the ```load_type``` and the value is another dictionary storing list of ```subtypes```.
   
-  Optionally you can also pass another key ```class``` by creating a child class from the ```<parent_load_details.parent> class```. This helps to customize your load specific details such as chart queries etc.
