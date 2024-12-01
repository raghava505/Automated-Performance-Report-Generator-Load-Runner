
import paramiko

# Configuration
configdb_node = "192.168.148.75"
username = "abacus"  # Replace with your SSH username
password = "abacus"  # Replace with your SSH password

query = "select domain,secret from customers order by 1"
configdb_command = f'sudo docker exec postgres-configdb15 bash -c "PGPASSWORD=pguptycs psql -U postgres configdb -c \\"{query}\\""'

try:
    # Create an SSH client
    ssh_client = paramiko.SSHClient()
    
    # Automatically add the remote server's SSH key if missing
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Connect to the remote machine
    ssh_client.connect(hostname=configdb_node, username=username, password=password)
    print(f"Connected to {configdb_node}")
    
    # Execute the command
    stdin, stdout, stderr = ssh_client.exec_command(configdb_command)
    
    # Read the output and errors
    output = stdout.read().decode()
    errors = stderr.read().decode()

    # Display the output
    if output:
        print(f"Command Output:\n{output}")
    if errors:
        print(f"Command Errors:\n{errors}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the SSH connection
    ssh_client.close()
    print("Connection closed.")

# Step 1: Split the data into lines
lines = output.strip().split('\n')

# Step 2: Create an empty dictionary
domain_dict = {}

# Step 3: Loop through each line and split by the '|' character
for line in lines:
    domain, secret = line.split('|')
    
    # Clean the domain and secret values (strip spaces)
    domain = domain.strip()
    secret = secret.strip()
    
    # Add to dictionary
    domain_dict[domain] = secret

# Output the dictionary
print(domain_dict)

for domain,secret in domain_dict.items():
    print(domain,secret)

number_of_simulators = 12
domain = "jupiter"