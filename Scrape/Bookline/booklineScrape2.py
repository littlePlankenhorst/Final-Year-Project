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
    if os.path.exists('Scrape\Bookline\scraping2_progress.json'):
        with open('Scrape\Bookline\scraping2_progress.json', 'r') as f:
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
    with open('Scrape\Bookline\scraping2_progress.json', 'w') as f:
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
    first_load = True  # Flag for first load
    current_rank = 1  # Track the rank of scraped items
    
    start_time = time.time()
    print(f"Previous total runtime: {format_runtime(previous_runtime)}")
    
    try:
        # Create/open CSV file
        with open('Data\Bookline\\Bookline_booktitles.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['page', 'rank', 'title', 'publisher']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            # Write header if file is empty
            if os.path.getsize('Data\Bookline\\Bookline_booktitles.csv') == 0:
                writer.writeheader()
            
            # Initial URL load
            initial_url = "https://bookline.ro/search/search.action?page=1&searchfield=*"
            driver.get(initial_url)
            
            # Handle cookie popup on first load
            if first_load:
                try:
                    print("Handling cookie popup...")
                    cookie_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                    )
                    cookie_button.click()
                    time.sleep(1)
                except Exception as e:
                    print(f"Could not handle cookie popup: {e}")
                
                # Set sorting to "Eladott darabszám szerint"
                try:
                    print("Setting sorting to 'Eladott darabszám szerint'...")
                    # Click on the sorting dropdown
                    sort_dropdown = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Relevancia szerint')]"))
                    )
                    sort_dropdown.click()
                    time.sleep(1)
                    
                    # Click on "Eladott darabszám szerint"
                    sort_by_orders = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Eladott darabszám szerint')]"))
                    )
                    sort_by_orders.click()
                    time.sleep(2)  # Wait for the sorting to apply
                except Exception as e:
                    print(f"Could not set sorting: {e}")
                    return
                
                first_load = False
            
            # Find and click the "Könyv" checkbox
            try:
                print("Finding and clicking the 'Könyv' checkbox...")
                konyv_checkbox = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Könyv')]"))
                )
                konyv_checkbox.click()
                time.sleep(2)  # Wait for the filter to apply
            except Exception as e:
                print(f"Could not find or click the 'Könyv' checkbox: {e}")
                return
            
            while current_page <= 10000:
                print(f"\n{'='*50}")
                print(f"Processing page {current_page}")
                print(f"{'='*50}")
                
                try:
                    # Wait for product items to load
                    wait = WebDriverWait(driver, 4)
                    try:
                        # Try multiple selectors to find products
                        products = None
                        selectors = [
                            "//div[contains(@class, 't-product-detailed')]",
                            "//div[contains(@class, 'c-product-detailed')]",
                            "//div[contains(@class, 'o-product')]",
                            "//div[contains(@class, 'l-flex__item')][.//h2[contains(@class, 'c-product-title')]]"
                        ]
                        
                        for selector in selectors:
                            try:
                                products = wait.until(
                                    EC.presence_of_all_elements_located((By.XPATH, selector))
                                )
                                if products:
                                    print(f"Found products using selector: {selector}")
                                    break
                            except:
                                continue
                        
                        if not products:
                            print("No products found with any selector")
                            break
                        
                        page_titles = []
                        for product in products:
                            try:
                                # Try multiple ways to find the title
                                title_element = None
                                try:
                                    title_element = product.find_element(By.CLASS_NAME, "c-product-title")
                                except:
                                    try:
                                        title_element = product.find_element(By.XPATH, ".//h2[contains(@class, 'c-product-title')]")
                                    except:
                                        continue
                                
                                if not title_element:
                                    continue
                                
                                # Get author info
                                author = ""
                                try:
                                    author_element = product.find_element(By.CLASS_NAME, "o-product__authors")
                                    author = author_element.text.strip()
                                except:
                                    pass
                                
                                # Get the title from the link
                                try:
                                    title_link = title_element.find_element(By.TAG_NAME, "a")
                                    book_title = title_link.text.strip()
                                except:
                                    book_title = title_element.text.strip()
                                
                                # Get publisher info
                                publisher = ""
                                try:
                                    publisher_element = product.find_element(By.CLASS_NAME, "o-product__publisher")
                                    publisher = publisher_element.text.strip()
                                except:
                                    pass
                                
                                full_title = f"{author}: {book_title}" if author else book_title
                                
                                if full_title:
                                    page_titles.append({
                                        'page': current_page,
                                        'rank': current_rank,
                                        'title': full_title,
                                        'publisher': publisher
                                    })
                                    print(f"Found title: {full_title} (Rank: {current_rank})")
                                    if publisher:
                                        print(f"Publisher: {publisher}")
                                    current_rank += 1
                            except Exception as e:
                                print(f"Error extracting title: {e}")
                                continue
                        
                        if not page_titles:
                            print("No titles extracted from products")
                            raise Exception("No titles extracted")
                        
                        # Save titles to CSV
                        for title_data in page_titles:
                            writer.writerow(title_data)
                        
                        print(f"Found {len(page_titles)} titles on page {current_page}")
                        save_progress(current_page)
                        
                        # Find and click the next page button
                        try:
                            next_page = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//span[@class='o-pagination__btn is-current-page']/following::a[1]"))
                            )
                            next_page.click()
                            time.sleep(2)  # Wait for the new page to load
                            current_page += 1
                        except Exception as e:
                            print(f"Could not find or click next page button: {e}")
                            break
                        
                    except Exception as e:
                        print(f"Error processing page: {e}")
                        print("Stopping execution for manual investigation...")
                        print("Will automatically retry in 10 seconds...")
                        time.sleep(10)
                        
                        # Try to find products again
                        try:
                            products = wait.until(
                                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 't-product-detailed')]"))
                            )
                            if products:
                                print("Retry successful, continuing with scraping...")
                                continue
                        except:
                            print("Retry failed, moving to next page...")
                            current_page += 1
                            continue
                    
                except Exception as e:
                    print(f"An error occurred: {e}")
                    print("Stopping execution for manual investigation...")
                    print("Will automatically retry in 10 seconds...")
                    time.sleep(10)
                    
                    # Try to find products again
                    try:
                        products = wait.until(
                            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 't-product-detailed')]"))
                        )
                        if products:
                            print("Retry successful, continuing with scraping...")
                            continue
                    except:
                        print("Retry failed, moving to next page...")
                        current_page += 1
                        continue
                
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
