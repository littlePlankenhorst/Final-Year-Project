import pandas as pd
import re
import unicodedata
from typing import Dict, List, Tuple
import numpy as np

columns = ['ID', 'Title', 'Title_Std', 'Author', 'Author_Std', 'Price', 'Reviews', 
            'Score', 'Number_Of_Pages', 'Genre1', 'Genre2', 'Genre3', 'Genre4', 'Genre5', 'Genre6',
            'First_Genre', 'Last_Genre', 'Category_ID', 'Publisher', 'Publisher_Std', 
            'Cover_Type', 'Publishing_Date', 'Language', 'Translator']

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

def convert_to_clean_int(value: any) -> int:
    """Convert value to clean integer without decimal part."""
    if pd.isna(value) or value == 'N/A':
        return np.nan
    try:
        # First convert to float to handle any format
        float_val = float(str(value).replace(',', '.').strip())
        # Convert to int to remove decimal part
        return int(float_val)
    except (ValueError, TypeError):
        return np.nan

def extract_publisher_and_year(publisher_text: str) -> Tuple[str, str]:
    """Extract publisher name and year from Bookline publisher field."""
    if pd.isna(publisher_text) or not isinstance(publisher_text, str):
        return publisher_text, 'N/A'
    
    # Split by comma and take only the publisher part
    parts = publisher_text.split(',')
    if len(parts) > 1:
        publisher = parts[0].strip()
        # Try to extract year from the remaining part
        year_match = re.search(r'\d{4}', parts[1])
        year = year_match.group().strip() if year_match else 'N/A'
        return publisher, year
    return publisher_text, 'N/A'

def clean_number(value: str) -> str:
    """Remove .0 from number strings."""
    if pd.isna(value) or value == 'N/A':
        return value
    # Check if string ends with .0
    if str(value).endswith('.0'):
        return str(value)[:-2]
    return str(value)

def process_bookline_categories(category_str: str) -> Tuple[List[str], str, str]:
    """Process Bookline categories string into list of categories and extract first/last."""
    if pd.isna(category_str):
        return [np.nan] * 6, np.nan, np.nan
    
    # Split by > and clean each category
    categories = [cat.strip() for cat in str(category_str).split('>')]
    
    # Get first and last genre
    first_genre = categories[1] if categories else np.nan
    last_genre = categories[-1] if categories else np.nan
    
    # Pad with NaN if needed
    while len(categories) < 6:
        categories.append(np.nan)
    
    return categories[:6], first_genre, last_genre  # Return first 6 categories and first/last

def handle_invalid_format(cover_type: str) -> str:
    """Return 'N/A' if format is invalid, otherwise return the original format."""
    if pd.isna(cover_type) or not isinstance(cover_type, str):
        return 'N/A'
    
    # Check if contains ISBN or starts with number
    if 'ISBN' in cover_type or re.match(r'^\d', cover_type):
        return 'N/A'
    return cover_type

def trim_string(text: str) -> str:
    """Remove leading and trailing whitespace from text."""
    if pd.isna(text) or not isinstance(text, str):
        return text
    return text.strip()

def generate_category_id(genres: List[str]) -> str:
    """Generate category ID from genre list by taking first two characters of each genre."""
    if not genres or all(pd.isna(g) for g in genres):
        return 'N/A'
    
    # Take first two characters of each non-empty genre
    id_parts = []
    for genre in reversed(genres):
        if pd.notna(genre) and isinstance(genre, str):
            # Take first two characters, handle special characters
            first_two = ''.join(c for c in genre[:6] if c.isalnum())
            if first_two:
                id_parts.append(first_two)
    
    return ''.join(id_parts) if id_parts else 'N/A'

