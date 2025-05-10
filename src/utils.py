import re
import os
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.gpt_extractor import scrape_website_with_firecrawl

############# Handle printing
def print_hello():
    """Print a concise and visually appealing explanation of the program."""
    
    print("\033[1;36m🔍 PERKS DATABASE UPDATER\033[0m")
    print("\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[1mPROCESS FLOW:\033[0m")
    print("  1. \033[1;32mFetch records\033[0m from Airtable perks database")
    print("  2. \033[1;32mVerify URL status\033[0m (active/inactive) for each perk")
    print("  3. \033[1;32mUpdate status in Airtable\033[0m for any changed perks")
    print("  4. \033[1;32mScrape active websites\033[0m using two methods:")
    print("     - BeautifulSoup + GPT-4o extraction")
    print("     - Perplexity API with subpage crawling")
    print("  5. \033[1;32mCombine results\033[0m from both scraping methods")
    print("  6. \033[1;32mUpdate Airtable\033[0m with the combined perk information")
    print("\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[1mEXTRACTED DATA:\033[0m")
    print("  • Provider description")
    print("  • What you get")
    print("  • How to get it")
    print("  • Monetary value")
    print("\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\n\n")


def print_perks(perks):
    for key, value in perks.items():
        line = f"{key}: {value}"
        print(f'{line[:100]}...')  


############# Logic to analyse URLs
def is_email(text):
    """
    Check if a string is a valid email address using regex pattern.
    This is more reliable than just checking for '@'.
    """
    # RFC 5322 compliant email regex pattern (simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, text))


def is_url_alive(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def scraper_beautiful_soup(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        texts = soup.find_all(['h1', 'h2', 'p', 'li'])
        page_text = "\n".join(t.get_text(strip=True) for t in texts)
        return page_text
    except Exception:
        return 


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
        
        if is_fake_404(url):
            print("ERROR: Detected 404-like error inside page (Selenium)")
            return 404
        
        return 200
    except Exception as e:
        print(f"INFO: Selenium failed: {e}")
        return None
    finally:
        driver.quit()



def is_fake_404(perk_url):
    # Scrape the website content
    scraped_text = scrape_website_with_firecrawl(perk_url)
    
    # Skip empty pages or very short content
    if not scraped_text or len(scraped_text.strip()) < 20:
        return False
    
    try:
        # Expert-designed prompt with detailed context for accurate detection
        prompt = f"""You're a specialized web content analyzer tasked with detecting two specific types of pages:

        1) FAKE 404 PAGES: Pages that display error messages but don't return an actual HTTP 404 status code
        2) CLOSED FORMS: Forms, applications, or typeforms that are no longer accepting submissions

        Analyze the following webpage content extremely carefully and determine if it falls into EITHER category.

        For FAKE 404 PAGES, look for:
        - Error messages ("page not found", "404", "error", etc.)
        - Missing content indicators
        - Broken link messaging
        - Technical error explanations
        - Apologetic language about content unavailability

        For CLOSED FORMS, look for:
        - "This form is no longer accepting responses"
        - "Applications are closed/paused"
        - "Submissions period has ended"
        - "We're not currently accepting applications"
        - "Program is currently on pause"
        - "Form is currently closed"
        - "This typeform isn't accepting new responses"
        - "We will inform you about a new application period"
        - Any language indicating the form exists but submissions are no longer being accepted

        Respond with EXACTLY ONE WORD:
        - "YES" if the content matches EITHER a fake 404 page OR a closed form
        - "NO" if it's a normal, functioning page

        Webpage content to analyze:
        {scraped_text[:3000]}"""

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a precise webpage status detector that specializes in identifying fake 404 pages and closed submission forms. You only respond with YES or NO."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        result = response.choices[0].message.content.strip().upper()
        
        # Log identified patterns for debugging
        if result == "YES":
            print(f"{perk_url} => Fake 404/Closed form detected by LLM")
        
        return result == "YES"
        
    except Exception as e:
        print(f"Error using GPT API: {e}")
        # Fallback to basic keyword detection if API fails
        text_lower = scraped_text.lower()
        
        # Combined patterns from both categories for simple fallback
        patterns = [
            "404", "page not found", "not found", "error-page",
            "isn't accepting new responses", "form is currently closed", 
            "submissions are no longer being accepted", "application period is over",
            "not currently accepting applications", "applications are currently paused",
            "program is currently on pause"
        ]
        
        return any(pattern in text_lower for pattern in patterns)


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
        if is_fake_404(url):
            print("ERROR: Detected 404-like error inside page (GET content)")
            return 404
        
        return response.status_code
    except requests.RequestException as e:
        print(f"ERROR: Requests failed: {e}")
        # As fallback, use Selenium
        return access_page_with_cookies(url)


############# Methods to save to local directory
def save_formatted_text(data, text_file_path):

    # Ensure the directory exists
    os.makedirs(os.path.dirname(text_file_path), exist_ok=True)
    
    with open(text_file_path, 'w', encoding='utf-8') as f:
        for name, details in data.items():
            f.write(f"Name: {name}\n")
            
            if 'Brief description of the provider' in details:
                f.write(f"Brief description of the provider: {details['Brief description of the provider']}\n")
            
            if 'What you get' in details:
                f.write(f"What you get: {details['What you get']}\n")
                
            if 'How to get it' in details:
                f.write(f"How to get it: {details['How to get it']}\n")
                
            if 'Value' in details:
                f.write(f"Value: {0 if details['Value'] == 'Not found' else details['Value']}\n")

            f.write("\n")  # Add a blank line between entries
    
    print(f"Formatted text saved to {text_file_path}")

def save_perks_status(perks_wo_link, perks_active, perks_inactive, perks_updated):
    # names of files to save the values
    perks_names = ['perks_wo_link', 'perks_active', 'perks_inactive', 'perks_updated']


    for i, perks in enumerate([perks_wo_link, perks_active, perks_inactive, perks_updated]):

        # Write it to a file (each item on a new line)
        with open(f'results/{perks_names[i]}.txt', 'w') as f:
            for item in perks:
                f.write(item + '\n')

