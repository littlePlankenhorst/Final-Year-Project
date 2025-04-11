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

def process_genres():
    """Process standardized_books.csv and update genres based on clusteredGenre.csv."""
    print("Starting genre processing...")
    
    # Read the input files
    books_df = pd.read_csv('Data/standardized_books.csv', sep=';', low_memory=False)
    clustered_df = pd.read_csv('Clustering/clusteredGenre.csv', sep=';', low_memory=False)
    
    print(f"Found {len(books_df)} books to process")
    print(f"Found {len(clustered_df)} genre mappings")
    
    # Create a dictionary for quick lookup of genre mappings
    genre_mapping = {}
    for _, row in clustered_df.iterrows():
        genre_mapping[row['Genre1_Std']] = (row['Genre'], row['SubGenre'])
    
    # Process each book
    for idx, row in books_df.iterrows():
        genre1_std = row['Genre1_Std']
        
        # Skip if no genre or not in mapping
        if pd.isna(genre1_std) or genre1_std not in genre_mapping:
            continue
            
        # Get the mapped genre and subgenre
        mapped_genre, mapped_subgenre = genre_mapping[genre1_std]
        
        # Update the book's genres
        books_df.at[idx, 'Genre1'] = mapped_genre
        books_df.at[idx, 'Genre2'] = mapped_subgenre
        
        # Update standardized versions
        books_df.at[idx, 'Genre1_Std'] = standardize_text(mapped_genre)
        books_df.at[idx, 'Genre2_Std'] = standardize_text(mapped_subgenre)
    
    # Save the updated data
    print("Saving updated data...")
    books_df.to_csv('Data/standardized_books.csv', index=False, sep=';', encoding='utf-8')
    
    # Print statistics
    print("\nGenre Processing Statistics:")
    print(f"Total books processed: {len(books_df)}")
    print(f"Books with updated genres: {len(books_df[~books_df['Genre1'].isna()])}")
    print(f"Unique main genres: {books_df['Genre1'].nunique()}")
    print(f"Unique subgenres: {books_df['Genre2'].nunique()}")
    
    print("\nGenre processing complete!")

if __name__ == "__main__":
    process_genres() 