# Setup and Install Report Generator tool
1. set ```REPORT_GENERATOR_ROOT_PATH``` environment variable in your machine.

    example : 
     ```
     sumonkey
     mkdir report_generator_project
     export REPORT_GENERATOR_ROOT_PATH=/opt/uptycs/report_generator_project
    ```
<br>

2. Navigate to  ```REPORT_GENERATOR_ROOT_PATH``` path, and git clone this repository 

    (make sure / verify that the directory name of git cloned project is ```save-report-data-to-mongo```)

    ```
    cd $REPORT_GENERATOR_ROOT_PATH
    git clone https://github.com/masabathularao-uptycs/save-report-data-to-mongo.git
    cd save-report-data-to-mongo 
    ```
<br>

3. install the ```mongo-report``` and ```load-report-generator``` docker contaiers by running :

    ```
    docker-compose up -d
    ```
    NOTE : This step builds the image in your machine. We will pushing the built image to a docker hub in futube, which avoids building the image locally.

---

# Collect your first report
1.  Enter into interactive mode 
    (optional : run this if you want to fetch the latest changes)
    ```
    git pull origin main
    ```
    ```
    docker exec -it load-report-generator bash   
    ```

2. Run the python script and enter required details to collect the report data and save to mongo:
    ```
    python3 scripts/main.py
    ```

# Generate/View your first report

1. Open <your_host_ip:8012> url in browser of your choice.
2. Select the saved report(s) data to view/publish the performance load report.

---
