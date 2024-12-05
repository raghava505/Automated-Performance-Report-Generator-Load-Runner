import json
import subprocess
import random

hostname = subprocess.run("hostname",shell=True,capture_output=True,text=True).stdout.strip()

def generate_names(instance:dict, createNew: bool) -> dict:
    clients = instance["clients"]
    domain = instance["domain"]
    suffix = random.randint(1,100)
    prefix = random.randint(1,100)
    
    file = instance["names"]
    if createNew:
        file = f"{domain}_names_{prefix}{suffix}.txt"
        instance["names"] = file
        
    with open(file, "w") as f:
        for i in range(clients):
            name = f"test-{domain}-{hostname}-{i+1}-{prefix}{suffix}\n"
            f.write(name)
    return instance


def generate():
    with open("testinput.json", 'r') as file:
        data = json.load(file)
        for instance in data["instances"]:
            instance = generate_names(instance, False)  
        
    with open("testinput.json", "w") as file:
        file.write(json.dumps(data, indent=4))
        
if __name__ == "__main__":
    generate()
        