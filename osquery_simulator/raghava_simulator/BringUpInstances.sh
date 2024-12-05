script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

nohup python3 $script_dir/InitiateLoad.py  > assets.log 2>&1 &
disown -ah