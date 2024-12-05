#!/bin/bash

# Get the directory of the current script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the full path of the current script
# script_path="${script_dir}/$(basename "${BASH_SOURCE[0]}")"

# Print the full path
# echo "The full path of the current file is: $script_path"

# Find and kill all processes with the keyword "endpointsim.py"
echo "Searching for processes containing 'endpointsim.py'..."

# List processes, filter for "endpointsim.py", and extract PIDs
pids=$(ps aux | grep "endpointsim.py" | grep -v grep | awk '{print $2}')

if [ -z "$pids" ]; then
    echo "No processes found containing 'endpointsim.py'."
else
    echo "Killing the following processes:"
    echo "$pids"
    
    # Kill the processes
    echo "$pids" | xargs kill -9
    echo "All processes containing 'endpointsim.py' have been terminated."
fi

sleep 3

nohup python3 $script_dir/InitiateLoad.py  > assets.log 2>&1 &
disown -ah