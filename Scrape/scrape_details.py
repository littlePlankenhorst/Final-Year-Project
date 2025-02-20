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
    if os.path.exists('details_progress.json'):
        with open('details_progress.json', 'r') as f:
            return json.load(f)
    return {'last_processed_line': 0}

def save_progress(line_number):
    with open('details_progress.json', 'w') as f:
        json.dump({'last_processed_line': line_number}, f)

def log_error(title, error):
    with open('Data\error_titles.txt', 'a', encoding='utf-8') as f:
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
        with open('Data\\book_details.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['year', 'page', 'title', 'average_score', 'votes', 'price', 
                         'categories', 'author', 'publisher', 'cover_type',
                         'publication_year', 'num_pages', 'format', 'code']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            if os.path.getsize('Data\\book_details.csv') == 0:
                writer.writeheader()
            
            with open('Data\libris_titles.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()[start_line:]
                
                for i, line in enumerate(lines, start=start_line):
                    year, page, title = line.strip().split(',', 2)
                    print(f"\nProcessing title {i+1}: {title}")
                    
                    try:
                        driver.get("https://www.libris.ro/")
                        
                        # Handle cookie popup only on first load
                        if first_load:
                            try:
                                refuse_button = WebDriverWait(driver, 3).until(
                                    EC.presence_of_element_located((By.XPATH, "//a[text()='Refuz toate']"))
                                )
                                if refuse_button.is_displayed():
                                    refuse_button.click()
                            except:
                                print("No cookie popup found or already handled")
                            first_load = False
                        
                        # Search for the book
                        search_box = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "autoComplete"))
                        )
                        search_box.clear()
                        search_box.send_keys(title)
                        search_box.send_keys(Keys.RETURN)
                        
                        # Wait for search results
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "pr-title-categ-pg"))
                        )
                        
                        # Find all results
                        results = driver.find_elements(By.CLASS_NAME, "pr-title-categ-pg")
                        
                        # Find exact matches
                        matching_results = []
                        for result in results:
                            if result.text.strip() == title.strip():
                                matching_results.append(result)
                        
                        if not matching_results:
                            print(f"No exact matches found for: {title}")
                            log_error(title, "No exact matches found")
                            save_progress(i + 1)
                            continue
                        
                        # Process each matching result
                        for match in matching_results:
                            try:
                                match.click()
                                
                                # Extract book details
                                book_details = {
                                    'year': year,
                                    'page': page,
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
                                    pub_year = driver.find_element(By.XPATH, "//li[contains(@class, 'pr-lista-item')]//*[contains(text(), 'An aparitie:')]/..")
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
                                
                                # Write details to CSV
                                writer.writerow(book_details)
                                
                                # Go back to search results if there are more matches
                                if len(matching_results) > 1:
                                    driver.back()
                                    time.sleep(1)  # Wait for page to load
                                    
                            except Exception as e:
                                print(f"Error processing match: {e}")
                                continue
                        
                        # Save progress after processing all matches
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