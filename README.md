[View the PDF](presentation.pdf)

# Setup and Install Report Generator tool
1. set ```REPORT_GENERATOR_ROOT_PATH```  and  ```LOCAL_IP_ADDRESS``` environment variables in your machine.

    example : 
     ```
    sumonkey
    mkdir report_generator_project
    echo 'export REPORT_GENERATOR_ROOT_PATH=/opt/uptycs/report_generator_project' >> ~/.bashrc
    echo 'export LOCAL_IP_ADDRESS=<YOUR_NODE_IP>'  >> ~/.bashrc
    source ~/.bashrc
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

3. install the ```mongo-report``` and ```load-report-generator``` docker containers by running :

    ```
    docker-compose up -d
    ```
    NOTE : This step builds the image in your machine. We will be pushing the built image to a docker hub in future, which avoids building the image locally.

---

# Collect your first report
1.  (optional : run this if you want to fetch the latest changes)
    
    ```
    cd $REPORT_GENERATOR_ROOT_PATH/save-report-data-to-mongo 
    git pull origin main
    ```
   
2. Enter into interactive mode 
    ```
    docker exec -it load-report-generator bash   
    ```

3. Run the python script and enter required details to collect the report data and save to mongo:
    ```
    python3 scripts/main.py
    ```

# Generate/View your first report

1. Open <your_host_ip:8012> url in browser of your choice.
2. Select the saved report(s) data to view/publish the performance load report.

---