def standardize_bookline_data(filepath: str) -> pd.DataFrame:
    """Standardize Bookline data according to common format."""
    print("\nProcessing Bookline data...")
    
    # Read CSV and handle mixed types warning
    df = pd.read_csv(filepath, sep=';', low_memory=False)
    print(f"Found {len(df)} books in Bookline")
    
    # Trim all string columns
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(trim_string)
    
    # Filter out non-book records and save them
    non_books = df[~df['category'].str.contains('Könyv', na=False)]
    if len(non_books) > 0:
        print(f"Found {len(non_books)} non-book records")
        non_books.to_csv('Data/noBook.csv', index=False, sep=';', encoding='utf-8')
        print("Saved non-book records to noBook.csv")
    
    # Keep only book records
    df = df[df['category'].str.contains('Könyv', na=False)]
    print(f"Processing {len(df)} book records")
    
    # Generate IDs
    df['ID'] = [generate_book_id('B', i) for i in range(len(df))]
    
    # Clean title and author
    print("Cleaning titles and authors...")
    df[['Title', 'Author']] = df.apply(
        lambda x: extract_author_from_title(x['title'], x['author']), 
        axis=1, 
        result_type='expand'
    )
    
    # Clean Bookline authors according to new rules
    def clean_bookline_author(author: str) -> str:
        if pd.isna(author) or not isinstance(author, str):
            return author
            
        # Remove content in brackets
        author = re.sub(r'\([^)]*\)', '', author)
        
        # Remove special cases
        author = author.replace('...', '')
        author = author.replace('SZERZŐ', '')
        author = author.replace('Szerkesztette:', '')
        author = author.replace('Szerkesztette', '')
        author = author.replace('Összeállította', '')
        author = author.replace('Össz.:', '')
        author = author.replace('Össz.', '')
        
        # Split by 'és' or 'and' and join with comma
        author = re.sub(r'\s+és\s+', ', ', author)
        author = re.sub(r'\s+and\s+', ', ', author)
        
        # Remove numbers
        author = re.sub(r'\d+', '', author)
        
        # Remove names starting with non-capital letters (except special cases)
        words = author.split()
        cleaned_words = []
        for word in words:
            if (word[0].isupper() or 
                word.lower() in ['von', 'van', 'der', 'de', 'gróf', 'dr'] or
                word.lower().startswith('van der')):
                cleaned_words.append(word)
        author = ' '.join(cleaned_words)
        
        return trim_string(author)
    
    # Apply author cleaning
    df['Author'] = df['Author'].apply(clean_bookline_author)
    
    # Create standardized fields
    df['Title_Std'] = df['Title'].apply(standardize_text)
    df['Author_Std'] = df['Author'].apply(standardize_text)
    
    # Extract publisher and year
    print("Extracting publisher and year...")
    df[['Publisher', 'Publishing_Date']] = df.apply(
        lambda x: extract_publisher_and_year(x['publisher']),
        axis=1,
        result_type='expand'
    )
    # Standardize publisher (after removing year)
    df['Publisher_Std'] = df['Publisher'].apply(standardize_text)
    
    # Process categories
    print("Processing categories...")
    category_results = df['category'].apply(process_bookline_categories)
    df[['Genre1', 'Genre2', 'Genre3', 'Genre4', 'Genre5', 'Genre6']] = pd.DataFrame(
        [r[0] for r in category_results],
        index=df.index
    )
    df['First_Genre'] = [r[1] for r in category_results]
    df['Last_Genre'] = [r[2] for r in category_results]
    
    # Generate category IDs and create mapping
    print("Generating category IDs...")
    df['Category_ID'] = df.apply(
        lambda x: generate_category_id([x['Genre1'], x['Genre2'], x['Genre3'], 
                                      x['Genre4'], x['Genre5'], x['Genre6']]),
        axis=1
    )
    
    # Create and save category mapping
    category_mapping = df[['Category_ID', 'category']].drop_duplicates()
    category_mapping.columns = ['Category_ID', 'Category_Path']
    category_mapping.to_csv('Data/category_mapping.csv', index=False, sep=';', encoding='utf-8')
    print(f"Saved {len(category_mapping)} unique category mappings to category_mapping.csv")
    
    # Convert numeric fields
    print("Converting numeric fields...")
    df['Score'] = df['score'].apply(convert_to_float)
    df['Reviews'] = df['reviews'].apply(convert_to_clean_int)
    df['Number_Of_Pages'] = df['pages'].apply(convert_to_clean_int).apply(clean_number)
    df['Publishing_Date'] = df['Publishing_Date'].apply(clean_number)
    df['Price'] = df['price'].apply(convert_to_float)  # Map price from input data
    
    # Map remaining fields
    df['Cover_Type'] = df['edition'].apply(handle_invalid_format)
    # Remove "Szállító" from cover types
    df['Cover_Type'] = df['Cover_Type'].apply(lambda x: 'N/A' if pd.isna(x) or not isinstance(x, str) or x.startswith('Szállító') else x)
    df['Language'] = df['language'].apply(lambda x: 'magyar' if pd.notna(x) and str(x).lower() == 'magyar' else '')
    df['Translator'] = 'N/A'
    
    # Trim all string columns in the final output
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(trim_string)
    
    return df[columns]

