# Steps to save your load report data into the database.

## step 1 
clone this repository into your local machine

## step 2

### step 2.1
Create "<your_stack>_nodes.json" file inside "config" folder if not present(only enter the details upto "other_nodes" field).
(NOTE : No need to enter the later fields i.e fields containing 'ram', 'cores', storage details)

### step 2.2
Verify the details of your load in "config/load_specific_details.json" and update if needed.

## step 3
Now, run "/scripts/main.py" and enter the required load details, the report data will be saved to database.