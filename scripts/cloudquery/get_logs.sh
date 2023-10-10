#!/bin/bash

simulators=("s4simhost1b" "s4simhost1d" "s4simhost2b" "s4simhost2d" "s4simhost3b" "s4simhost3d" "s4simhost4b" "s4simhost4d" "s4simhost5b" "s4simhost5d" "s4simhost6b" "s4simhost6d")

remote_logs_path="~/multi-customer-cqsim/aws/logs"

output_folder="expected_logs"
mkdir -p $output_folder

for simulator in "${simulators[@]}"; do
    
    dictionary=$(ssh abacus@$simulator "cd $remote_logs_path; tail -1 \$(ls -trh | tail -1) | grep -oP 'printlogs:\s+\K.*'")

   
    json_data=$(echo $dictionary | sed "s/'/\"/g")

    
    echo $json_data > $output_folder/${simulator}_dict.json

    echo "Extracted dictionary saved for $simulator"
done

echo "Extraction and saving process completed."
