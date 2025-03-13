from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
import time
import json
import os
import csv

def load_progress():
    if os.path.exists('Scrape\Bookline\scraping_progress.json'):
        with open('Scrape\Bookline\scraping_progress.json', 'r') as f:
            data = json.load(f)
            if 'total_runtime' not in data:
                data['total_runtime'] = 0
            return data
    return {'current_page': 1, 'total_runtime': 0}

def save_progress(page_number, runtime=None):
    progress_data = load_progress()
    progress_data['current_page'] = page_number
    if runtime is not None:
        progress_data['total_runtime'] = runtime
    with open('Scrape\Bookline\scraping_progress.json', 'w') as f:
        json.dump(progress_data, f)

def format_runtime(seconds):
    from datetime import timedelta
    return str(timedelta(seconds=int(seconds)))

def scrape_bookline():
    edge_options = Options()
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Edge(options=edge_options)
    progress = load_progress()
    current_page = progress['current_page']
    previous_runtime = progress['total_runtime']
    first_load = True  # Flag for first page load
    
    start_time = time.time()
    print(f"Previous total runtime: {format_runtime(previous_runtime)}")
    
    try:
        # Create/open CSV file
        with open('Data\Bookline\\bookline_titles.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['page', 'title']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            # Write header if file is empty
            if os.path.getsize('Data\Bookline\\bookline_titles.csv') == 0:
                writer.writeheader()
            
            while current_page <= 10000:
                print(f"\n{'='*50}")
                print(f"Processing page {current_page}")
                print(f"{'='*50}")
                
                url = f"https://bookline.ro/search/search.action?page={current_page}&searchfield=*"
                driver.get(url)
                
                # Handle cookie popup only on first load
                if first_load:
                    try:
                        print("Handling cookie popup...")
                        cookie_button = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                        )
                        cookie_button.click()
                        time.sleep(1)  # Wait for popup to close
                    except Exception as e:
                        print(f"Could not handle cookie popup: {e}")
                    first_load = False
                
                # Wait for product items to load
                wait = WebDriverWait(driver, 30)
                try:
                    # Updated XPath to be more specific and avoid duplicates
                    products = wait.until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, "//div[@class='l-flex__item l-flex__item--12@small'][.//h2[@class='c-product-title']]")
                        )
                    )
                    
                    if not products:
                        print("No more products found")
                        break
                    
                    page_titles = []
                    for product in products:
                        try:
                            # Get the h2 element with author and title info
                            title_element = product.find_element(
                                By.CLASS_NAME, "c-product-title"
                            )
                            
                            # Get author info from the previous sibling div
                            try:
                                author_element = product.find_element(
                                    By.CLASS_NAME, "o-product__authors"
                                )
                                author = author_element.text.strip()
                            except:
                                author = ""
                            
                            # Get the title from the link
                            title_link = title_element.find_element(By.TAG_NAME, "a")
                            book_title = title_link.text.strip()
                            
                            # Combine author and title if author exists
                            full_title = f"{author}: {book_title}" if author else book_title
                            
                            if full_title:
                                page_titles.append(full_title)
                                print(f"Found title: {full_title}")  # Debug print
                        except Exception as e:
                            print(f"Error extracting title: {e}")
                            continue
                    
                    # Save titles to CSV
                    for title in page_titles:
                        writer.writerow({
                            'page': current_page,
                            'title': title
                        })
                    
                    print(f"Found {len(page_titles)} titles on page {current_page}")
                    save_progress(current_page)  # Save progress without runtime
                    current_page += 1
                    
                except Exception as e:
                    print(f"Error processing page: {e}")
                    raise
                
                time.sleep(1)  # Small delay between pages
                
    except KeyboardInterrupt:
        print("\nScript interrupted by user!")
        runtime = time.time() - start_time
        total_runtime = previous_runtime + runtime
        print(f"\nSession runtime: {format_runtime(runtime)}")
        print(f"Total runtime: {format_runtime(total_runtime)}")
        save_progress(current_page, total_runtime)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        runtime = time.time() - start_time
        total_runtime = previous_runtime + runtime
        save_progress(current_page, total_runtime)
        
    finally:
        runtime = time.time() - start_time
        total_runtime = previous_runtime + runtime
        print(f"\nSession runtime: {format_runtime(runtime)}")
        print(f"Total runtime: {format_runtime(total_runtime)}")
        save_progress(current_page, total_runtime)
        driver.quit()

if __name__ == "__main__":
    scrape_bookline()
