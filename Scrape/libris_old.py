from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
import time

def scrape_libris_old():
    # Set up Edge options
    edge_options = Options()
    # edge_options.add_argument("--headless")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Edge(options=edge_options)
    first_load = True
    
    try:
        for year in range(2000, 2003):  # 1977 to 2002
            current_page = 1
            
            while True:  # Page loop
                # Different URL format for years before 2000
                if year < 2000:
                    filter_value = f"000999{year}"
                else:
                    # For 2000: 822, 2001: 821, 2002: 820
                    filter_base = 822 - (year - 2000)
                    filter_value = f"000{filter_base}{year}"
                
                url = f"https://www.libris.ro/carti?ft&fsv_77563={filter_value}&iv.pg={current_page}&isf=1"
                driver.get(url)
                print(f"\nScraping year {year}, page {current_page}")
                
                # Handle popups on first load
                if first_load:
                    try:
                        # Handle cookie popup
                        refuse_button = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, "//a[text()='Refuz toate']"))
                        )
                        if refuse_button.is_displayed():
                            refuse_button.click()
                        
                        # Handle newsletter popup
                        newsletter_close = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "close_news_modal"))
                        )
                        if newsletter_close.is_displayed():
                            newsletter_close.click()
                            time.sleep(5)
                    except:
                        print("No popups found or already handled")
                    first_load = False
                
                # Check for "no products found" message
                try:
                    no_products = driver.find_element(By.XPATH, "//div[contains(text(), 'Nu am gasit produse care sa corespunda filtrelor alese')]")
                    if no_products:
                        print(f"No more products for year {year}")
                        break  # Move to next year
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
                    with open('Data\libris_titles_old.txt', 'a', encoding='utf-8') as f:
                        for title in page_titles:
                            f.write(f"{year},{current_page},{title}\n")
                    
                    print(f"Found {len(page_titles)} titles on page {current_page}")
                    
                    # For years before 2000, only process the first page
                    if year < 2000:
                        break
                    
                    # For years 2000 and after, check if we need to continue to next page
                    if len(product_items) < 40:
                        print(f"Found {len(product_items)} items (less than 40) - last page for year {year}")
                        break  # Move to next year
                    
                    current_page += 1
                    
                except Exception as e:
                    print(f"Error processing page: {e}")
                    break  # Move to next year
                
                time.sleep(1)  # Small delay between pages
                
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_libris_old() 