def extract_unique_per_store(df: pd.DataFrame, store_prefix: str, columns: List[str]) -> Dict[str, pd.DataFrame]:
    """Extract unique values for specified columns from a store's dataframe."""
    store_df = df[df['ID'].str.startswith(store_prefix)]
    unique_dfs = {}
    
    for col in columns:
        if col in store_df.columns:
            # Get both original and standardized columns if available
            std_col = f"{col}_Std" if f"{col}_Std" in store_df.columns else None
            
            if std_col:
                unique_df = store_df[[col, std_col]].drop_duplicates()
            else:
                unique_df = pd.DataFrame({col: store_df[col].unique()})
            
            unique_dfs[col.lower()] = unique_df
    
    return unique_dfs

def save_unique_per_store(unique_dfs: Dict[str, pd.DataFrame], store_name: str, output_dir: str):
    """Save unique dataframes to CSV files for a specific store."""
    for name, df in unique_dfs.items():
        df.to_csv(f'{output_dir}/{store_name}_{name}.csv', index=False, encoding='utf-8', sep=';')

def standardize_carturesti_data(filepath: str) -> pd.DataFrame:
    """Standardize Carturesti data according to common format."""
    print("\nProcessing Carturesti data...")
    
    # Read CSV and handle mixed types warning
    df = pd.read_csv(filepath, sep=';', low_memory=False)
    print(f"Found {len(df)} books in Carturesti")
    
    # Trim all string columns
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(trim_string)
    
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
    for i in range(1, 7):
        df[f'Genre{i}'] = df[f'category_{i}'] if f'category_{i}' in df.columns else np.nan
    
    # Set first and last genre
    df['First_Genre'] = df['Genre1']
    df['Last_Genre'] = df.apply(
        lambda x: next((x[f'Genre{i}'] for i in range(6, 0, -1) if not pd.isna(x[f'Genre{i}'])), np.nan),
        axis=1
    )
    
    # Convert numeric fields with fixes
    df['Score'] = df['score'].apply(convert_to_float).apply(lambda x: round(x/2, 1) if not pd.isna(x) else x)
    df['Reviews'] = df['reviews'].apply(convert_to_clean_int)
    df['Number_Of_Pages'] = df['pages'].apply(convert_to_clean_int).apply(clean_number)
    df['Price'] = df['price'].apply(convert_to_float)  # Map price from input data
    
    # Process language field for cover type and publishing date
    def process_language_field(lang: str, current_cover_type: str, current_pub_date: str) -> Tuple[str, str]:
        if pd.isna(lang) or not isinstance(lang, str):
            return current_cover_type, current_pub_date
            
        # Check for cover type keywords
        cover_keywords = [
            "hajtogatott", "irkafűzött", "kapcsos", "kartonált", "kasírozott",
            "kemény", "keménytábla", "kötve", "lapozó", "leporelló", "műanyag",
            "műbőr", "nylon", "puhatáblás", "spirál", "Spirál", "szabadlapos",
            "vászon", "bőr", "velúr", "borító", "díszdobozban", "díszkötésben",
            "tokban", "félbőr", "félkarton", "félműbőr", "félvászon", "flexi",
            "fűzve", "gyűrűs mappa"
        ]
        
        # Check for publishing date
        year_match = re.search(r'Gyártási év:\s*(\d{4})', lang)
        year = year_match.group(1) if year_match else current_pub_date
        
        # Check for invalid content
        invalid_keywords = [
            "Korhatár", "Korhatárra", "hibátlan", "hangoskönyv", "könyv",
            "rajzaival", "mappában", "CD", "plüss", "Rajzolta", "Windows",
            "térkép", "Típus", "cm", "pdf", "mobi", "ISBN", "Infinity", "kártya"
        ]
        
        # If any invalid keyword is found, return original values
        if any(keyword in lang for keyword in invalid_keywords):
            return current_cover_type, current_pub_date
            
        # Extract cover type if any keyword is found
        cover_type = current_cover_type
        for keyword in cover_keywords:
            if keyword in lang:
                cover_type = keyword
                break
                
        return trim_string(cover_type), trim_string(year)
    
    # Process language field and update cover type and publishing date
    df[['Cover_Type', 'Publishing_Date']] = pd.DataFrame(
        df.apply(lambda x: process_language_field(x['language'], x['edition'], x['publish_date']), axis=1).tolist(),
        index=df.index
    )
    
    # Map remaining fields
    df['Publisher'] = df['publisher']
    df['Publisher_Std'] = df['Publisher'].apply(standardize_text)
    df['Language'] = df['language']
    df['Translator'] = df['translator']
    
    # Generate category IDs
    df['Category_ID'] = df.apply(
        lambda x: generate_category_id([x['Genre1'], x['Genre2'], x['Genre3'], 
                                      x['Genre4'], x['Genre5'], x['Genre6']]),
        axis=1
    )
    
    # Trim all string columns in the final output
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(trim_string)
    
    return df[columns]

