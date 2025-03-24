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
from datetime import timedelta

def load_progress():
    if os.path.exists('Scrape/Carturesti/error_progress.json'):
        with open('Scrape/Carturesti/error_progress.json', 'r') as f:
            data = json.load(f)
            if 'total_runtime' not in data:
                data['total_runtime'] = 0
            return data
    return {'last_processed_line': 0, 'total_runtime': 0}

def save_progress(line_number, runtime=None):
    progress_data = load_progress()
    progress_data['last_processed_line'] = line_number
    if runtime is not None:
        progress_data['total_runtime'] = runtime
    with open('Scrape/Carturesti/error_progress.json', 'w') as f:
        json.dump(progress_data, f)

def format_runtime(seconds):
    return str(timedelta(seconds=int(seconds)))

def log_waste(title):
    with open('Data/Carturesti/waste.txt', 'a', encoding='utf-8') as f:
        f.write(f"{title}\n")

def clean_search_query(text):
    return text.replace('%', '')

def scrape_error_books():
    edge_options = Options()
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Edge(options=edge_options)
    progress = load_progress()
    start_line = progress['last_processed_line']
    previous_runtime = progress['total_runtime']
    
    start_time = time.time()
    print(f"Previous total runtime: {format_runtime(previous_runtime)}")
    
    try:
        print("Opening Carturesti.ro...")
        driver.get("https://carturesti.ro/")
        
        # Handle cookie popup
        try:
            print("Handling cookie popup...")
            cookie_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "cc-deny"))
            )
            cookie_button.click()
            time.sleep(1)
        except Exception as e:
            print(f"Cookie popup handling failed: {str(e)}")

        with open('Data/Carturesti/book_details.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'author', 'score', 'reviews', 'price', 'category_1', 
                         'category_2', 'category_3', 'category_4', 'language', 'publish_date', 
                         'publisher', 'pages', 'translator', 'edition']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            # Read error titles
            with open('Data/Carturesti/error_titles.txt', 'r', encoding='utf-8') as f:
                error_titles = f.readlines()[start_line:]
                
                for i, line in enumerate(error_titles, start=start_line):
                    try:
                        # Parse title and author
                        title_author = line.strip().split(' - ')
                        if len(title_author) != 2:
                            print(f"Invalid format in line: {line}")
                            log_waste(line.strip())
                            continue
                            
                        csv_title, csv_author = title_author
                        # Search only by title
                        search_query = clean_search_query(csv_title)
                        
                        print(f"\n{'='*50}")
                        print(f"Processing book {i+1}:")
                        print(f"Title: {csv_title}")
                        print(f"Author: {csv_author}")
                        print(f"{'='*50}")
                        
                        # Rest of the scraping logic remains similar but with better error handling
                        try:
                            search_box = WebDriverWait(driver, 6).until(
                                EC.presence_of_element_located((By.XPATH, "//input[@id='search-input']"))
                            )
                            search_box.clear()
                            time.sleep(1)
                            search_box.send_keys(search_query)
                            time.sleep(0.5)
                            search_box.send_keys(Keys.RETURN)
                            
                            # Initialize book details
                            book_details = {field: "N/A" for field in fieldnames}
                            
                            # Wait for and click first result
                            try:
                                print("Looking for first result...")
                                first_result = WebDriverWait(driver, 6).until(
                                    EC.element_to_be_clickable((
                                        By.XPATH, 
                                        "//a[@class='clean-a select-item-event' and contains(@data-ng-click, 'onProductClick')]"
                                    ))
                                )
                                print("Found result, clicking...")
                                first_result.click()
                                time.sleep(1)
                            except Exception as e:
                                print(f"Could not find or click search result: {str(e)}")
                                log_waste(f"{csv_title} - {csv_author}")
                                save_progress(i + 1)
                                # driver.get("https://carturesti.ro/")
                                continue
                            
                            # Extract title
                            try:
                                title_element = driver.find_element(By.XPATH, "//h1[@class='titluProdus']")
                                book_details['title'] = title_element.text.strip()
                                print(f"Found title: {book_details['title']}")
                            except Exception as e:
                                print(f"Could not find title: {str(e)}")
                            
                            # Extract author
                            try:
                                author_element = driver.find_element(By.XPATH, "//a[contains(@href, '/autor/')]")
                                book_details['author'] = author_element.text.strip()
                                print(f"Found author: {book_details['author']}")
                            except Exception as e:
                                print(f"Could not find author: {str(e)}")
                            
                            # Extract score and reviews
                            try:
                                score_element = driver.find_element(
                                    By.XPATH, "//span[@data-ng-bind='h.numberFormat(agregateRating,1)']"
                                )
                                reviews_element = driver.find_element(
                                    By.XPATH, "//span[@data-ng-bind='votes']"
                                )
                                book_details['score'] = score_element.text.strip()
                                book_details['reviews'] = reviews_element.text.strip()
                                print(f"Found rating: {book_details['score']}, reviews: {book_details['reviews']}")
                            except Exception as e:
                                print(f"Could not find rating/reviews: {str(e)}")
                            
                            # Extract price
                            try:
                                price_element = driver.find_element(By.XPATH, "//span[@class='pret']")
                                bani_element = price_element.find_element(By.XPATH, ".//span[@class='bani']")
                                price = f"{price_element.text.replace(bani_element.text, '')}.{bani_element.text}"
                                book_details['price'] = price
                                print(f"Found price: {price}")
                            except Exception as e:
                                print(f"Could not find price: {str(e)}")
                            
                            # Extract categories (up to 4)
                            try:
                                category_links = driver.find_elements(
                                    By.XPATH, "//div[@class='linkuriCategorii']/a"
                                )
                                for idx, link in enumerate(category_links[:4], 1):
                                    book_details[f'category_{idx}'] = link.text.strip()
                                categories = [book_details[f'category_{idx}'] for idx in range(1, 5) 
                                           if book_details[f'category_{idx}'] != "N/A"]
                                print(f"Found categories: {', '.join(categories)}")
                            except Exception as e:
                                print(f"Could not find categories: {str(e)}")
                            
                            # Extract additional attributes
                            attributes = {
                                'language': "//div[@class='productAttr'][contains(., 'Limba:')]//div",
                                'publish_date': "//div[@class='productAttr'][contains(., 'Data publicarii:')]//div",
                                'publisher': "//div[@class='productAttr'][contains(., 'Editura:')]//div",
                                'pages': "//div[@class='productAttr'][contains(., 'Nr. pagini:')]//div",
                                'translator': "//div[@class='productAttr'][contains(., 'Traducatori:')]//div",
                                'edition': "//div[@class='productAttr'][contains(., 'Tip coperta:')]//div"
                            }
                            
                            for attr_key, xpath in attributes.items():
                                try:
                                    attr_element = driver.find_element(By.XPATH, xpath)
                                    value = attr_element.text.strip()
                                    book_details[attr_key] = value
                                    print(f"Found {attr_key}: {value}")
                                except Exception as e:
                                    print(f"Could not find {attr_key}: {str(e)}")
                            
                            # Verify we found at least title and author before saving
                            if book_details['title'] != "N/A" and book_details['author'] != "N/A":
                                print("\nSaving to CSV...")
                                writer.writerow(book_details)
                                save_progress(i + 1)
                            else:
                                print("\nInsufficient data found, logging to waste...")
                                log_waste(f"{csv_title} - {csv_author}")
                                save_progress(i + 1)
                            
                        except Exception as e:
                            print(f"Error during scraping process: {str(e)}")
                            log_waste(f"{csv_title} - {csv_author}")
                            save_progress(i + 1)
                            driver.get("https://carturesti.ro/")
                            continue
                        
                    except Exception as e:
                        print(f"Error processing line {i+1}: {str(e)}")
                        log_waste(line.strip())
                        save_progress(i + 1)
                        continue
                    
    except KeyboardInterrupt:
        print("\nScript interrupted by user!")
        runtime = time.time() - start_time
        total_runtime = previous_runtime + runtime
        print(f"\nSession runtime: {format_runtime(runtime)}")
        print(f"Total runtime: {format_runtime(total_runtime)}")
        save_progress(i + 1, total_runtime)
        
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        runtime = time.time() - start_time
        total_runtime = previous_runtime + runtime
        save_progress(i + 1, total_runtime)
        
    finally:
        runtime = time.time() - start_time
        total_runtime = previous_runtime + runtime
        print(f"\nSession runtime: {format_runtime(runtime)}")
        print(f"Total runtime: {format_runtime(total_runtime)}")
        save_progress(i + 1, total_runtime)
        driver.quit()

if __name__ == "__main__":
    scrape_error_books() 