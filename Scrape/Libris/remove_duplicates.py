def remove_duplicates(input_file, output_file):
    # Dictionary to store unique titles and their corresponding full lines
    seen_titles = {}
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Split only on first two commas to get the title
            parts = line.split(',', 2)
            if len(parts) >= 3:
                title = parts[2].strip()
                # Keep only the first occurrence of each title
                if title not in seen_titles:
                    seen_titles[title] = line

    # Write unique lines to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        # Sort by original line order (using the full line as stored)
        for line in seen_titles.values():
            f.write(line)

# Use the function
remove_duplicates('Data/Libris\libris_titles.txt', 'Data/Libris\libris_titles_unique.txt')