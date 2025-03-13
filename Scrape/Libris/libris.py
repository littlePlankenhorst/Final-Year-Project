from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
import time
import json
import os

def load_progress():
    if os.path.exists('Scrape\Libris\scraping_progress.json'):
        with open('Scrape\Libris\scraping_progress.json', 'r') as f:
            return json.load(f)
    return {'year': 2002, 'page': 1}

def save_progress(year, page):
    with open('Scrape\Libris\scraping_progress.json', 'w') as f:
        json.dump({'year': year, 'page': page}, f)

def scrape_libris():
    # Load previous progress
    progress = load_progress()
    current_year = progress['year']
    current_page = progress['page']
    
    # Set up Edge options
    edge_options = Options()
    # edge_options.add_argument("--headless")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Edge(options=edge_options)
    first_load = True  # Flag for first page load
    
    try:
        while current_year <= 2025:
            # Calculate filter value (decreases by 1 for each year)
            filter_base = 820 - (current_year - 2002)
            filter_value = f"000{filter_base}{current_year}"
            
            while True:  # Page loop
                # Construct URL with year filter and page number
                url = f"https://www.libris.ro/carti?ft&fsv_77563={filter_value}&iv.pg={current_page}&isf=1"
                driver.get(url)
                print(f"\nScraping year {current_year}, page {current_page}")
                
                # Handle popups only on first page load
                if first_load:
                    try:
                        # Handle cookie popup
                        refuse_button = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, "//a[text()='Refuz toate']"))
                        )
                        if refuse_button.is_displayed():
                            refuse_button.click()
                            
                        # Handle newsletter popup
                        newsletter_close = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "close_news_modal"))
                        )
                        if newsletter_close.is_displayed():
                            newsletter_close.click()
                            time.sleep(5)  # Wait for page to load after closing popups
                    except:
                        print("No popups found or already handled")
                    
                    first_load = False  # Reset flag after handling popups
                
                # Check for "no products found" message
                try:
                    no_products = driver.find_element(By.XPATH, "//div[contains(text(), 'Nu am gasit produse care sa corespunda filtrelor alese')]")
                    if no_products:
                        print(f"No more products for year {current_year}")
                        current_year += 1
                        current_page = 1
                        save_progress(current_year, current_page)
                        break
                except:
                    pass  # Continue if message not found
                
                # Wait for the products list
                try:
                    wait = WebDriverWait(driver, 10)
                    products_list = wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "categ-prod-list"))
                    )
                    
                    # Find all product items
                    product_items = products_list.find_elements(By.CLASS_NAME, "categ-prod-item")
                    
                    # Extract titles
                    page_titles = []
                    for item in product_items:
                        try:
                            title_element = item.find_element(By.CLASS_NAME, "pr-title-categ-pg")
                            page_titles.append(title_element.text)
                        except Exception as e:
                            print(f"Error extracting title: {e}")
                            continue
                    
                    # Save titles to file
                    with open('Data\Libris\libris_titles.txt', 'a', encoding='utf-8') as f:
                        for title in page_titles:
                            f.write(f"{current_year},{current_page},{title}\n")
                    
                    print(f"Found {len(page_titles)} titles on page {current_page}")
                    
                    # Save current progress before moving to next page
                    save_progress(current_year, current_page-1)
                    
                    # Check if we've reached the end of this year's products
                    if len(product_items) < 40:
                        print(f"Found {len(product_items)} items (less than 40) - last page for year {current_year}")
                        current_year += 1
                        current_page = 1
                        save_progress(current_year, current_page)
                        break
                    
                    # Move to next page
                    current_page += 1
                    
                except Exception as e:
                    print(f"Error processing page: {e}")
                    # Don't update progress here - keep the last successful values
                    raise  # Re-raise the exception to trigger the finally block
                
                time.sleep(1)  # Small delay between pages
                
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    scrape_libris()
