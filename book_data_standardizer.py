import pandas as pd
import re
import unicodedata
from typing import Dict, List, Tuple
import numpy as np

columns = ['ID', 'Title', 'Title_Std', 'Author', 'Author_Std', 'Price', 'Reviews', 
            'Score', 'Genre1', 'Genre1_Std', 'Genre2', 'Genre2_Std', 'Genre3', 
            'Genre3_Std', 'Genre4', 'Genre4_Std', 'Number_Of_Pages', 'Publisher', 
            'Publisher_Std', 'Cover_Type', 'Cover_Type_Std', 'Publishing_Date', 
            'Language', 'Language_Std', 'Translator']

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

def generate_book_id(store_initial: str, index: int) -> str:
    """Generate unique book ID with store initial and sequential number."""
    return f"{store_initial}{index:04d}"

def extract_author_from_title(title: str, author: str) -> Tuple[str, str]:
    """Remove author from title if present and return cleaned title and author."""
    if pd.isna(title) or pd.isna(author) or not isinstance(title, str) or not isinstance(author, str):
        return title, author
    
    # Clean and standardize for comparison
    clean_author = standardize_text(author)
    clean_title = standardize_text(title)
    
    # Check if author appears at start or end of title
    if clean_title.startswith(clean_author):
        title = title[len(author):].strip(' -:')
    elif clean_title.endswith(clean_author):
        title = title[:-len(author)].strip(' -:')
    
    return title, author

def convert_to_float(value: str) -> float:
    """Convert string to float, handling various formats and returning NaN for invalid values."""
    if pd.isna(value) or value == 'N/A':
        return np.nan
    try:
        # Remove any currency symbols and convert commas to dots
        clean_value = str(value).replace(',', '.').strip()
        clean_value = re.sub(r'[^\d.]', '', clean_value)
        return float(clean_value)
    except (ValueError, TypeError):
        return np.nan

def convert_to_int(value: str) -> int:
    """Convert string to integer by cutting off decimal part."""
    if pd.isna(value) or value == 'N/A':
        return np.nan
    try:
        # First convert to float to handle decimal numbers
        float_val = float(str(value).replace(',', '.').strip())
        # Then truncate decimal part
        return int(float_val)
    except (ValueError, TypeError):
        return np.nan

def standardize_bookline_data(filepath: str) -> pd.DataFrame:
    """Standardize Bookline data according to common format."""
    print("\nProcessing Bookline data...")
    
    # Read CSV and handle mixed types warning
    df = pd.read_csv(filepath, sep=';', low_memory=False)
    print(f"Found {len(df)} books in Bookline")
    
    # Generate IDs
    df['ID'] = [generate_book_id('B', i) for i in range(len(df))]
    
    # Clean title and author
    print("Cleaning titles and authors...")
    df[['Title', 'Author']] = df.apply(
        lambda x: extract_author_from_title(x['title'], x['author']), 
        axis=1, 
        result_type='expand'
    )
    
    # Create standardized fields
    df['Title_Std'] = df['Title'].apply(standardize_text)
    df['Author_Std'] = df['Author'].apply(standardize_text)
    
    # Map categories to genre fields (reversed order)
    print("Processing categories...")
    categories = df['category'].str.split('>', expand=True)
    if not categories.empty:
        num_categories = len(categories.columns)
        print(f"Found {num_categories} category levels")
        # Reverse the order of categories
        categories = categories[categories.columns[::-1]]
        for i in range(4):
            df[f'Genre{i+1}'] = categories[i] if i < len(categories.columns) else np.nan
            df[f'Genre{i+1}_Std'] = df[f'Genre{i+1}'].apply(standardize_text)
    
    # Convert numeric fields
    print("Converting numeric fields...")
    df['Price'] = df['price'].apply(convert_to_float)
    df['Score'] = df['score'].apply(convert_to_float)
    df['Reviews'] = df['reviews'].apply(convert_to_int)
    df['Number_Of_Pages'] = df['pages'].apply(convert_to_int)
    
    # Map remaining fields
    df['Publisher'] = df['publisher']
    df['Publisher_Std'] = df['Publisher'].apply(standardize_text)
    df['Cover_Type'] = df['edition']
    df['Cover_Type_Std'] = df['Cover_Type'].apply(standardize_text)
    df['Language'] = df['language']
    df['Language_Std'] = df['Language'].apply(standardize_text)
    df['Translator'] = 'N/A'
    df['Publishing_Date'] = 'N/A'
    
    # Print some statistics
    print("\nBookline Statistics:")
    print(f"Total books: {len(df)}")
    print(f"Unique authors: {df['Author'].nunique()}")
    print(f"Unique publishers: {df['Publisher'].nunique()}")
    print(f"Average price: {df['Price'].mean():.2f}")
    print(f"Average rating: {df['Score'].mean():.2f}")
    
    return df[columns]

