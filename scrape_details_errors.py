from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.keys import Keys
import time
import json
import os
import csv

def load_progress():
    if os.path.exists('Scrape\errors_details_progress.json'):
        with open('Scrape\errors_details_progress.json', 'r') as f:
            return json.load(f)
    return {'last_processed_line': 0}

def save_progress(line_number):
    with open('Scrape\errors_details_progress.json', 'w') as f:
        json.dump({'last_processed_line': line_number}, f)

def log_error(title, error):
    # Strip error message at first tab space
    error = str(error).split('\t')[0]
    with open('Data\waste.txt', 'a', encoding='utf-8') as f:
        f.write(f"{title}\t{error}\n")

def scrape_book_details():
    edge_options = Options()
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Edge(options=edge_options)
    progress = load_progress()
    start_line = progress['last_processed_line']
    first_load = True
    
    try:
        with open('Data\error_book_details.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'average_score', 'votes', 'price', 
                         'categories', 'author', 'publisher', 'cover_type',
                         'publication_year', 'num_pages', 'format', 'code']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            if os.path.getsize('Data\error_book_details.csv') == 0:
                writer.writeheader()
            
            with open('Data\error_titles.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()[start_line:]
                
                for i, line in enumerate(lines, start=start_line):
                    title = line
                    print(f"\n{'='*50}")
                    print(f"Processing title {i+1}: {title}")
                    print(f"{'='*50}")
                    
                    try:
                        print("Opening Libris.ro...")
                        driver.get("https://www.libris.ro/")
                        
                        # Handle cookie popup only on first load
                        if first_load:
                            try:
                                print("Handling cookie popup...")
                                refuse_button = WebDriverWait(driver, 1).until(
                                    EC.presence_of_element_located((By.XPATH, "//a[text()='Refuz toate']"))
                                )
                                if refuse_button.is_displayed():
                                    refuse_button.click()
                            except:
                                print("No cookie popup found or already handled")
                            first_load = False
                        
                        print("Searching for the book...")
                        # Search for the book
                        search_box = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.ID, "autoComplete"))
                        )
                        search_box.clear()
                        search_box.send_keys(title)
                        search_box.send_keys(Keys.RETURN)
                        
                        # Wait for search results
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "pr-title-categ-pg"))
                        )
                        
                        # Find all results
                        results = driver.find_elements(By.CLASS_NAME, "pr-title-categ-pg")
                        
                        # Find first exact match
                        matching_result = None
                        for result in results:
                            if result.text.strip() == title.strip():
                                matching_result = result
                                break
                        
                        if not matching_result:
                            print(f"No exact matches found for: {title}")
                            log_error(title, "No exact matches found")
                            save_progress(i + 1)
                            continue
                        
                        # Process the matching result
                        try:
                            matching_result.click()
                            
                            # Extract book details
                            book_details = {
                                'title': title,
                                'average_score': "null",
                                'votes': "null",
                                'price': "null",
                                'categories': "null",
                                'author': "null",
                                'publisher': "null",
                                'cover_type': "null",
                                'publication_year': "null",
                                'num_pages': "null",
                                'format': "null",
                                'code': "null"
                            }
                            
                            # Extract fields
                            try:
                                score = driver.find_element(By.CLASS_NAME, "count-nr").text
                                book_details['average_score'] = score.strip() or "null"
                            except:
                                pass
                            
                            try:
                                votes = driver.find_element(By.CLASS_NAME, "review-num").text
                                book_details['votes'] = votes.strip('() review-uri') or "null"
                            except:
                                pass
                            
                            try:
                                price = driver.find_element(By.CLASS_NAME, "pr-pret-intreg").text
                                book_details['price'] = price.replace(" Lei", "") or "null"
                            except:
                                pass
                            
                            try:
                                categories = driver.find_element(By.XPATH, "//li[contains(@class, 'pr-lista-item')]//*[contains(text(), 'Categoria:')]/..")
                                book_details['categories'] = categories.text.replace("Categoria: ", "") or "null"
                            except:
                                pass
                            
                            try:
                                author = driver.find_element(By.XPATH, "//li[contains(@class, 'pr-lista-item')]//*[contains(text(), 'Autor:')]/..")
                                book_details['author'] = author.text.replace("Autor: ", "") or "null"
                            except:
                                pass
                            
                            try:
                                publisher = driver.find_element(By.XPATH, "//li[contains(@class, 'pr-lista-item')]//*[contains(text(), 'Editura:')]/..")
                                book_details['publisher'] = publisher.text.replace("Editura: ", "") or "null"
                            except:
                                pass
                            
                            try:
                                cover = driver.find_element(By.XPATH, "//li[contains(@class, 'pr-lista-item')]//*[contains(text(), 'Editie:')]/..")
                                book_details['cover_type'] = cover.text.replace("Editie: ", "") or "null"
                            except:
                                pass
                            
                            try:
                                pub_year = driver.find_element(By.XPATH, "//li[contains(@class, 'pr-lista-item pr-lista-item-remove-bottom-border')]//*[contains(text(), 'An aparitie:')]/..")
                                book_details['publication_year'] = pub_year.text.replace("An aparitie: ", "") or "null"
                            except:
                                pass
                            
                            try:
                                pages = driver.find_element(By.XPATH, "//li[contains(@class, 'pr-lista-item')]//*[contains(text(), 'Nr. pagini:')]/..")
                                book_details['num_pages'] = pages.text.replace("Nr. pagini: ", "") or "null"
                            except:
                                pass
                            
                            try:
                                format_info = driver.find_element(By.XPATH, "//li[contains(@class, 'pr-lista-item')]//*[contains(text(), 'Format:')]/..")
                                book_details['format'] = format_info.text.replace("Format: ", "") or "null"
                            except:
                                pass
                            
                            try:
                                code = driver.find_element(By.XPATH, "//li[contains(@class, 'pr-lista-item')]//*[contains(text(), 'Cod:')]/..")
                                book_details['code'] = code.text.replace("Cod: ", "") or "null"
                            except:
                                pass
                            
                            # After extracting all fields, print the found data
                            print("\nFound book details:")
                            print(f"Title: {title}")
                            
                            # Only print non-null values
                            for key, value in book_details.items():
                                if value != "null" and key not in ['year', 'page', 'title']:
                                    print(f"{key.replace('_', ' ').title()}: {value}")
                            
                            print("\nSaving to CSV...")
                            
                            # Write details to CSV
                            writer.writerow(book_details)
                            
                        except Exception as e:
                            print(f"Error processing match: {e}")
                            continue
                        
                        # Save progress
                        save_progress(i + 1)
                        
                    except Exception as e:
                        print(f"Error processing title: {e}")
                        log_error(title, str(e))
                        save_progress(i + 1)
                        continue
                    
                    time.sleep(1)  # Small delay between requests
                    
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_book_details() 