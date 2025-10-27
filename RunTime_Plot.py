# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 16:57:21 2024

@author: OEM
"""

import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

# Load the CSV file
file_path = 'D:/Nationwide_Tsunami_Inundation/Inundation_Runtimes.csv'  # Replace with the correct path to your CSV file
df = pd.read_csv(file_path)

# Function to convert "0 days 02:24:44.269052" to seconds
def convert_to_seconds(time_str):
    days, time = time_str.split(' days ')
    days = int(days)
    hours, minutes, seconds = map(float, time.split(':'))
    total_seconds = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds).total_seconds()
    return total_seconds

# Apply the conversion to the 'Run_Time' column
df['Run_Time_Seconds'] = df['Run_Time'].apply(convert_to_seconds)

# Create the 'Return_Period' column based on 'turn_Peri' and 'percentile'
df['Return Period'] = df.apply(lambda row: f"H{int(row['Return_Period'])}y{int(row['Percentile'])}p", axis=1)

# Define the specific order for 'Return Period Event'
order = ['H100y50p', 'H100y84p', 'H250y50p', 'H250y84p', 'H500y50p', 'H500y84p', 
         'H1000y50p', 'H1000y84p', 'H1500y50p', 'H1500y84p', 'H2000y50p', 'H2000y84p', 
         'H2500y50p', 'H2500y84p']

# Convert 'Return_Period' to a categorical type with the specific order
df['Return Period'] = pd.Categorical(df['Return Period'], categories=order, ordered=True)

# Sort the DataFrame by 'Return_Period'
df = df.sort_values('Return Period')

# Calculate the 99th percentile for each return period event
percentiles = df.groupby('Return Period')['Run_Time_Seconds'].quantile(0.99)

# Identify outliers above the 99th percentile
outliers_above_99 = []

for event in order:
    upper_bound = percentiles.loc[event]
    event_outliers = df[(df['Return Period'] == event) & (df['Run_Time_Seconds'] > upper_bound)]
    outliers_above_99.extend(event_outliers['Return Period'].tolist())

# Count the occurrences of each outlier
outlier_counts = Counter(outliers_above_99)

# Print outliers above the 99th percentile and their counts
print("Outliers Above 99th Percentile by Area:")
for area, count in outlier_counts.items():
    print(f"{area}: {count}")

# Prepare labels without 'H' and with a space after 'y'
formatted_labels = [label.replace('H', '').replace('y', 'y ') for label in order]

# Plotting
plt.figure(figsize=(16, 9))

# Use seaborn style for the plot
sns.set(style="whitegrid")

# Create a box plot with whiskers extending to the 1st and 99th percentiles
ax = sns.boxplot(x='Return Period', y='Run_Time_Seconds', data=df, color='#87ceeb', whis=[1, 99])

# Customize the plot
ax.set_xticks([i for i in range(len(order))])
ax.set_xticklabels(formatted_labels, rotation=45, ha='right', fontsize=16)

plt.yticks(fontsize=16)
plt.ylabel('Run Time (seconds)', fontsize=16)
plt.xlabel('')  # Remove x-label

# Tight layout for better spacing
plt.tight_layout()

# Save the plot to a file
plot_output_path = 'D:/Nationwide_Tsunami_Inundation/Plots/RunTime_BoxPlot_With_Percentiles.png'
plt.savefig(plot_output_path, dpi=400)

# Display the plot
plt.show()

#################################################################################################
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

# Load the CSV file
file_path = 'D:/Nationwide_Tsunami_Inundation/Inundation_Runtimes.csv'  # Replace with the correct path to your CSV file
df = pd.read_csv(file_path)

# Function to convert "0 days 02:24:44.269052" to seconds
def convert_to_seconds(time_str):
    days, time = time_str.split(' days ')
    days = int(days)
    hours, minutes, seconds = map(float, time.split(':'))
    total_seconds = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds).total_seconds()
    return total_seconds

# Apply the conversion to the 'Run_Time' column
df['Run_Time_Seconds'] = df['Run_Time'].apply(convert_to_seconds)

# Create the 'Return_Period' column based on 'turn_Peri' and 'percentile'
df['Return Period'] = df.apply(lambda row: f"H{int(row['Return_Period'])}y{int(row['Percentile'])}p", axis=1)

# Define the specific order for 'Return Period Event'
order = ['H100y50p', 'H250y50p', 'H500y50p', 
         'H1000y50p', 'H1500y50p', 'H2000y50p', 
         'H2500y50p']

# Convert 'Return_Period' to a categorical type with the specific order
df['Return Period'] = pd.Categorical(df['Return Period'], categories=order, ordered=True)

# Sort the DataFrame by 'Return Period'
df = df.sort_values('Return Period')

# Calculate the 99th percentile for each return period event
percentiles = df.groupby('Return Period')['Run_Time_Seconds'].quantile(0.99)

# Identify outliers above the 99th percentile
outliers_above_99 = []

for event in order:
    upper_bound = percentiles.loc[event]
    event_outliers = df[(df['Return Period'] == event) & (df['Run_Time_Seconds'] > upper_bound)]
    outliers_above_99.extend(event_outliers['Return Period'].tolist())

# Count the occurrences of each outlier
outlier_counts = Counter(outliers_above_99)

# Print outliers above the 99th percentile and their counts
print("Outliers Above 99th Percentile by Area:")
for area, count in outlier_counts.items():
    print(f"{area}: {count}")

# Prepare labels without 'H' and with a space after 'y'
formatted_labels = [label.replace('H', '').replace('y', 'y ') for label in order]

# Plotting
plt.figure(figsize=(16, 6))

# Use seaborn style for the plot
sns.set(style="whitegrid")

# Create a box plot with whiskers extending to the 1st and 99th percentiles, without plotting outliers
ax = sns.boxplot(x='Return Period', y='Run_Time_Seconds', data=df, color='#87ceeb', whis=[1, 99], showfliers=False)

# Customize the plot
ax.set_xticks([i for i in range(len(order))])
ax.set_xticklabels(formatted_labels, rotation=45, ha='right', fontsize=22)

plt.yticks(fontsize=20)
plt.ylabel('Run Time (seconds)', fontsize=22)
plt.xlabel('')  # Remove x-label

plt.ylim(0,2250)

# Tight layout for better spacing
plt.tight_layout()

# Save the plot to a file
plot_output_path = 'D:/Nationwide_Tsunami_Inundation/Plots/RunTime_BoxPlot_With_Percentiles_2.jpg'
plt.savefig(plot_output_path, dpi=400)

# Display the plot
plt.show()

####################################################################################################
# Calculate the sum of Run_Time_Seconds for each combination of Return_Period and Percentile
summed_runtime_df = df.groupby(['Return_Period', 'Percentile']).agg(
    Sum_Run_Time_Seconds=('Run_Time_Seconds', 'sum')
).reset_index()

# Calculate the mean of Run_Time_Seconds for each combination of Return_Period and Percentile
mean_runtime_df = df.groupby(['Return_Period', 'Percentile']).agg(
    Mean_Run_Time_Seconds=('Run_Time_Seconds', 'mean')
).reset_index()

# Calculate the mean of Run_Time_Seconds for each combination of Return_Period and Percentile
Median_runtime_df = df.groupby(['Return_Period', 'Percentile']).agg(
    Median_Run_Time_Seconds=('Run_Time_Seconds', 'median')
).reset_index()

# Merge the sum and mean DataFrames
combined_runtime_df = pd.merge(summed_runtime_df, mean_runtime_df, on=['Return_Period', 'Percentile'])

Total_Overall_Runtime = summed_runtime_df.Sum_Run_Time_Seconds.sum()

####################################################################################################
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Load the CSV file
file_path = 'D:/Nationwide_Tsunami_Inundation/Inundation_Runtimes.csv'  # Replace with the correct path to your CSV file
df = pd.read_csv(file_path)

# Function to convert "0 days 02:24:44.269052" to seconds
def convert_to_seconds(time_str):
    days, time = time_str.split(' days ')
    days = int(days)
    hours, minutes, seconds = map(float, time.split(':'))
    total_seconds = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds).total_seconds()
    return total_seconds

# Apply the conversion to the 'Run_Time' column
df['Run_Time_Seconds'] = df['Run_Time'].apply(convert_to_seconds)

# Create the 'Return Period' column based on 'Return_Period' and 'Percentile'
df['Return Period'] = df.apply(lambda row: f"H{int(row['Return_Period'])}y{int(row['Percentile'])}p", axis=1)

# Filter out only the 50p events
df_50p = df[df['Percentile'] == 50]

# Calculate the mean for the 50p events
means = df_50p.groupby('Return Period')['Run_Time_Seconds'].mean()

# Define the specific order for 'Return Period Event'
order = ['H100y50p', 'H250y50p', 'H500y50p', 'H1000y50p', 'H1500y50p', 'H2000y50p', 'H2500y50p']

# Convert 'Return_Period' to a categorical type with the specific order
df['Return Period'] = pd.Categorical(df['Return Period'], categories=order, ordered=True)

# Sort the DataFrame by 'Return Period'
df = df.sort_values('Return Period')

# Prepare labels without 'H' and with a space after 'y'
formatted_labels = [label.replace('H', '').replace('y50p', '') for label in order]

# Plotting
plt.figure(figsize=(16, 6))

# Use seaborn style for the plot
sns.set(style="whitegrid")

# Create a box plot with whiskers extending to the 1st and 99th percentiles, without plotting outliers
ax = sns.boxplot(x='Return Period', y='Run_Time_Seconds', data=df_50p, color='#87ceeb', whis=[1, 99], showfliers=False)

# Adjust the x-ticks and labels
ax.set_xticks([i for i in range(len(order))])
ax.set_xticklabels(formatted_labels, ha='center', fontsize=22)  # Align labels to the center

plt.yticks(fontsize=20)
plt.ylabel('Run Time (seconds)', fontsize=22)
plt.xlabel('Return Period (year)', fontsize=22)  # Remove x-label

plt.ylim(0, 2250)

# Plot the mean as a red line for the 50p events
for i, event in enumerate(order):
    mean_value = means.get(event, None)
    if mean_value is not None:
        plt.plot([i - 0.4, i + 0.4], [mean_value, mean_value], color='red', lw=2)

# Tight layout for better spacing
plt.tight_layout()

# Save the plot to a file
plot_output_path = 'D:/Nationwide_Tsunami_Inundation/Plots/RunTime_BoxPlot_With_50p_Means.jpg'
plt.savefig(plot_output_path, dpi=400)

plot_output_path = 'D:/Nationwide_Tsunami_Inundation/Plots/RunTime_BoxPlot_With_50p_Means.pdf'
plt.savefig(plot_output_path, dpi=400)

# Display the plot
plt.show()


###############################################################
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

# Load the CSV file
file_path = 'D:/Nationwide_Tsunami_Inundation/Inundation_Runtimes.csv'  # Replace with the correct path to your CSV file
df = pd.read_csv(file_path)

# Function to convert "0 days 02:24:44.269052" to seconds
def convert_to_seconds(time_str):
    days, time = time_str.split(' days ')
    days = int(days)
    hours, minutes, seconds = map(float, time.split(':'))
    total_seconds = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds).total_seconds()
    return total_seconds

# Apply the conversion to the 'Run_Time' column
df['Run_Time_Seconds'] = df['Run_Time'].apply(convert_to_seconds)

# Create the 'Return_Period' column based on 'Return_Period' and 'Percentile'
df['Return Period'] = df.apply(lambda row: f"H{int(row['Return_Period'])}y{int(row['Percentile'])}p", axis=1)

# Filter out only the 50p events
df_50p = df[df['Percentile'] == 50]

# Calculate the mean for the 50p events
means = df_50p.groupby('Return Period')['Run_Time_Seconds'].mean()

# Define the specific order for 'Return Period Event'
order = ['H100y50p', 'H250y50p', 'H500y50p', 'H1000y50p', 'H1500y50p', 'H2000y50p', 'H2500y50p']

# Convert 'Return_Period' to a categorical type with the specific order
df['Return Period'] = pd.Categorical(df['Return Period'], categories=order, ordered=True)

# Sort the DataFrame by 'Return Period'
df = df.sort_values('Return Period')

# Prepare labels without 'H' and with a space after 'y'
formatted_labels = [label.replace('H', '').replace('y', 'y ') for label in order]

# Plotting
plt.figure(figsize=(16, 6))

# Use seaborn style for the plot
sns.set(style="whitegrid")

# Set y-axis grid lines with bolder lines at specific points
ax.grid(True, which='both', axis='y', linestyle='-', color='lightgrey')
ax.axhline(y=1, color='black', linestyle='-', linewidth=1.5)  # Line at 1
ax.axhline(y=10, color='black', linestyle='-', linewidth=1.5)  # Line at 10
ax.axhline(y=100, color='black', linestyle='-', linewidth=1.5)  # Line at 100
ax.axhline(y=1000, color='black', linestyle='-', linewidth=1.5)  # Line at 1000

# Create a box plot with whiskers extending to the 1st and 99th percentiles, without plotting outliers
ax = sns.boxplot(x='Return Period', y='Run_Time_Seconds', data=df_50p, color='#87ceeb', whis=[1, 99], showfliers=False)

# Set y-axis to logarithmic scale
ax.set_yscale('log')

# Customize the plot
ax.set_xticks([i for i in range(len(order))])
ax.set_xticklabels(formatted_labels, ha='right', fontsize=22)

plt.yticks(fontsize=20)
plt.ylabel('Run Time (seconds)', fontsize=22)
plt.xlabel('')  # Remove x-label

plt.ylim(1, 3000)

# Plot the mean as a red line for the 50p events
for i, event in enumerate(order):
    mean_value = means.get(event, None)
    if mean_value is not None:
        plt.plot([i - 0.4, i + 0.4], [mean_value, mean_value], color='red', lw=2)

# Tight layout for better spacing
plt.tight_layout()

# Save the plot to a file
plot_output_path = 'D:/Nationwide_Tsunami_Inundation/Plots/RunTime_BoxPlot_With_50p_Means_Log.jpg'
plt.savefig(plot_output_path, dpi=400)

plot_output_path = 'D:/Nationwide_Tsunami_Inundation/Plots/RunTime_BoxPlot_With_50p_Means_Log.pdf'
plt.savefig(plot_output_path, dpi=400)

# Display the plot
plt.show()

###################################################################
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import ScalarFormatter

# Load the CSV file
file_path = 'D:/Nationwide_Tsunami_Inundation/Inundation_Runtimes.csv'  # Replace with the correct path to your CSV file
df = pd.read_csv(file_path)

# Function to convert "0 days 02:24:44.269052" to seconds
def convert_to_seconds(time_str):
    days, time = time_str.split(' days ')
    days = int(days)
    hours, minutes, seconds = map(float, time.split(':'))
    total_seconds = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds).total_seconds()
    return total_seconds

# Apply the conversion to the 'Run_Time' column
df['Run_Time_Seconds'] = df['Run_Time'].apply(convert_to_seconds)

# Create the 'Return_Period' column based on 'Return_Period' and 'Percentile'
df['Return Period'] = df.apply(lambda row: f"H{int(row['Return_Period'])}y{int(row['Percentile'])}p", axis=1)

# Filter out only the 50p events
df_50p = df[df['Percentile'] == 50]

# Calculate the mean for the 50p events
means = df_50p.groupby('Return Period')['Run_Time_Seconds'].mean()

# Define the specific order for 'Return Period Event'
order = ['H100y50p', 'H250y50p', 'H500y50p', 'H1000y50p', 'H1500y50p', 'H2000y50p', 'H2500y50p']

# Convert 'Return_Period' to a categorical type with the specific order
df['Return Period'] = pd.Categorical(df['Return Period'], categories=order, ordered=True)

# Sort the DataFrame by 'Return Period'
df = df.sort_values('Return Period')

# Extract the year values from the order for x-axis labels
formatted_labels = [label.replace('H', '').replace('y50p', '') for label in order]

# Plotting
plt.figure(figsize=(16, 6))
sns.set(style="whitegrid")

# Set y-axis grid lines with moderately bold lines at specific points
ax = plt.gca()
highlighted_lines = [1, 10, 100, 1000]  # The values for the bolder lines
for y in highlighted_lines:
    ax.axhline(y=y, color='grey', linestyle='-', linewidth=1)  # Set moderate thickness and lighter color

# Add regular grid lines in light grey
ax.grid(True, which='both', axis='y', linestyle='-', color='lightgrey', linewidth=0.5)

# Plot the box plot on top of the grid lines
sns.boxplot(x='Return Period', y='Run_Time_Seconds', data=df_50p, color='#87ceeb', whis=[1, 99], showfliers=False, order=order, ax=ax)

# Set y-axis to logarithmic scale
ax.set_yscale('log')

# Use plain scalar formatting for the y-axis
ax.yaxis.set_major_formatter(ScalarFormatter())
ax.yaxis.get_major_formatter().set_scientific(False)

# Customize the plot
ax.set_xticks([i for i in range(len(order))])
ax.set_xticklabels(formatted_labels, ha='center', fontsize=22)  # Center-align the labels
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)
plt.ylabel('Run Time (seconds)', fontsize=22)
plt.xlabel('Return Period (years)', fontsize=22)

plt.ylim(1, 3000)

# Plot the mean as a red line for the 50p events
for i, event in enumerate(order):
    mean_value = means.get(event, None)
    if mean_value is not None:
        plt.plot([i - 0.4, i + 0.4], [mean_value, mean_value], color='red', lw=2)

# Tight layout for better spacing
plt.tight_layout()

# Save the plot to a file
plot_output_path = 'D:/Nationwide_Tsunami_Inundation/Plots/RunTime_BoxPlot_With_50p_Means_Log_Seconds.jpg'
plt.savefig(plot_output_path, dpi=400)

plot_output_path = 'D:/Nationwide_Tsunami_Inundation/Plots/RunTime_BoxPlot_With_50p_Means_Log_Seconds.pdf'
plt.savefig(plot_output_path, dpi=400)

# Display the plot
plt.show()