def fix_carturesti_price(price: str) -> float:
    """Fix Carturesti prices that incorrectly start with zero."""
    if pd.isna(price) or price == 'N/A':
        return np.nan
    try:
        price_float = float(str(price).replace(',', '.').strip())
        if 0 < price_float < 1:  # If price starts with 0 (like 0.38)
            # Extract the first non-zero digit and create new price
            digits = str(price_float).replace('0.', '')
            return float(f"{digits}.{digits}")
        return price_float
    except (ValueError, TypeError):
        return np.nan

def standardize_carturesti_data(filepath: str) -> pd.DataFrame:
    """Standardize Carturesti data according to common format."""
    print("\nProcessing Carturesti data...")
    
    # Read CSV and handle mixed types warning
    df = pd.read_csv(filepath, sep=';', low_memory=False)
    print(f"Found {len(df)} books in Carturesti")
    
    # Generate IDs
    df['ID'] = [generate_book_id('C', i) for i in range(len(df))]
    
    # Clean title and author - using lowercase column names
    df[['Title', 'Author']] = df.apply(
        lambda x: extract_author_from_title(x['title'], x['author']), 
        axis=1, 
        result_type='expand'
    )
    
    # Create standardized fields
    df['Title_Std'] = df['Title'].apply(standardize_text)
    df['Author_Std'] = df['Author'].apply(standardize_text)
    
    # Map categories directly (already split)
    for i in range(1, 5):
        df[f'Genre{i}'] = df[f'category_{i}']
        df[f'Genre{i}_Std'] = df[f'Genre{i}'].apply(standardize_text)
    
    # Convert numeric fields with fixes
    df['Price'] = df['price'].apply(fix_carturesti_price)
    df['Score'] = df['score'].apply(convert_to_float)
    df['Reviews'] = df['reviews'].apply(convert_to_int)
    df['Number_Of_Pages'] = df['pages'].apply(convert_to_int)
    
    # Map remaining fields
    df['Publisher'] = df['publisher']
    df['Publisher_Std'] = df['Publisher'].apply(standardize_text)
    df['Cover_Type'] = df['edition']
    df['Cover_Type_Std'] = df['Cover_Type'].apply(standardize_text)
    df['Publishing_Date'] = df['publish_date']
    df['Language'] = df['language']
    df['Language_Std'] = df['Language'].apply(standardize_text)
    df['Translator'] = df['translator']
    
    # Print some statistics
    print("\nCarturesti Statistics:")
    print(f"Total books: {len(df)}")
    print(f"Unique authors: {df['Author'].nunique()}")
    print(f"Unique publishers: {df['Publisher'].nunique()}")
    print(f"Average price: {df['Price'].mean():.2f}")
    print(f"Average rating: {df['Score'].mean():.2f}")
    
    return df[columns]

def standardize_libris_data(filepath: str) -> pd.DataFrame:
    """Standardize Libris data according to common format."""
    print("\nProcessing Libris data...")
    
    # Read CSV and handle mixed types warning
    df = pd.read_csv(filepath, sep=';', low_memory=False)
    print(f"Found {len(df)} books in Libris")
    
    # Generate IDs
    df['ID'] = [generate_book_id('L', i) for i in range(len(df))]
    
    # Clean title and author
    df[['Title', 'Author']] = df.apply(
        lambda x: extract_author_from_title(x['title'], x['author']), 
        axis=1, 
        result_type='expand'
    )
    
    # Create standardized fields
    df['Title_Std'] = df['Title'].apply(standardize_text)
    df['Author_Std'] = df['Author'].apply(standardize_text)
    
    # Split categories into genres
    categories = df['categories'].str.split(',', expand=True)
    for i in range(4):
        df[f'Genre{i+1}'] = categories[i] if i < len(categories.columns) else np.nan
        df[f'Genre{i+1}_Std'] = df[f'Genre{i+1}'].apply(standardize_text)
    
    # Convert numeric fields
    df['Price'] = df['price'].apply(convert_to_float)
    df['Score'] = df['average_score'].apply(convert_to_float)
    df['Reviews'] = df['votes'].apply(convert_to_int)
    df['Number_Of_Pages'] = df['num_pages'].apply(convert_to_int)
    df['Publishing_Date'] = df['publication_year'].apply(convert_to_int)
    
    # Map remaining fields
    df['Publisher'] = df['publisher']
    df['Publisher_Std'] = df['Publisher'].apply(standardize_text)
    df['Cover_Type'] = df['cover_type']
    df['Cover_Type_Std'] = df['Cover_Type'].apply(standardize_text)
    df['Language'] = 'N/A'
    df['Language_Std'] = df['Language'].apply(standardize_text)
    df['Translator'] = 'N/A'
    
    # Print some statistics
    print("\nLibris Statistics:")
    print(f"Total books: {len(df)}")
    print(f"Unique authors: {df['Author'].nunique()}")
    print(f"Unique publishers: {df['Publisher'].nunique()}")
    print(f"Average price: {df['Price'].mean():.2f}")
    print(f"Average rating: {df['Score'].mean():.2f}")
    
    return df[columns]