def standardize_libris_data(filepath: str) -> pd.DataFrame:
    """Standardize Libris data according to common format."""
    print("\nProcessing Libris data...")
    
    # Read CSV and handle mixed types warning
    df = pd.read_csv(filepath, sep=';', low_memory=False)
    print(f"Found {len(df)} books in Libris")
    
    # Trim all string columns
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(trim_string)
    
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
    for i in range(6):
        df[f'Genre{i+1}'] = categories[i] if i < len(categories.columns) else np.nan
    
    # Set first and last genre
    df['First_Genre'] = df['Genre1']
    df['Last_Genre'] = df.apply(
        lambda x: next((x[f'Genre{i}'] for i in range(6, 0, -1) if not pd.isna(x[f'Genre{i}'])), np.nan),
        axis=1
    )
    
    # Convert numeric fields
    df['Score'] = df['average_score'].apply(convert_to_float)
    df['Reviews'] = df['votes'].apply(convert_to_clean_int)
    df['Number_Of_Pages'] = df['num_pages'].apply(convert_to_clean_int).apply(clean_number)
    df['Publishing_Date'] = df['publication_year'].apply(convert_to_clean_int).apply(clean_number)
    df['Price'] = df['price'].apply(convert_to_float)  # Map price from input data
    
    # Map remaining fields
    df['Publisher'] = df['publisher']
    df['Publisher_Std'] = df['Publisher'].apply(standardize_text)
    df['Cover_Type'] = df['cover_type'].apply(handle_invalid_format)
    df['Language'] = 'N/A'
    df['Translator'] = 'N/A'
    
    # Generate category IDs
    df['Category_ID'] = df.apply(
        lambda x: generate_category_id([x['Genre1'], x['Genre2'], x['Genre3'], 
                                      x['Genre4'], x['Genre5'], x['Genre6']]),
        axis=1
    )
    
    # Trim all string columns in the final output
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(trim_string)
    
    return df[columns]

