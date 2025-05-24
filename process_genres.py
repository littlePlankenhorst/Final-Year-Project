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

def generate_category_id(genres: List[str]) -> str:
    """Generate category ID from genre list by taking first two characters of each genre."""
    if not genres or all(pd.isna(g) for g in genres):
        return 'N/A'
    
    # Take first two characters of each non-empty genre
    id_parts = []
    for genre in genres:
        if pd.notna(genre) and isinstance(genre, str):
            # Take first two characters, handle special characters
            first_two = ''.join(c for c in genre[:6] if c.isalnum())
            if first_two:
                id_parts.append(first_two)
    
    return ''.join(id_parts) if id_parts else 'N/A'

def process_genres():
    """Process standardized files and update genres based on genresStandard.csv."""
    print("Starting genre processing...")
    
    # Read the genre mapping file
    genre_mapping = pd.read_csv('Clustering/genresStandard.csv', sep=';', low_memory=False)
    # Create a dictionary for quick lookup (reverse mapping)
    mapping_dict = dict(zip(genre_mapping.iloc[:, 0], genre_mapping.iloc[:, 1]))
    
    print(f"Found {len(mapping_dict)} genre mappings")
    
    # Process each target file
    target_files = [
        'Data\Libris\standardized.csv',
        'Data\Carturesti\standardized.csv'
    ]
    
    for file_path in target_files:
        print(f"\nProcessing {file_path}...")
        
        # Read the target file
        df = pd.read_csv(file_path, sep=';', low_memory=False)
        print(f"Found {len(df)} books to process")
        
        # Process each genre column
        for i in range(1, 7):
            col_name = f'Genre{i}'
            if col_name in df.columns:
                # Convert to string and handle NaN values
                df[col_name] = df[col_name].astype(str).replace('nan', np.nan)
                
                # Apply mapping and split
                df[col_name] = df[col_name].apply(
                    lambda x: mapping_dict.get(x, x) if pd.notna(x) else x
                )
        
        # Now split the mapped values and distribute to appropriate columns
        for idx, row in df.iterrows():
            # Get the mapped value from Genre1 or Genre2 if Genre1 is "Carte"
            mapped_value = row['Genre2'] if row['Genre1'] == "Carte" else row['Genre1']
            
            if pd.notna(mapped_value):
                # Split the mapped value
                split_genres = str(mapped_value).split('>')
                # Clear all genre columns first
                for i in range(1, 7):
                    df.at[idx, f'Genre{i}'] = np.nan
                # Set Genre1 to "Könyv"
                df.at[idx, 'Genre1'] = "Könyv"
                # Fill remaining genres
                for i, genre in enumerate(split_genres, 2):
                    if i <= 6:  # Only fill up to Genre6
                        df.at[idx, f'Genre{i}'] = genre.strip()
            else:
                # Keep the original values if both Genre1 and Genre2 are NaN
                for i in range(1, 7):
                    df.at[idx, f'Genre{i}'] = row[f'Genre{i}']
        
        # Set first and last genre after processing
        df['First_Genre'] = df['Genre2']
        df['Last_Genre'] = df.apply(
            lambda x: next((x[f'Genre{i}'] for i in range(6, 0, -1) if not pd.isna(x[f'Genre{i}'])), np.nan),
            axis=1
        )
        
        # Generate category IDs after all genre processing is complete
        df['Category_ID'] = df.apply(
            lambda x: generate_category_id([x['Genre1'], x['Genre2'], x['Genre3'], 
                                          x['Genre4'], x['Genre5'], x['Genre6']]),
            axis=1
        )
        
        # Save the updated data
        print("Saving updated data...")
        df.to_csv(file_path, index=False, sep=';', encoding='utf-8')
        
        # Print statistics
        print("\nGenre Processing Statistics:")
        print(f"Total books processed: {len(df)}")
        for i in range(1, 7):
            col_name = f'Genre{i}'
            if col_name in df.columns:
                print(f"Unique genres in {col_name}: {df[col_name].nunique()}")
                print(f"Sample of {col_name}:")
                print(df[col_name].head())
    
    print("\nGenre processing complete!")

if __name__ == "__main__":
    process_genres() 