def create_unique_lists(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Create unique lists for Authors, Categories, Publishers, and Formats."""
    unique_lists = {
        'authors': pd.DataFrame({
            'Author': pd.Series(df['Author'].dropna().unique()),
            'Author_Std': pd.Series(df['Author_Std'].dropna().unique())
        }),
        'publishers': pd.DataFrame({
            'Publisher': pd.Series(df['Publisher'].dropna().unique()),
            'Publisher_Std': pd.Series(df['Publisher_Std'].dropna().unique())
        }),
        'formats': pd.DataFrame({
            'Format': pd.Series(df['Cover_Type'].dropna().unique()),
            'Format_Std': pd.Series(df['Cover_Type_Std'].dropna().unique())
        })
    }
    
    # Handle categories separately as they're spread across multiple columns
    all_categories = []
    for i in range(1, 5):
        all_categories.extend(df[f'Genre{i}'].dropna().unique())
    
    unique_lists['categories'] = pd.DataFrame({
        'Category': pd.Series(list(set(all_categories))),
        'Category_Std': pd.Series(list(set(all_categories))).apply(standardize_text)
    })
    
    return unique_lists

def save_unique_lists(unique_lists: Dict[str, pd.DataFrame], output_dir: str):
    """Save unique lists to CSV files."""
    for name, df in unique_lists.items():
        df.to_csv(f'{output_dir}/{name}.csv', index=False, encoding='utf-8')

# Modify the main execution to include overall statistics
if __name__ == "__main__":
    print("Starting data standardization process...")
    
    # Standardize data from each source
    bookline_df = standardize_bookline_data('Data\Bookline\\book_details.csv')
    print("Saving Bookline standardized data...")
    bookline_df.to_csv('Data\Bookline\standardized.csv')
    
    carturesti_df = standardize_carturesti_data('Data\Carturesti\\book_details_unique.csv')
    print("Saving Carturesti standardized data...")
    carturesti_df.to_csv('Data\Carturesti\standardized.csv')
    
    libris_df = standardize_libris_data('Data\Libris\\book_details_unique.csv')
    print("Saving Libris standardized data...")
    libris_df.to_csv('Data\Libris\standardized.csv')
    
    # Combine all data
    print("\nCombining all data...")
    all_books = pd.concat([bookline_df, carturesti_df, libris_df], ignore_index=True)
    
    # Print overall statistics
    print("\nOverall Statistics:")
    print(f"Total books: {len(all_books)}")
    print(f"Books per store:")
    print(f"  Bookline: {len(bookline_df)}")
    print(f"  Carturesti: {len(carturesti_df)}")
    print(f"  Libris: {len(libris_df)}")
    print(f"Unique authors across all stores: {all_books['Author'].nunique()}")
    print(f"Unique publishers across all stores: {all_books['Publisher'].nunique()}")
    print(f"Average price across all stores: {all_books['Price'].mean():.2f}")
    
    # Create and save unique lists
    print("\nCreating unique lists...")
    unique_lists = create_unique_lists(all_books)
    print("Saving unique lists...")
    save_unique_lists(unique_lists, 'Data')
    
    # Save standardized data
    print("Saving combined standardized data...")
    all_books.to_csv('Data/standardized_books.csv', index=False, encoding='utf-8')
    
    print("\nData standardization complete!") 