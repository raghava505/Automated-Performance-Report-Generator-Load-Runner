# Steps to save your performance load report data into the database.

## step 1 
1. Login to 'perf-prod-dashboard' node.
2. switch to monkey user (sumonkey)
3. Navigate to project directory(cd tool_support/LoadTests/save-report-data-to-mongo)
4. Pull the latest code from github (git pull origin main). Make sure you do not have any local changes made (git stash).
5. Activate the virtual environment : run the command 'source raghava_venv/bin/activate'

## step 2
Run "/scripts/main.py" and enter the required load details, the report data will be saved to database.

# configure a new lab stack

Create "<your_stack>_nodes.json" file inside "config" folder if not present(only enter the details upto "other_nodes" field).
(NOTE 1: No need to enter the later fields i.e fields containing 'ram', 'cores', storage details)
(NOTE 2: make sure all your stack host ip addresses are mapped in /etc/hosts in autoendtoend node)


# configure a new load type

step 1 : In scripts/input.py, add a new key-value pair inside load_type_options. The key is the load_type and the value is another dictionary storing list of 'subtypes'.

step 2 (optional) : You can also pass another key 'class' by creating a child class from the <parent_load_details.parent> class. This helps to customize your load specific details such as chart queries etc.