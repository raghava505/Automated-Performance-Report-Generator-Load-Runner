import time
import zmq
import json

# message = """1767638765{
#     "node_key": "NODEKEY",
#     "action": "added",
#     "data": [
#     {
#         "name": "memory_info",
#         "calendarTime": "Wed Jul 15 21:08:45 2020 UTC",
#         "counter": "1",
#         "epoch": "1594741297754",
#         "unixTime": "UNIXTIMESTAMP",
#         "action": "added",
#         "columns": {
#         "swap_cached": "0",
#         "memory_free": "62628204544",
#         "swap_free": "0",
#         "cached": "2620739584",
#         "memory_total": "67558985728",
#         "swap_total": "0",
#         "__rid__": "38ed79ffaa858e8315b279f952fffcff09ec3942",
#         "inactive": "1035059200",
#         "active": "2743885824",
#         "buffers": "307703808"
#         },
#         "hostIdentifier": "ASSETID"
#     }
#     ],
#     "log_type": "result"
# }"""

def producer():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://127.0.0.1:5555")  # Bind to a local port

    print("Producer started. Waiting for subscribers to connect...")
    time.sleep(2)  # Allow time for subscribers to connect

    print("Posting messages...")

    input_file_path="/Users/masabathulararao/Documents/jmeter-tool/rhel7-6tab_12rec.log"
    original_endline = endline = 1 #duration will be equal to double of this value (in sec)
    
    with open(input_file_path, "r") as file:
        while endline:
            timestamp_line = file.readline().strip()
            json_line = file.readline().strip()
            if not timestamp_line or not json_line:
                print("Reached end of the file.")
                break
            
            try:
                # Parse the JSON line
                message = json.loads(json_line)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print(f"Invalid JSON: {json_line}")

            # # Publish the message
            socket.send_json(message)
            endline -= 1
            print(f"Published message, endline remaining : {endline}/{original_endline}")
            time.sleep(2)  # Wait 2 seconds

if __name__ == "__main__":
    producer()
