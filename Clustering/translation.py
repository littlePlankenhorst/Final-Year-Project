import csv

# Define the input and output file paths
input_file_path = 'Clustering\standCart.txt'
output_file_path = 'Clustering/standCart.csv'

# Read the input file and process the data
with open(input_file_path, 'r', encoding='utf-8') as infile:
    lines = infile.readlines()

# Prepare the data for CSV
csv_data = []
for line in lines:
    # Strip whitespace and split the line by '|'
    parts = line.strip().split('**')
    if len(parts) >= 2:
        # Extract the relevant fields and strip extra spaces
        ro = parts[1].strip()
        hu = parts[3].strip()
        csv_data.append([ro, hu])

# Write the processed data to a new CSV file
with open(output_file_path, 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.writer(outfile,  delimiter=';')
    writer.writerow(['RO', 'HU'])  # Write the header
    writer.writerows(csv_data)      # Write the data rows

print(f"Data has been transformed and saved to {output_file_path}.")