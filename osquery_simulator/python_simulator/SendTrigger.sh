#!/bin/bash

# Get the directory of the current script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the full path of the current script
# script_path="${script_dir}/$(basename "${BASH_SOURCE[0]}")"

# Print the full path
# echo "The full path of the current file is: $script_path"

nohup python3 $script_dir/LoadTrigger.py &> python_log.out &
