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
    if os.path.exists('Scrape\Bookline\details_progress.json'):
        with open('Scrape\Bookline\details_progress.json', 'r') as f:
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
    with open('Scrape\Bookline\details_progress.json', 'w') as f:
        json.dump(progress_data, f)

def format_runtime(seconds):
    return str(timedelta(seconds=int(seconds)))

def log_error(title, error):
    error_msg = str(error).split('\n')[0]
    with open('Data\Bookline\error_titles.txt', 'a', encoding='utf-8') as f:
        f.write(f"{title}\n")

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
        print("Opening Bookline.ro...")
        driver.get("https://bookline.ro/")
        
        # Handle cookie popup
        try:
            print("Handling cookie popup...")
            cookie_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            time.sleep(1)
        except Exception as e:
            print(f"Could not handle cookie popup: {e}")

        with open('Data\Bookline\\book_details.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['page', 'title', 'author', 'publisher', 'price', 'score', 'reviews', 'language', 
                         'pages', 'edition', 'code', 'category']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            if os.path.getsize('Data\Bookline\\book_details.csv') == 0:
                writer.writeheader()
            
            with open('Data\Bookline\\bookline_titles.csv', 'r', encoding='utf-8') as f:
                # Skip header
                next(f)
                lines = f.readlines()[start_line:]
                
                for i, line in enumerate(lines, start=start_line):
                    page, title = line.strip().split(';', 1)
                    print(f"\n{'='*50}")
                    print(f"Processing title {i+1}: {title}")
                    print(f"{'='*50}")
                    
                    try:
                        print("Searching for the book...")
                        # Find and clear search input
                        search_box = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "c-simple-search__input"))
                        )
                        search_box.clear()
                        time.sleep(1)
                        search_box.send_keys(title)
                        time.sleep(0.5)
                        search_box.send_keys(Keys.RETURN)
                        
                        # Wait for results and click first match
                        first_result = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "c-product-title"))
                        )
                        first_result.click()
                        time.sleep(1)
                        
                        # Initialize book details with publisher field
                        book_details = {
                            'page': page,
                            'title': "null",
                            'author': "null",
                            'publisher': "null",  # Added publisher field
                            'price': "null",
                            'score': "null",
                            'reviews': "null",
                            'language': "null",
                            'pages': "N/A",
                            'edition': "N/A",
                            'code': "N/A",
                            'category': "N/A"
                        }
                        
                        # Extract title from product page
                        try:
                            title_element = driver.find_element(
                                By.XPATH, "//h1[@class='c-product__title']"
                            )
                            book_details['title'] = title_element.text.strip()
                            print(f"Found title: {book_details['title']}")
                        except Exception as e:
                            error_msg = str(e).split('\n')[0]
                            print(f"Could not find title: {error_msg}")
                            book_details['title'] = title
                        
                        # Extract author
                        try:
                            author_element = driver.find_element(
                                By.XPATH, "//div[@class='o-product-authors']//span[@itemprop='name']"
                            )
                            book_details['author'] = author_element.text.strip()
                            print(f"Found author: {book_details['author']}")
                        except Exception as e:
                            error_msg = str(e).split('\n')[0]
                            print(f"Could not find author: {error_msg}")
                        
                        # Extract price
                        try:
                            price_element = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//p[@class='o-prices-block__price1']//span[@class='price']")
                                )
                            )
                            price = price_element.text.strip()
                            if price:
                                book_details['price'] = price.replace("RON", "").strip()
                            else:
                                # Check for alternative text
                                alt_price = driver.find_element(
                                    By.XPATH, "//p[@class='o-prices-block__price1']"
                                ).text.strip()
                                book_details['price'] = alt_price
                            print(f"Found price: {book_details['price']}")
                        except Exception as e:
                            print(f"Could not find price: {e}")
                        
                        # Extract rating and reviews
                        try:
                            rating_element = driver.find_element(
                                By.XPATH, "//div[contains(@class, 'o-rating-block-simple')]"
                            )
                            rating_data = rating_element.get_attribute("data-stars")
                            reviews_data = rating_element.get_attribute("data-favcount")
                            book_details['score'] = rating_data or "null"
                            book_details['reviews'] = reviews_data or "null"
                            print(f"Found rating: {rating_data}, reviews: {reviews_data}")
                        except Exception as e:
                            print(f"Could not find rating/reviews: {e}")
                        
                        # Extract publisher
                        try:
                            publisher_element = driver.find_element(
                                By.XPATH, "//a[@class='c-product__publisher']"
                            )
                            book_details['publisher'] = publisher_element.text.strip()
                            print(f"Found publisher: {book_details['publisher']}")
                        except Exception as e:
                            print(f"Could not find publisher: {e}")
                        
                        # Extract category breadcrumb (updated)
                        try:
                            # Get the container div first
                            container = driver.find_element(
                                By.XPATH, "//div[contains(@class, 'l-container') and contains(@class, 'l-gutter-2x-px')]"
                            )
                            # Get the HTML content as string
                            html_content = container.get_attribute('innerHTML')
                            
                            # If container found, look for breadcrumb items
                            if '<ol class="o-breadcrumb "' in html_content:
                                category_elements = container.find_elements(
                                    By.XPATH, ".//span[@itemprop='name']"
                                )
                                categories = [elem.text.strip() for elem in category_elements]
                                book_details['category'] = " > ".join(categories) if categories else "N/A"
                                print(f"Found category: {book_details['category']}")
                            else:
                                print("No breadcrumb found in container")
                                book_details['category'] = "N/A"
                        except Exception as e:
                            error_msg = str(e).split('\n')[0]
                            print(f"Could not find category: {error_msg}")
                            book_details['category'] = "N/A"
                        
                        # Extract details (pages, edition, ISBN, language)
                        try:
                            details_element = driver.find_element(
                                By.XPATH, "//div[contains(@class, 'o-h5')]"
                            )
                            details_text = details_element.text.strip()
                            
                            # Check if details start with a number (pages)
                            if details_text[0].isdigit():
                                book_details['language'] = "magyar"
                                if '･' in details_text:
                                    parts = details_text.split('･')
                                    book_details['pages'] = parts[0].replace(" oldal", "").strip()
                                    book_details['edition'] = parts[1].strip()
                                    if len(parts) > 2:
                                        book_details['code'] = parts[2].replace("ISBN:", "").strip()
                            else:
                                # If starts with language
                                book_details['language'] = details_text.split('･')[0].strip() if '･' in details_text else details_text
                                if '･' in details_text:
                                    parts = details_text.split('･')
                                    if len(parts) > 1:
                                        book_details['pages'] = parts[1].replace(" oldal", "").strip() if "oldal" in parts[1] else "N/A"
                                    if len(parts) > 2:
                                        book_details['edition'] = parts[2].strip()
                                    if len(parts) > 3:
                                        book_details['code'] = parts[3].replace("ISBN:", "").strip()
                            
                            print(f"Found details - Language: {book_details['language']}, "
                                  f"Pages: {book_details['pages']}, "
                                  f"Edition: {book_details['edition']}, "
                                  f"Code: {book_details['code']}")
                        except Exception as e:
                            print(f"Could not find book details: {e}")
                        
                        # Save to CSV
                        print("\nSaving to CSV...")
                        writer.writerow(book_details)
                        save_progress(i + 1)
                        
                    except Exception as e:
                        error_msg = str(e).split('\n')[0]
                        print(f"Error processing title: {error_msg}")
                        log_error(title, error_msg)
                        save_progress(i + 1)
                        continue
                    
                    time.sleep(1)
                    
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
