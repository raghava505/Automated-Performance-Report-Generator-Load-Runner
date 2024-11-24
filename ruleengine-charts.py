import pandas as pd
import matplotlib.pyplot as plt

# Step 1: Read the CSV file
file_path = '163-ruleengine-cpu.csv'  # Replace with your actual file path
data = pd.read_csv(file_path)

# Step 2: Convert 'Time' column to datetime
data['Time'] = pd.to_datetime(data['Time'])

# Step 3: Process the other columns
# Convert percentage strings to numeric values (removing the '%' sign and converting to float)
data.iloc[:, 1:] = data.iloc[:, 1:].replace('%', '', regex=True).astype(float)

# Step 4: Plot the data
plt.figure(figsize=(14, 8))

# Plot each column except 'Time'
for column in data.columns[1:]:
    plt.plot(data['Time'], data[column], label=column)

# Customizing the plot
plt.title('Time Series Data')
plt.xlabel('Time')
plt.ylabel('Values (%)')
plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
plt.legend()
plt.grid()
plt.tight_layout()  # Adjust layout to prevent clipping of labels
plt.show()
