#!/bin/bash
nohup python3 /Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/osquery_simulator/endpointsim.py --domain cosmos --secret ae014395-7e94-4f97-aa30-4e9d8e0d36e8 --data_assets 100 &> osx_log_data-4d92964b-5f06-4aa9-8fc9-1df74f0bb224.out &
sleep 10
nohup python3 /Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/osquery_simulator/endpointsim.py --domain cosmos --secret ae014395-7e94-4f97-aa30-4e9d8e0d36e8 --controlplane_assets 100 &> osx_log_controlplane-432b8073-1f89-4611-a578-32ac45aafa47.out &
sleep 10
nohup python3 /Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/osquery_simulator/endpointsim.py --domain cosmos1 --secret c9ce7d77-2e5c-4ae5-b2e1-147a50411bce --data_assets 100 &> osx_log_data-d9f371a1-075c-44a9-91c4-32cc2ca910df.out &
sleep 10
sleep 20
