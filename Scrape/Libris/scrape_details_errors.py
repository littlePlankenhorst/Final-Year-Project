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
    if os.path.exists('Scrape\Libris\errors_details_progress.json'):
        with open('Scrape\Libris\errors_details_progress.json', 'r') as f:
            data = json.load(f)
            # Add default runtime if not present
            if 'total_runtime' not in data:
                data['total_runtime'] = 0
            return data
    return {'last_processed_line': 0, 'total_runtime': 0}

def save_progress(line_number, runtime):
    progress_data = load_progress()
    progress_data['last_processed_line'] = line_number
    progress_data['total_runtime'] = progress_data.get('total_runtime', 0) + runtime
    with open('Scrape\Libris\errors_details_progress.json', 'w') as f:
        json.dump(progress_data, f)

def log_error(title, error):
    # Strip error message at first tab space
    error = str(error).split('\t')[0]
    with open('Data\Libris\waste.txt', 'a', encoding='utf-8') as f:
        f.write(f"{title}\t{error}\n")

def scrape_book_details_errors():
    edge_options = Options()
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Edge(options=edge_options)
    progress = load_progress()
    start_line = progress['last_processed_line']
    
    try:
        # Open the main URL only once at the start
        print("Opening Libris.ro...")
        driver.get("https://www.libris.ro/")
        
        # Handle cookie popup
        try:
            print("Handling cookie popup...")
            refuse_button = WebDriverWait(driver, 12).until(
                EC.presence_of_element_located((By.XPATH, "//a[text()='Refuz toate']"))
            )
            if refuse_button.is_displayed():
                refuse_button.click()
                time.sleep(3)  # Wait for newsletter popup
        except:
            print("No cookie popup found or already handled")
        
        # Handle newsletter popup
        try:
            print("Handling newsletter popup...")
            close_newsletter = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "modal-close-x-c-newsletter"))
            )
            if close_newsletter.is_displayed():
                close_newsletter.click()
                time.sleep(1)  # Wait for popup to close
        except:
            print("No newsletter popup found or already handled")

        with open('Data\Libris\error_book_details.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'average_score', 'votes', 'price', 
                         'categories', 'author', 'publisher', 'cover_type',
                         'publication_year', 'num_pages', 'format', 'code']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            if os.path.getsize('Data\Libris\error_book_details.csv') == 0:
                writer.writeheader()
            
            with open('Data\error_titles.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()[start_line:]
                
                for i, line in enumerate(lines, start=start_line):
                    title = line
                    print(f"\n{'='*50}")
                    print(f"Processing title {i+1}: {title}")
                    print(f"{'='*50}")
                    
                    try:
                        print("Searching for the book...")
                        # Search for the book from current page
                        search_box = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "autoComplete"))
                        )
                        search_box.clear()
                        time.sleep(1)  # Wait before typing
                        search_box.send_keys(title)
                        time.sleep(0.5)  # Wait before pressing Enter
                        search_box.send_keys(Keys.RETURN)
                        
                        # Wait for search results with longer timeout
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "pr-title-categ-pg"))
                        )
                        
                        time.sleep(1)  # Wait for results to stabilize
                        
                        # Find all results
                        results = driver.find_elements(By.CLASS_NAME, "pr-title-categ-pg")
                        
                        # Find first exact match and its price
                        matching_result = None
                        for result in results:
                            if result.text.strip() == title.strip():
                                matching_result = result
                                try:
                                    # Get the parent container and find the first anchor tag
                                    parent_container = result.find_element(By.XPATH, "./ancestor::div[contains(@class, 'pr-history-item')]")
                                    link = parent_container.find_element(By.TAG_NAME, "a")
                                    html_content = link.get_attribute('outerHTML')
                                    
                                    # Extract price from data-price attribute
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
                            log_error(title, "No exact matches found")
                            save_progress(i + 1, 0)
                            continue
                        
                        # Process the matching result
                        try:
                            # Wait for element to be clickable
                            WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, "pr-title-categ-pg"))
                            )
                            time.sleep(1)  # Additional wait before clicking
                            matching_result.click()
                            
                            # Initialize book_details
                            book_details = {
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

                            # Wait for page to load
                            wait = WebDriverWait(driver, 10)
                            
                            # Wait for the details list to be visible
                            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "pr-lista-detalii")))
                            time.sleep(1)  # Wait for all elements to stabilize

                            # Get review data
                            try:
                                print("Extracting review data...")
                                try:
                                    # Look for the feedback count element
                                    feedback_element = wait.until(
                                        EC.presence_of_element_located((By.CLASS_NAME, "pr-rg-feedback-count"))
                                    )
                                    feedback_text = feedback_element.text.strip()
                                    
                                    # Parse the text: "5 (1 review-uri)" -> score: "5", votes: "1"
                                    score = feedback_text.split('(')[0].strip()
                                    votes = feedback_text.split('(')[1].split('review')[0].strip()
                                    
                                    book_details['average_score'] = score or "null"
                                    book_details['votes'] = votes or "null"
                                    print(f"Found reviews - Score: {score}, Number of reviews: {votes}")
                                    
                                except:
                                    # If element not found, set default values
                                    print("No reviews found for this book")
                                    book_details['average_score'] = "0"
                                    book_details['votes'] = "0"
                                
                            except Exception as e:
                                print(f"Error processing review data: {str(e)}")
                                book_details['average_score'] = "0"
                                book_details['votes'] = "0"

                            # Click "show more" button
                            try:
                                print("Expanding details...")
                                show_more = wait.until(
                                    EC.element_to_be_clickable((By.CLASS_NAME, "afiseaza-mai-mult"))
                                )
                                show_more.click()
                                time.sleep(1)  # Wait for animation
                            except Exception as e:
                                print(f"Could not expand details: {str(e)}")

                            # Extract all details from list items
                            print("Extracting book details...")
                            try:
                                # Wait for list items to be visible
                                items = wait.until(
                                    EC.presence_of_all_elements_located((By.CLASS_NAME, "pr-lista-item"))
                                )
                                
                                for item in items:
                                    try:
                                        text = item.text.strip()
                                        
                                        # Map the text to the corresponding field
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

                            # Print found details
                            print("\nFound book details:")
                            print(f"Title: {title}")
                            for key, value in book_details.items():
                                if value != "null" and key != 'title':
                                    print(f"{key.replace('_', ' ').title()}: {value}")
                            
                            print("\nSaving to CSV...")
                            writer.writerow(book_details)
                            save_progress(i + 1, 0)
                            
                        except Exception as e:
                            print(f"Error processing match: {e}")
                            continue
                        
                    except Exception as e:
                        print(f"Error processing title: {e}")
                        log_error(title, str(e))
                        save_progress(i + 1, 0)
                        continue
                    
                    time.sleep(1)  # Small delay between requests
                    
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_book_details_errors() 