import pandas as pd
import numpy as np

def process_csv(file_path):
    # Step 1: Read the CSV file
    data = pd.read_csv(file_path)

    # Step 2: Convert 'Time' column to datetime
    data['Time'] = pd.to_datetime(data['Time'])

    # Step 3: Process the other columns to convert percentage strings to float
    data.iloc[:, 1:] = data.iloc[:, 1:].replace('%', '', regex=True).astype(float)
    print(data)
    # data['Scaled Row Ave'] = data.iloc[:, 1:].mean(axis=1)

    # # Create a new DataFrame with only 'Time' and 'Scaled Row Ave' columns
    # data = data[['Time', 'Scaled Row Ave']]
    # print(data)
    # Step 4: Calculate required statistics
    min_values = data.iloc[:, 1:].min() / 100
    max_values = data.iloc[:, 1:].max() / 100
    average_values = data.iloc[:, 1:].mean() / 100
    percentiles_99 = data.iloc[:, 1:].quantile(0.99) / 100
    percentiles_95 = data.iloc[:, 1:].quantile(0.95) / 100
    percentiles_90 = data.iloc[:, 1:].quantile(0.90) / 100
    percentiles_85 = data.iloc[:, 1:].quantile(0.85) / 100
    percentiles_80 = data.iloc[:, 1:].quantile(0.80) / 100
    percentiles_75 = data.iloc[:, 1:].quantile(0.75) / 100

    # Step 5: Create a DataFrame for the statistics
    stats_df = pd.DataFrame({
        'Min': min_values,
        'Max': max_values,
        'Average': average_values,
        '99th Percentile': percentiles_99,
        '95th Percentile': percentiles_95,
        '90th Percentile': percentiles_90,
        '85th Percentile': percentiles_85,
        '80th Percentile': percentiles_80,
        '75th Percentile': percentiles_75
    })
    print(stats_df)
    # Step 6: Round all values to 2 decimal places and return the mean of each column
    return stats_df.mean().round(2)

# Process both CSV files
df_162 = process_csv('162-2days-cpu.csv')
df_163 = process_csv('163-2days-cpu.csv')

# Combine both final comparison DataFrames for easier calculation
final_df_162 = pd.DataFrame(df_162, columns=['162 code (cores)'])
final_df_163 = pd.DataFrame(df_163, columns=['163 code (cores)'])
combined_df = pd.concat([final_df_162, final_df_163], axis=1)

# Calculate absolute and relative differences
combined_df['Absolute Difference (cores)'] = combined_df['163 code (cores)'] - combined_df['162 code (cores)']
combined_df['Relative Difference (%)'] = ((combined_df['Absolute Difference (cores)'] / combined_df['162 code (cores)']) * 100).round(2)

# Add up/down arrow indicators
combined_df['Absolute Difference (cores)'] = np.where(
    combined_df['Absolute Difference (cores)'] > 0,
    combined_df['Absolute Difference (cores)'].abs().round(2).astype(str) + " ⬆️",
    combined_df['Absolute Difference (cores)'].abs().round(2).astype(str) + " ⬇️"
)

combined_df['Relative Difference (%)'] = np.where(
    combined_df['Relative Difference (%)'] > 0,
    combined_df['Relative Difference (%)'].abs().round(2).astype(str) + " ⬆️",
    combined_df['Relative Difference (%)'].abs().round(2).astype(str) + " ⬇️"
)

# Display the final comparison DataFrame and save it to a CSV file
print(df_163)

print(combined_df)
combined_df.to_csv("result.csv", index=True)
