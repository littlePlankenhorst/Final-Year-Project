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
import signal
from datetime import datetime, timedelta

def load_progress():
    if os.path.exists('Scrape\Libris\error_progress.json'):
        with open('Scrape\Libris\error_progress.json', 'r') as f:
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
    with open('Scrape\Libris\error_progress.json', 'w') as f:
        json.dump(progress_data, f)

def format_runtime(seconds):
    return str(timedelta(seconds=int(seconds)))

def log_waste(title):
    with open('Data\Libris\waste.txt', 'a', encoding='utf-8') as f:
        f.write(f"{title}\n")

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
        print("Opening Libris.ro...")
        driver.get("https://www.libris.ro/")
        
        # Handle cookie popup
        try:
            print("Handling cookie popup...")
            refuse_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[text()='Refuz toate']"))
            )
            if refuse_button.is_displayed():
                refuse_button.click()
                time.sleep(10)
        except:
            print("No cookie popup found or already handled")
        
        # Handle newsletter popup
        try:
            print("Handling newsletter popup...")
            close_newsletter = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "modal-close-x-c-newsletter"))
            )
            if close_newsletter.is_displayed():
                close_newsletter.click()
                time.sleep(1)
        except:
            print("No newsletter popup found or already handled")

        with open('Data\Libris\\book_details.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['year', 'page', 'title', 'average_score', 'votes', 'price', 
                         'categories', 'author', 'publisher', 'cover_type',
                         'publication_year', 'num_pages', 'format', 'code']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            with open('Data\Libris\error_titles.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()[start_line:]
                
                for i, line in enumerate(lines, start=start_line):
                    title = line.strip()  # Error titles don't have year and page
                    print(f"\n{'='*50}")
                    print(f"Processing title {i+1}: {title}")
                    print(f"{'='*50}")
                    
                    try:
                        print("Searching for the book...")
                        search_box = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.ID, "autoComplete"))
                        )
                        search_box.clear()
                        time.sleep(1)
                        search_box.send_keys(title)
                        time.sleep(0.5)
                        search_box.send_keys(Keys.RETURN)
                        
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "pr-title-categ-pg"))
                        )
                        
                        time.sleep(1)
                        
                        results = driver.find_elements(By.CLASS_NAME, "pr-title-categ-pg")
                        
                        matching_result = None
                        for result in results:
                            if result.text.strip() == title.strip():
                                matching_result = result
                                try:
                                    parent_container = result.find_element(By.XPATH, "./ancestor::div[contains(@class, 'pr-history-item')]")
                                    link = parent_container.find_element(By.TAG_NAME, "a")
                                    html_content = link.get_attribute('outerHTML')
                                    
                                    if 'data-price="' in html_content:
                                        price = html_content.split('data-price="')[1].split('"')[0]
                                        print(f"Found price from search results: {price}")
                                    else:
                                        price = "null"
                                        print("Price attribute not found in HTML")
                                        
                                except Exception as e:
                                    print(f"Could not find price in search results: {str(e)}")
                                    price = "null"
                                break
                        
                        if not matching_result:
                            print(f"No exact matches found for: {title}")
                            log_waste(title)
                            save_progress(i + 1)
                            continue
                        
                        try:
                            WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, "pr-title-categ-pg"))
                            )
                            time.sleep(1)
                            matching_result.click()
                            
                            wait = WebDriverWait(driver, 5)
                            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "pr-lista-detalii")))
                            time.sleep(1)

                            book_details = {
                                'year': "null",  # No year info in error titles
                                'page': "null",  # No page info in error titles
                                'title': title,
                                'average_score': "null",
                                'votes': "null",
                                'price': price,
                                'categories': "null",
                                'author': "null",
                                'publisher': "null",
                                'cover_type': "null",
                                'publication_year': "null",
                                'num_pages': "null",
                                'format': "null",
                                'code': "null"
                            }

                            # Get review data
                            try:
                                print("Extracting review data...")
                                feedback_element = wait.until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "pr-rg-feedback-count"))
                                )
                                feedback_text = feedback_element.text.strip()
                                score = feedback_text.split('(')[0].strip()
                                votes = feedback_text.split('(')[1].split('review')[0].strip()
                                
                                book_details['average_score'] = score or "null"
                                book_details['votes'] = votes or "null"
                                print(f"Found reviews - Score: {score}, Number of reviews: {votes}")
                            except:
                                print("No reviews found for this book")
                                book_details['average_score'] = "0"
                                book_details['votes'] = "0"

                            # Click "show more" button
                            try:
                                print("Expanding details...")
                                show_more = wait.until(
                                    EC.element_to_be_clickable((By.CLASS_NAME, "afiseaza-mai-mult"))
                                )
                                show_more.click()
                                time.sleep(1)
                            except Exception as e:
                                print(f"Could not expand details: {str(e)}")

                            # Extract details
                            print("Extracting book details...")
                            try:
                                items = wait.until(
                                    EC.presence_of_all_elements_located((By.CLASS_NAME, "pr-lista-item"))
                                )
                                
                                for item in items:
                                    try:
                                        text = item.text.strip()
                                        if "Categoria:" in text:
                                            book_details['categories'] = text.replace("Categoria:", "").strip()
                                        elif "Autor:" in text:
                                            book_details['author'] = text.replace("Autor:", "").strip()
                                        elif "Editura:" in text:
                                            book_details['publisher'] = text.replace("Editura:", "").strip()
                                        elif "Editie:" in text:
                                            book_details['cover_type'] = text.replace("Editie:", "").strip()
                                        elif "An aparitie:" in text:
                                            book_details['publication_year'] = text.replace("An aparitie:", "").strip()
                                        elif "Nr. pagini:" in text:
                                            book_details['num_pages'] = text.replace("Nr. pagini:", "").strip()
                                        elif "Format:" in text:
                                            book_details['format'] = text.replace("Format:", "").strip()
                                        elif "Cod:" in text:
                                            book_details['code'] = text.replace("Cod:", "").strip()
                                    except Exception as e:
                                        print(f"Error processing item: {str(e)}")
                                        continue

                            except Exception as e:
                                print(f"Error extracting details: {str(e)}")

                            print("\nFound book details:")
                            for key, value in book_details.items():
                                if value != "null":
                                    print(f"{key.replace('_', ' ').title()}: {value}")
                            
                            print("\nSaving to CSV...")
                            writer.writerow(book_details)
                            save_progress(i + 1)
                            
                        except Exception as e:
                            print(f"Error processing match: {e}")
                            log_waste(title)
                            continue
                        
                    except Exception as e:
                        print(f"Error processing title: {str(e)}")
                        log_waste(title)
                        save_progress(i + 1)
                        # driver.get("https://www.libris.ro/")
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
        print(f"An error occurred: {e}")
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