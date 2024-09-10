# Setup and Install Report Generator tool
1. set 'REPORT_GENERATOR_ROOT_PATH' environment variable in your machine.
    example : 
     ```
     sumonkey
     mkdir report_generator_project
     export REPORT_GENERATOR_ROOT_PATH=/opt/uptycs/report_generator_project
     cd report_generator_project
    ```
2. Go to the 'REPORT_GENERATOR_ROOT_PATH' path, and git clone this repository (verify/make sure that the git cloned project directonay name is "save-report-data-to-mongo")
3. 'cd save-report-data-to-mongo'
4. 'docker-compose up -d' (make sure docker is installed in your machine)
    This step installs 'mongo-report' and 'load-report-generator' containers .

---

# Collect your first report
1.  Enter into interactive mode 
```
docker exec -it load-report-generator bash   
```
2. run 'python3 scripts/main.py'
3. Enter the required load details and the report data will be saved to Mongodb.

# Generate your first report

1. Open 8012 port of your machine in the browser (prefer chrome)
2. Select the saved report(s) data to view/publish the report.

---
