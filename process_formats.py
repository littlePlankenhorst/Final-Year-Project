import pandas as pd
import re
import unicodedata
from typing import Dict, List, Tuple
import numpy as np

def remove_accents(text: str) -> str:
    """Remove accents from text while preserving base characters."""
    if pd.isna(text) or not isinstance(text, str):
        return text
    return ''.join(c for c in unicodedata.normalize('NFKD', text)
                  if unicodedata.category(c) != 'Mn')

def standardize_text(text: str) -> str:
    """Convert text to lowercase and remove special characters."""
    if pd.isna(text) or not isinstance(text, str):
        return text
    # Remove accents first
    text = remove_accents(text)
    # Convert to lowercase and remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    return text

def process_formats():
    """Process standardized_books.csv and update formats based on formatStandard.csv."""
    print("Starting format processing...")
    
    # Read the input files
    books_df = pd.read_csv('Data/standardized_books.csv', sep=';', low_memory=False)
    format_df = pd.read_csv('Clustering/formatStandard.csv', sep=';', low_memory=False)
    
    print(f"Found {len(books_df)} books to process")
    print(f"Found {len(format_df)} format mappings")
    
    # Create a dictionary for quick lookup of format mappings
    format_mapping = {}
    for _, row in format_df.iterrows():
        format_mapping[row['Formatum']] = row['StandardFormatum']
    
    # Process each book
    for idx, row in books_df.iterrows():
        cover_type = row['Cover_Type']
        
        # Skip if no cover type or not in mapping
        if pd.isna(cover_type) or cover_type not in format_mapping:
            continue
            
        # Get the mapped format
        mapped_format = format_mapping[cover_type]
        
        # Update the book's cover type
        books_df.at[idx, 'Cover_Type'] = mapped_format
        
        # Update standardized version
        books_df.at[idx, 'Cover_Type_Std'] = standardize_text(mapped_format)
    
    # Save the updated data
    print("Saving updated data...")
    books_df.to_csv('Data/standardized_books.csv', index=False, sep=';', encoding='utf-8')
    
    # Print statistics
    print("\nFormat Processing Statistics:")
    print(f"Total books processed: {len(books_df)}")
    print(f"Books with updated formats: {len(books_df[~books_df['Cover_Type'].isna()])}")
    print(f"Unique formats: {books_df['Cover_Type'].nunique()}")
    
    print("\nFormat processing complete!")

if __name__ == "__main__":
    process_formats() 