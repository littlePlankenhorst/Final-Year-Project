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
    if os.path.exists('Scrape\Carturesti\details_progress.json'):
        with open('Scrape\Carturesti\details_progress.json', 'r') as f:
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
    with open('Scrape\Carturesti\details_progress.json', 'w') as f:
        json.dump(progress_data, f)

def format_runtime(seconds):
    return str(timedelta(seconds=int(seconds)))

def log_error(title):
    with open('Data\Carturesti\error_titles.txt', 'a', encoding='utf-8') as f:
        f.write(f"{title}\n")

def clean_search_query(text):
    # Remove percentage symbols
    return text.replace('%', '')

def scrape_book_details():
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
            error_msg = str(e).split('\n')[0]
            print(f"Could not handle cookie popup: {error_msg}")

        with open('Data\Carturesti\\book_details.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'author', 'score', 'reviews', 'price', 'category_1', 
                         'category_2', 'category_3', 'category_4', 'language', 'publish_date', 
                         'publisher', 'pages', 'translator', 'edition']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            if os.path.getsize('Data\Carturesti\\book_details.csv') == 0:
                writer.writeheader()
            
            with open('Data\Carturesti\\book_details_carturesti.csv', 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f, delimiter=',', quotechar='"')
                next(csv_reader)  # Skip header
                lines = list(csv_reader)[start_line:]
                
                books_processed = 0  # Add counter at the start of processing

                for i, row in enumerate(lines, start=start_line):
                    try:
                           
                        # Unpack the row values
                        csv_title, csv_price, csv_author = row
                        # Clean the title and author before creating search query
                        clean_title = clean_search_query(csv_title)
                        clean_author = clean_search_query(csv_author)
                        search_query = f"{clean_title} {clean_author}"
                        
                        print(f"\n{'='*50}")
                        print(f"Processing book {i+1}:")
                        print(f"Original title: {csv_title}")
                        print(f"Search query: {search_query}")
                        print(f"Author: {csv_author}")
                        print(f"{'='*50}")
                        
                        try:
                            print("Searching for the book...")
                            search_box = WebDriverWait(driver, 6).until(
                                EC.presence_of_element_located((By.XPATH, "//input[@id='search-input']"))
                            )
                            search_box.clear()
                            time.sleep(1)
                            search_box.send_keys(search_query)
                            time.sleep(0.5)
                            search_box.send_keys(Keys.RETURN)
                            
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
                                print("Could not find or click search result")
                                log_error(f"{csv_title} - {csv_author}")
                                save_progress(i + 1)
                                continue
                            
                            # Initialize book details
                            book_details = {field: "N/A" for field in fieldnames}
                            
                            # Extract title
                            try:
                                title_element = driver.find_element(By.XPATH, "//h1[@class='titluProdus']")
                                book_details['title'] = title_element.text.strip()
                                print(f"Found title: {book_details['title']}")
                            except Exception as e:
                                print("Could not find title")
                            
                            # Extract author
                            try:
                                author_element = driver.find_element(By.XPATH, "//a[contains(@href, '/autor/')]")
                                book_details['author'] = author_element.text.strip()
                                print(f"Found author: {book_details['author']}")
                            except Exception as e:
                                print("Could not find author")
                            
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
                                print("Could not find rating/reviews")
                            
                            # Extract price
                            try:
                                price_element = driver.find_element(By.XPATH, "//span[@class='pret']")
                                bani_element = price_element.find_element(By.XPATH, ".//span[@class='bani']")
                                price = f"{price_element.text.replace(bani_element.text, '')}.{bani_element.text}"
                                book_details['price'] = price
                                print(f"Found price: {price}")
                            except Exception as e:
                                print("Could not find price")
                            
                            # Extract categories (up to 4)
                            try:
                                category_links = driver.find_elements(
                                    By.XPATH, "//div[@class='linkuriCategorii']/a"
                                )
                                for i, link in enumerate(category_links[:4], 1):
                                    book_details[f'category_{i}'] = link.text.strip()
                                categories = [book_details[f'category_{i}'] for i in range(1, 5) 
                                           if book_details[f'category_{i}'] != "N/A"]
                                print(f"Found categories: {', '.join(categories)}")
                            except Exception as e:
                                print("Could not find categories")
                            
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
                                    print(f"Could not find {attr_key}")
                            
                            # Save to CSV
                            print("\nSaving to CSV...")
                            writer.writerow(book_details)
                            save_progress(i + 1)
                            books_processed += 1  # Increment counter after successful processing
                            
                        except Exception as e:
                            print("Error processing book")
                            log_error(f"{csv_title} - {csv_author}")
                            save_progress(i + 1)
                            print("Going to main page")
                            driver.get("https://carturesti.ro/")
                            continue
                        
                        time.sleep(1)
                        
                    except ValueError as e:
                        print(f"Error parsing CSV row: {row}")
                        log_error(f"CSV parsing error - {','.join(row)}")
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
        error_msg = str(e).split('\n')[0]
        print(f"An error occurred: {error_msg}")
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
    scrape_book_details()