def create_unique_lists(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Create unique lists for Authors, Categories, Publishers, and Formats."""
    # Handle authors - keep first occurrence of each standardized author
    authors_df = pd.DataFrame({
        'Author': df['Author'],
        'Author_Std': df['Author_Std']
    }).drop_duplicates(subset=['Author_Std'], keep='first')
    
    publishers_df = pd.DataFrame({
        'Publisher': df['Publisher'],
        'Publisher_Std': df['Publisher_Std']
    }).drop_duplicates()
    
    # Handle formats - exclude N/A and "Szállító"
    formats_df = pd.DataFrame({
        'Format': df['Cover_Type'],
        'Format_Std': df['Cover_Type'].apply(lambda x: 'N/A' if x == 'N/A' else 'Szállító')
    })
    formats_df = formats_df[
        (formats_df['Format'] != 'N/A') & 
        ~formats_df['Format'].str.contains('Szállító', na=False)
    ].drop_duplicates()
    
    # Handle categories - clean spaces and drop duplicates
    all_categories = []
    for i in range(1, 7):
        valid_categories = df[['Genre' + str(i)]].dropna()
        all_categories.extend(valid_categories['Genre' + str(i)].str.strip())
    
    categories_df = pd.DataFrame({
        'Category': pd.Series(all_categories)
    }).drop_duplicates()
    
    return {
        'authors': authors_df,
        'publishers': publishers_df,
        'formats': formats_df,
        'categories': categories_df
    }

def save_unique_lists(unique_lists: Dict[str, pd.DataFrame], output_dir: str):
    """Save unique lists to CSV files."""
    for name, df in unique_lists.items():
        df.to_csv(f'{output_dir}/{name}.csv', index=False, encoding='utf-8', sep=';')

# Modify the main execution
if __name__ == "__main__":
    print("Starting data standardization process...")
    
    # Standardize data from each source
    bookline_df = standardize_bookline_data('Data\Bookline\\Book_details_unique.csv')
    print("Saving Bookline standardized data...")
    bookline_df.to_csv('Data\Bookline\standardized.csv', sep=';')
    
    carturesti_df = standardize_carturesti_data('Data\Carturesti\\book_details_unique.csv')
    print("Saving Carturesti standardized data...")
    carturesti_df.to_csv('Data\Carturesti\standardized.csv', sep=';')
    
    libris_df = standardize_libris_data('Data\Libris\\book_details_unique.csv')
    print("Saving Libris standardized data...")
    libris_df.to_csv('Data\Libris\standardized.csv', sep=';')
    
    # Combine all data
    print("\nCombining all data...")
    all_books = pd.concat([bookline_df, carturesti_df, libris_df], ignore_index=True)
    
    # Extract and save unique values per store
    stores = {
        'Bookline': ('B', bookline_df),
        'Carturesti': ('C', carturesti_df),
        'Libris': ('L', libris_df)
    }
    
    for store_name, (prefix, df) in stores.items():
        print(f"\nExtracting unique values for {store_name}...")
        unique_dfs = extract_unique_per_store(
            df, 
            prefix, 
            ['Author', 'Genre1', 'Publisher', 'Cover_Type']
        )
        save_unique_per_store(unique_dfs, store_name, 'Data')
    
    # Print overall statistics
    print("\nOverall Statistics:")
    print(f"Total books: {len(all_books)}")
    print(f"Books per store:")
    print(f"  Bookline: {len(all_books[all_books['ID'].str.startswith('B')])}")
    print(f"  Carturesti: {len(all_books[all_books['ID'].str.startswith('C')])}")
    print(f"  Libris: {len(all_books[all_books['ID'].str.startswith('L')])}")
    print(f"Unique authors: {all_books['Author'].nunique()}")
    print(f"Unique publishers: {all_books['Publisher'].nunique()}")
    print(f"Average price: {all_books['Price'].mean():.2f}")
    print(f"Books with valid format: {(all_books['Cover_Type'] != 'N/A').sum()}")
    
    # Create and save unique lists
    print("\nCreating unique lists...")
    unique_lists = create_unique_lists(all_books)
    print("Saving unique lists...")
    save_unique_lists(unique_lists, 'Data')
    
    # Save standardized data
    print("Saving combined standardized data...")
    all_books.to_csv('Data/standardized_books.csv', index=False, encoding='utf-8', sep=';')
    
    print("\nData standardization complete!") 