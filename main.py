from airtable_utils import get_records, update_record
from web_utils import is_url_alive, scraper_beautiful_soup
from llm_extractors import gpt_extractor
from llm_extractors.gpt_extractor import gpt_extract_info
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import config
import os
from scrape_analyze import scrape_with_firecrawl
import requests
import json
from openai import OpenAI



# deals with pages that have cookies to allow scraping
def access_page_with_cookies(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'agree') or contains(text(), 'AGREE')]"))
            )
            cookie_button.click()
            print("OK: Accepted cookies")
        except:
            print("INFO: No cookie banner detected")
        
        page_source = driver.page_source
        if is_fake_404(page_source):
            print("ERROR: Detected 404-like error inside page (Selenium)")
            return 404
        
        return 200
    except Exception as e:
        print(f"INFO: Selenium failed: {e}")
        return None
    finally:
        driver.quit()

# checks if pages with 200 code are in reality active
def is_fake_404(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    
    # Check <title>
    if soup.title and any(word in soup.title.text.lower() for word in ["404", "page not found", "not found", "error"]):
        return True
    
    # Check main heading
    h1 = soup.find("h1")
    if h1 and any(word in h1.text.lower() for word in ["404", "page not found", "not found", "error"]):
        return True
    
    # Optional: check for known error container divs/classes
    error_keywords = ["error-page", "not-found", "404"]
    for keyword in error_keywords:
        if soup.find(class_=lambda x: x and keyword in x):
            return True
    
    return False

# gets the status code from each page
def get_url_status_code(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/112.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    session = requests.Session()
    session.headers.update(headers)

    try:
        # HEAD request first
        response = session.head(url, allow_redirects=True, timeout=5)
        
        # If HEAD gives bad result, retry GET anyway
        if response.status_code >= 400:
            print("ERROR: HEAD request failed or returned error, retrying with GET...")
            response = session.get(url, allow_redirects=True, timeout=10)

        # After GET:

        if response.status_code == 404:
            print("ERROR: 404 Not Found (confirmed by requests)")
            return 404

        if 400 <= response.status_code < 600 and response.status_code not in [401, 403, 405]:
            print(f"ERROR: HTTP error {response.status_code} (confirmed by requests)")
            return response.status_code

        # If GET gives suspicious access issue
        if response.status_code in [401, 403, 405]:
            print("ERROR: Access issue detected (GET), trying with Selenium...")
            selenium_result = access_page_with_cookies(url)
            return selenium_result
        
        # If 200 OK, double-check page content
        if is_fake_404(response.text):
            print("ERROR: Detected 404-like error inside page (GET content)")
            return 404
        
        return response.status_code
    except requests.RequestException as e:
        print(f"ERROR: Requests failed: {e}")
        # As fallback, use Selenium
        return access_page_with_cookies(url)

# main status processing logic - loop over airtable rows
def process_records(records):

    perks_wo_link  = []
    perks_active   = []
    perks_inactive = []
    perks_updated  = []

    for record in records:
        fields = record.get('fields', {})
        perk_name = fields.get("Name")
        perk_url = fields.get("Link")
        current_status = fields.get("Status", "").lower()  # Default to empty string if missing

        # Case 1: No URL available
        if not perk_url:
            perks_wo_link.append(perk_name)
            continue
        
        # Case 1: No URL or it's an email (contains "@")
        if not perk_url or "@" in perk_url:
            perks_wo_link.append(perk_name)
            continue

        # Case 2: URL available but missing http
        if not perk_url.startswith(('http://', 'https://')):
            perk_url = 'http://' + perk_url

        print(f'\nProcessing perk: {perk_name}, at {perk_url}')

        # Check URL status
        status_code = get_url_status_code(perk_url)

        if status_code == 200:
            print(f"OK: Link is active (Status Code: {status_code})")

            if current_status != "active":
                
                update_record(record['id'], {"Status": "active"})
                perks_active.append(perk_name)
                perks_updated.append(perk_name)  # Only append if status changed

            perks_active.append(perk_name)

        elif status_code is None:
            print(f"ERROR: Failed to reach URL (Status Code: {status_code})")

            if current_status != "broken/expired":
                update_record(record['id'], {"Status": "broken/expired"})
                perks_updated.append(perk_name)

            perks_inactive.append(perk_name)

        else:
            print(f"ERROR: Link is inactive (Status Code: {status_code})")

            if current_status != "broken/expired":
                update_record(record['id'], {"Status": "broken/expired"})
                perks_updated.append(perk_name)

            perks_inactive.append(perk_name)
        
        time.sleep(1)  # polite rate limiting

    # Final summary
    print("Perks without link :", perks_wo_link)
    print("Perks active       :", perks_active)
    print("Perks inactive     :", perks_inactive)
    print("Perks updated      :", perks_updated)

    return perks_wo_link, perks_active, perks_inactive, perks_updated


def scrap_website(records):
    
    def print_perks(perks):
        for key, value in perks.items():
            print(f"{key}: {value}")
    
    print("\nNumber of active perks to be scraped: ", len(records))

    # filter 'records' to consider only the active perks
    results = {}

    for record in records:
        # extract information from argument records
        fields = record.get('fields', {})
        perk_name = fields.get("Name")
        perk_url = fields.get("Link")
        print(f'\nAnalysing perk: {perk_name}')

        # SCRAPER 1: BeautifulSoup - scrape the url's text with beautiful soup
        bs_page_text = scraper_beautiful_soup(perk_url)
        #print(bs_page_text)

        # SCRAPER 2
        #fc_page_text = scraper_firecrawl(perk_url)

        # SCRAPER 3
        #ppx_page_text = scraper_perplexity(perk_url)
        
        # Extract information using GPT
        gpt_extraction = gpt_extract_info(bs_page_text)
        results[perk_name] = gpt_extraction
        #print("BEAUTIFULSOUP:")
        print_perks(gpt_extraction)



    return results

if __name__ == "__main__":

    process_records_flag = 0

    # extract perk database table from airtable
    records = get_records()

    if process_records_flag == 1:

        # identify which records are active/inactive and update status on airtable
        perks_wo_link, perks_active, perks_inactive, _ = process_records(records)

        # Write it to a file (each item on a new line)
        with open('perks_active.txt', 'w') as f:
            for item in perks_active:
                f.write(item + '\n')

    else:
        # Read the list of active perk to avoid reruning the whole analysis 
        with open('perks_active.txt', 'r') as f:
            perks_active = [line.strip() for line in f]

    # filter all the records from airtable - we only scratch the ones which are active
    records_active = [item for item in records if item['fields'].get('Name') in perks_active]

    # scrape the active websites to update information: 
    scrap_website(records_active[:3])
