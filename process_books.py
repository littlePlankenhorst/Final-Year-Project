import pandas as pd
import numpy as np

def process_books():
    print("Reading standardized books data...")
    # Read the standardized books data
    df = pd.read_csv('Data/standardized_books.csv', sep=';', encoding='utf-8')
    print(f"Total records read: {len(df)}")
    
    # Define required columns for checking
    relevant_check_columns = ['Title', 'Author', 'Price', 'Reviews', 'Score', 'Genre1']
    full_check_columns = ['Title', 'Author', 'Price', 'Reviews', 'Score', 'Number_Of_Pages', 'Genre1', 
                         'Publisher', 'Cover_Type']
    
    # Create relevantLines.csv - only records with all required fields filled
    print("\nProcessing relevantLines.csv...")
    relevant_df = df.copy()  # Keep all columns
    relevant_df = relevant_df.dropna(subset=relevant_check_columns)
    relevant_df.to_csv('Data/relevantLines.csv', sep=';', index=False, encoding='utf-8')
    print(f"Saved {len(relevant_df)} records to relevantLines.csv")
    
    # Create fullLines.csv - only records with all required fields filled
    print("\nProcessing fullLines.csv...")
    full_df = df.copy()  # Keep all columns
    full_df = full_df.dropna(subset=full_check_columns)
    full_df.to_csv('Data/fullLines.csv', sep=';', index=False, encoding='utf-8')
    print(f"Saved {len(full_df)} records to fullLines.csv")
    
    # Print overall statistics
    print("\nOverall Statistics:")
    print(f"Total records in standardized_books.csv: {len(df)}")
    print(f"Records with all relevant fields: {len(relevant_df)} ({len(relevant_df)/len(df)*100:.2f}%)")
    print(f"Records with all full fields: {len(full_df)} ({len(full_df)/len(df)*100:.2f}%)")
    
    # Print store-specific statistics
    stores = {
        'Bookline': 'B',
        'Carturesti': 'C',
        'Libris': 'L'
    }
    
    print("\nStore-specific Statistics:")
    for store_name, prefix in stores.items():
        store_df = df[df['ID'].str.startswith(prefix)]
        store_relevant = relevant_df[relevant_df['ID'].str.startswith(prefix)]
        store_full = full_df[full_df['ID'].str.startswith(prefix)]
        
        print(f"\n{store_name}:")
        print(f"  Total records: {len(store_df)}")
        print(f"  Records with all relevant fields: {len(store_relevant)} ({len(store_relevant)/len(store_df)*100:.2f}%)")
        print(f"  Records with all full fields: {len(store_full)} ({len(store_full)/len(store_df)*100:.2f}%)")
    
    # Print field completion statistics
    print("\nField completion statistics:")
    for col in relevant_check_columns + ['Publisher', 'Cover_Type', 'Number_Of_Pages']:
        completion_rate = (1 - df[col].isna().mean()) * 100
        print(f"{col}: {completion_rate:.2f}%")
        
        # Print store-specific completion rates
        for store_name, prefix in stores.items():
            store_df = df[df['ID'].str.startswith(prefix)]
            store_completion = (1 - store_df[col].isna().mean()) * 100
            print(f"  {store_name}: {store_completion:.2f}%")

if __name__ == "__main__":
    process_books() 