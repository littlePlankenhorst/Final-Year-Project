import pandas as pd
import os

def remove_duplicates():
    input_file = 'Data/Libris/book_details.csv'
    output_file = 'Data/Libris/book_details_unique.csv'
    
    print("Reading CSV file...")
    # Read CSV with semicolon delimiter
    df = pd.read_csv(input_file, delimiter=';')
    
    # Get initial count
    initial_count = len(df)
    print(f"Initial number of records: {initial_count}")
    
    # Remove duplicates based on title and author
    print("Removing duplicates...")
    df_unique = df.drop_duplicates(subset=['title', 'author', 'price'], keep='first')
    
    # Get final count
    final_count = len(df_unique)
    duplicates_removed = initial_count - final_count
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Final number of records: {final_count}")
    
    # Save to new CSV file
    print(f"Saving to {output_file}...")
    df_unique.to_csv(output_file, index=False, sep=';')
    print("Done!")
    
    # Print some statistics
    if duplicates_removed > 0:
        duplicate_percentage = (duplicates_removed / initial_count) * 100
        print(f"\nStatistics:")
        print(f"Duplicate percentage: {duplicate_percentage:.2f}%")
        print(f"Data reduction: {duplicates_removed} rows")

if __name__ == "__main__":
    remove_duplicates() 